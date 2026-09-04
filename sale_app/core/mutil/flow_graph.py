import asyncio
import functools
import json
import operator
import os
import time
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage

from langgraph.constants import TAG_HIDDEN
from langgraph._internal._constants import NS_SEP

from sale_app.core.mutil.classify_utils import fallback_category, parse_category_name, suggest_category_from_state
from sale_app.core.mutil.flow_routers import confirm_router, decide_router, information_router
from sale_app.core.mutil.node_names import NextNode
from sale_app.config.log import Logger

logger = Logger("fly_base")

_chain = None
_checkpointer = None
_checkpointer_cm = None


def super_agent_node(state, agent, name):
    quick_category = suggest_category_from_state(state)
    if quick_category:
        return {"next": quick_category}

    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        return {
            "next": name,
        }

    invoke_state = dict(state)
    if isinstance(last_message, HumanMessage):
        invoke_state["question"] = state.get("question") or last_message.content

    result = agent.invoke(invoke_state)
    category_name = fallback_category(invoke_state)
    if isinstance(result, AIMessage):
        content = result.content
        logger.info(f"问题分类:{content}")
        if content:
            category_name = parse_category_name(content, fallback=fallback_category(invoke_state))
    return {
        "next": category_name,
    }


class FlowState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    next: str
    pre_node: str
    question: str
    fixed_question: str
    history: list
    information_sequences: Annotated[list, operator.add]
    product_list: list
    isRecommend: bool
    isInfoConfirmed: bool
    awaiting_info_confirm: bool
    info_summary: str
    awaiting_conversion: bool
    conversion_completed: bool


def build_flow_graph(llm):
    from langgraph.graph import END, StateGraph

    from sale_app.core.agent.information_gathering import (
        information_node,
        information_gathering,
    )
    from sale_app.core.agent.information_confirm import (
        information_confirm_node,
        information_summary,
    )
    from sale_app.core.agent.customer_conversion import conversion_node
    from sale_app.core.agent.intention_confirm import intention_confirm, intention_node
    from sale_app.core.agent.other_agent import chat_manager, agent_node
    from sale_app.core.agent.qa_handle import qa_node, qa_agent
    from sale_app.core.mutil.fix_question import fix_question, fixed_question_node
    from sale_app.core.agent.question_class_node import question_class_func
    from sale_app.core.mutil.recommend_product_graph import build_recommend_graph, recommend_graph_node

    super = question_class_func(
        llm, ["信息收集", "闲聊经理", "意图确认", "产品推荐", "产品解答专家"]
    )
    supervisor_node = functools.partial(super_agent_node, agent=super, name="问题分类")

    flow_graph = StateGraph(FlowState)
    flow_graph.add_node(
        NextNode.FIX, functools.partial(fixed_question_node, agent=fix_question(llm))
    )
    flow_graph.add_node(NextNode.CLASSIFY, supervisor_node)
    flow_graph.add_node(
        NextNode.CHAT,
        functools.partial(agent_node, agent=chat_manager(llm), name="闲聊经理"),
    )
    flow_graph.add_node(
        NextNode.INTENT,
        functools.partial(
            intention_node, agent=intention_confirm(llm), name="意图确认"
        ),
    )
    flow_graph.add_node(
        NextNode.GATHER,
        functools.partial(
            information_node, agent=information_gathering(llm), name="信息收集"
        ),
    )
    flow_graph.add_node(
        NextNode.CONFIRM,
        functools.partial(
            information_confirm_node,
            summary_agent=information_summary(llm),
            name="信息确认",
        ),
    )
    flow_graph.add_node(
        NextNode.QA,
        functools.partial(qa_node, agent=qa_agent(llm), name="产品解答专家"),
    )
    recommend_subgraph = build_recommend_graph(llm).compile()
    flow_graph.add_node(
        NextNode.RECOMMEND,
        functools.partial(recommend_graph_node, compiled_graph=recommend_subgraph),
    )
    flow_graph.add_node(
        NextNode.CONVERSION,
        functools.partial(conversion_node, name="客户转化"),
    )

    flow_graph.add_edge(NextNode.FIX, NextNode.CLASSIFY)
    flow_graph.add_conditional_edges(
        NextNode.CLASSIFY,
        decide_router,
        {
            NextNode.CHAT: NextNode.CHAT,
            NextNode.INTENT: NextNode.INTENT,
            NextNode.GATHER: NextNode.GATHER,
            NextNode.CONFIRM: NextNode.CONFIRM,
            NextNode.RECOMMEND: NextNode.RECOMMEND,
            NextNode.CONVERSION: NextNode.CONVERSION,
            NextNode.QA: NextNode.QA,
        },
    )
    flow_graph.add_conditional_edges(
        NextNode.INTENT,
        lambda x: x["next"],
        {
            NextNode.GATHER: NextNode.GATHER,
            NextNode.CHAT: NextNode.CHAT,
        },
    )
    flow_graph.add_conditional_edges(
        NextNode.GATHER,
        information_router,
        {
            NextNode.FINISH: END,
            NextNode.CONFIRM: NextNode.CONFIRM,
        },
    )
    flow_graph.add_conditional_edges(
        NextNode.CONFIRM,
        confirm_router,
        {
            NextNode.FINISH: END,
            NextNode.RECOMMEND: NextNode.RECOMMEND,
        },
    )
    flow_graph.add_edge(NextNode.CHAT, END)
    flow_graph.add_edge(NextNode.QA, END)
    flow_graph.add_edge(NextNode.CONVERSION, END)
    flow_graph.add_edge(NextNode.RECOMMEND, END)
    flow_graph.set_entry_point(NextNode.FIX)
    return flow_graph


