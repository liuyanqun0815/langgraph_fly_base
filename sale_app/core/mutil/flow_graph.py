import functools
import json
import operator
import os
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage

from sale_app.core.mutil.node_names import NextNode
from sale_app.config.log import Logger

logger = Logger("fly_base")

_chain = None
_checkpointer = None
_checkpointer_cm = None


def super_agent_node(state, agent, name):
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        return {
            "next": name,
        }
    result = agent.invoke(state)
    category_name = "闲聊经理"
    if isinstance(result, ToolMessage):
        pass
    if isinstance(result, AIMessage):
        content = result.content
        logger.info(f"问题分类:{content}")
        if content:
            clean_string = content.strip("```json\n").strip("\n```")
            data = json.loads(clean_string)
            category_name = data["category_name"]
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


def decide_router(state):
    nxt = state.get("next") or ""
    pre_node = state.get("pre_node") or ""

    if NextNode.QA in nxt:
        return NextNode.QA
    if NextNode.RECOMMEND in nxt:
        return NextNode.RECOMMEND
    if NextNode.GATHER in nxt:
        return NextNode.GATHER
    if NextNode.GATHER in pre_node and NextNode.QA not in nxt:
        return NextNode.GATHER
    return nxt


def information_router(state):
    if state.get("isRecommend"):
        return NextNode.RECOMMEND
    return NextNode.FINISH


def build_flow_graph(llm):
    from langgraph.graph import END, StateGraph

    from sale_app.core.agent.information_gathering import (
        information_node,
        information_gathering,
    )
    from sale_app.core.agent.intention_confirm import intention_confirm, intention_node
    from sale_app.core.agent.other_agent import chat_manager, agent_node
    from sale_app.core.agent.qa_handle import qa_node, qa_agent
    from sale_app.core.mutil.fix_question import fix_question, fixed_question_node
    from sale_app.core.agent.question_class_node import question_class_func
    from sale_app.core.mutil.recommend_product_graph import build_recommend_graph

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
        NextNode.QA,
        functools.partial(qa_node, agent=qa_agent(llm), name="产品解答专家"),
    )
    flow_graph.add_node(NextNode.RECOMMEND, build_recommend_graph(llm).compile())

    flow_graph.add_edge(NextNode.FIX, NextNode.CLASSIFY)
    flow_graph.add_conditional_edges(
        NextNode.CLASSIFY,
        decide_router,
        {
            NextNode.CHAT: NextNode.CHAT,
            NextNode.INTENT: NextNode.INTENT,
            NextNode.GATHER: NextNode.GATHER,
            NextNode.RECOMMEND: NextNode.RECOMMEND,
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
            NextNode.RECOMMEND: NextNode.RECOMMEND,
        },
    )
    flow_graph.add_edge(NextNode.CHAT, END)
    flow_graph.add_edge(NextNode.QA, END)
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


def startup_chain() -> None:
    """在 FastAPI lifespan startup 调用；测试可跳过。"""
    global _chain, _checkpointer, _checkpointer_cm
    if _chain is not None:
        return
    from langgraph.checkpoint.sqlite import SqliteSaver

    from sale_app.core.moudel.zhipuai import ZhipuAI

    llm = ZhipuAI().openai_chat()
    graph = build_flow_graph(llm)
    _checkpointer_cm = SqliteSaver.from_conn_string(_checkpoint_db_path())
    _checkpointer = _checkpointer_cm.__enter__()
    _chain = graph.compile(checkpointer=_checkpointer)


def shutdown_chain() -> None:
    global _chain, _checkpointer, _checkpointer_cm
    if _checkpointer_cm is not None:
        _checkpointer_cm.__exit__(None, None, None)
    _checkpointer_cm = None
    _checkpointer = None
    _chain = None


def get_chain():
    global _chain
    if _chain is None:
        startup_chain()
    return _chain


def run_flow(question: str, config: dict) -> FlowState:
    return get_chain().invoke({"messages": [HumanMessage(content=question)]}, config)
