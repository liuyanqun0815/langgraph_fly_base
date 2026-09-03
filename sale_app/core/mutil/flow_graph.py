import functools
import json
import operator
import os
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage

from sale_app.core.mutil.node_names import NextNode
from sale_app.config.log import Logger

logger = Logger("fly_base")

llm = None
memory = None
flow_graph = None
chain = None


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


def _build_graph():
    global llm, memory, flow_graph, chain
    if chain is not None:
        return chain

    from langgraph.checkpoint.sqlite import SqliteSaver
    from langgraph.graph import END, StateGraph

    from sale_app.core.agent.information_gathering import information_node, information_gathering
    from sale_app.core.agent.intention_confirm import intention_confirm, intention_node
    from sale_app.core.agent.other_agent import chat_manager, agent_node
    from sale_app.core.agent.qa_handle import qa_node, qa_agent
    from sale_app.core.mutil.fix_question import fix_question, fixed_question_node
    from sale_app.core.agent.question_class_node import question_class_func
    from sale_app.core.moudel.zhipuai import ZhipuAI
    from sale_app.core.mutil.recommend_product_graph import re_graph
    from sale_app.util.file_utils import find_project_root

    llm = ZhipuAI().openai_chat()
    db_path = find_project_root(os.path.abspath(__file__)) + "/storage/memory_file/chat_history.db"
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    memory = SqliteSaver.from_conn_string(db_path)

    super = question_class_func(llm, ["信息收集", "闲聊经理", "意图确认", "产品推荐", "产品解答专家"])
    supervisor_node = functools.partial(super_agent_node, agent=super, name="问题分类")

    flow_graph = StateGraph(FlowState)
    flow_graph.add_node("问题修复", functools.partial(fixed_question_node, agent=fix_question(llm)))
    flow_graph.add_node("问题分类", supervisor_node)
    flow_graph.add_node("闲聊经理", functools.partial(agent_node, agent=chat_manager(llm), name="闲聊经理"))
    flow_graph.add_node("意图确认", functools.partial(intention_node, agent=intention_confirm(llm), name="意图确认"))
    flow_graph.add_node(
        "信息收集", functools.partial(information_node, agent=information_gathering(llm), name="信息收集")
    )
    flow_graph.add_node("产品解答专家", functools.partial(qa_node, agent=qa_agent(llm), name="产品解答专家"))
    flow_graph.add_node("产品推荐", re_graph.compile())

    flow_graph.add_edge("问题修复", "问题分类")
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
    flow_graph.set_entry_point("问题修复")

    chain = flow_graph.compile(checkpointer=memory)
    return chain


def get_chain():
    return _build_graph()


def run_flow(question: str, config: dict) -> FlowState:
    return get_chain().invoke({"messages": [HumanMessage(content=question)]}, config)