def _checkpoint_db_path() -> str:
    from sale_app.util.file_utils import find_project_root

    db_path = (
        find_project_root(os.path.abspath(__file__))
        + "/storage/memory_file/chat_history.db"
    )
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path


async def startup_chain() -> None:
    """在 FastAPI lifespan startup 调用；测试可 asyncio.run(startup_chain())。"""
    global _chain, _checkpointer, _checkpointer_cm
    if _chain is not None:
        return
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

    from sale_app.core.moudel.zhipuai import ZhipuAI

    llm = ZhipuAI().openai_chat()
    graph = build_flow_graph(llm)
    _checkpointer_cm = AsyncSqliteSaver.from_conn_string(_checkpoint_db_path())
    _checkpointer = await _checkpointer_cm.__aenter__()
    _chain = graph.compile(checkpointer=_checkpointer)


async def shutdown_chain() -> None:
    global _chain, _checkpointer, _checkpointer_cm
    if _checkpointer_cm is not None:
        await _checkpointer_cm.__aexit__(None, None, None)
    _checkpointer_cm = None
    _checkpointer = None
    _chain = None


def _run_startup_if_needed() -> None:
    if _chain is not None:
        return
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(startup_chain())
    else:
        raise RuntimeError("LangGraph chain 未初始化，请在 FastAPI lifespan 中 await startup_chain()")


def get_chain():
    _run_startup_if_needed()
    return _chain


def run_flow(question: str, config: dict) -> FlowState:
    return get_chain().invoke({"messages": [HumanMessage(content=question)]}, config)


# 面向用户、允许 token 流式输出的节点
STREAM_TOKEN_NODES = {
    NextNode.CHAT,
    NextNode.QA,
    NextNode.RECOMMEND,
    "产品推荐",
}

# 结构化输出节点：无 token 流，在节点结束时一次性推送
STRUCTURED_REPLY_NODES = {
    NextNode.GATHER,
    NextNode.CONFIRM,
    NextNode.CONVERSION,
}

# 工作流追踪节点（用于执行过程面板）
TRACKED_WORKFLOW_NODES = {
    NextNode.FIX,
    NextNode.CLASSIFY,
    NextNode.CHAT,
    NextNode.INTENT,
    NextNode.GATHER,
    NextNode.CONFIRM,
    NextNode.CONVERSION,
    NextNode.QA,
    NextNode.RECOMMEND,
    "信息提取",
    "产品推荐",
}

ESTIMATED_WORKFLOW_STEPS = 10


def _is_graph_node_chain_event(event: dict) -> bool:
    """仅保留 LangGraph 图节点级 chain 事件，忽略节点内部的 Runnable 子链。

    与 langgraph.pregel._messages.StreamMessagesHandler 的过滤逻辑一致：
    event.name 必须等于 metadata.langgraph_node，且非 hidden / 非子图内部任务。
    """
    metadata = event.get("metadata") or {}
    node = metadata.get("langgraph_node") or ""
    if node not in TRACKED_WORKFLOW_NODES:
        return False
    if event.get("name") != node:
        return False
    tags = event.get("tags") or []
    if TAG_HIDDEN in tags:
        return False
    checkpoint_ns = metadata.get("langgraph_checkpoint_ns")
    if checkpoint_ns:
        ns = tuple(str(checkpoint_ns).split(NS_SEP))[:-1]
        if len(ns) > 0:
            return False
    return True


def _truncate(text: str, max_len: int = 800) -> str:
    text = " ".join(text.split())
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _preview_value(value, max_len: int = 800) -> str:
    if value is None:
        return ""
    if isinstance(value, BaseMessage):
        content = value.content
        text = content if isinstance(content, str) else json.dumps(content, ensure_ascii=False, default=str)
        return _truncate(text, max_len)
    if isinstance(value, dict):
        sanitized = {}
        for key, val in value.items():
            if key == "messages" and isinstance(val, list):
                sanitized[key] = [_preview_value(item, 200) for item in val[-3:]]
            elif isinstance(val, (str, int, float, bool)) or val is None:
                sanitized[key] = val
            else:
                sanitized[key] = _preview_value(val, 200)
        return _truncate(json.dumps(sanitized, ensure_ascii=False, default=str), max_len)
    if isinstance(value, list):
        items = [_preview_value(item, 150) for item in value[:5]]
        return _truncate(json.dumps(items, ensure_ascii=False, default=str), max_len)
    return _truncate(str(value), max_len)


def _chunk_text(chunk) -> str:
    content = getattr(chunk, "content", chunk)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict) and part.get("type") == "text":
                parts.append(part.get("text", ""))
        return "".join(parts)
    return str(content) if content else ""


def _ai_messages_from_output(output) -> list[str]:
    if not isinstance(output, dict):
        return []
    texts = []
    for msg in output.get("messages") or []:
        if isinstance(msg, AIMessage) and msg.content:
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            if text:
                texts.append(text)
    return texts


async def astream_flow(question: str, config: dict, step_offset: int = 0):
    """流式推送用户可见回复与工作流步骤事件。"""
    chain = get_chain()
    inputs = {"messages": [HumanMessage(content=question)]}
    emitted_nodes: set[str] = set()
    step_counter = step_offset
    active_runs: dict[str, dict] = {}

    async for event in chain.astream_events(inputs, config, version="v2"):
        metadata = event.get("metadata") or {}
        node = metadata.get("langgraph_node") or ""
        kind = event.get("event")
        run_id = str(event.get("run_id") or metadata.get("run_id") or f"{node}-{step_counter}")

        if kind == "on_chain_start" and _is_graph_node_chain_event(event):
            step_counter += 1
            active_runs[run_id] = {"step": step_counter, "node": node, "started_at": time.time()}
            preview_in = _preview_value(event.get("data", {}).get("input"))
            yield {
                "type": "step_start",
                "step": step_counter,
                "node": node,
                "input": preview_in,
            }
            yield {
                "type": "progress",
                "current": step_counter - 1,
                "total": max(ESTIMATED_WORKFLOW_STEPS, step_counter),
                "label": f"正在执行：{node}",
            }

        elif kind == "on_chain_end" and _is_graph_node_chain_event(event):
            run_info = active_runs.pop(run_id, None)
            step = run_info["step"] if run_info else step_counter
            duration_ms = None
            if run_info:
                duration_ms = int((time.time() - run_info["started_at"]) * 1000)
            preview_out = _preview_value(event.get("data", {}).get("output"))
            yield {
                "type": "step_end",
                "step": step,
                "node": node,
                "output": preview_out,
                "duration_ms": duration_ms,
                "status": "ok",
            }
            yield {
                "type": "progress",
                "current": step,
                "total": max(ESTIMATED_WORKFLOW_STEPS, step),
                "label": f"已完成：{node}",
            }
            if node in STRUCTURED_REPLY_NODES and node not in emitted_nodes:
                for text in _ai_messages_from_output(event.get("data", {}).get("output")):
                    emitted_nodes.add(node)
                    yield {"type": "token", "text": text}

        elif kind == "on_chat_model_stream" and node in STREAM_TOKEN_NODES:
            text = _chunk_text(event.get("data", {}).get("chunk"))
            if text:
                emitted_nodes.add(node)
                yield {"type": "token", "text": text}

    yield {
        "type": "progress",
        "current": step_counter,
        "total": max(step_counter, 1),
        "label": "工作流执行完成",
    }
