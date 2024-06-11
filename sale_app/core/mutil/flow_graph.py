import functools
import json
import operator
import re
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END

from sale_app.core.agent.information_gathering_test import information_node, information_gathering
from sale_app.core.agent.other_agent import chat_manager
from sale_app.core.mutil.fix_question import fix_question, fixed_question_node
from sale_app.core.mutil.question_router import create_team_supervisor
from sale_app.core.moudel.zhipuai import ZhipuAI

llm = ZhipuAI().openai_chat()


def agent_node(state, agent):
    result = agent.invoke(state)
    return {"messages": [AIMessage(content=result.content)]}


def super_agent_node(state, agent):
    name = "FINISH"
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        return {
            "next": name,
        }
    result = agent.invoke(state)
    if isinstance(result, ToolMessage):
        pass
    if isinstance(result, AIMessage):
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
        if result.additional_kwargs:
            next_node = result.additional_kwargs["tool_calls"][0]["function"]["arguments"]
            name = json.loads(next_node)["next"]
        else:
            text = result.content
            match = re.search(r"next='([^']+)'", text)
            if match:
                name = match.group(1)
            else:
                name = state["pre_node"]
    return {
        "next": name,
    }


class FlowState(TypedDict):
    # 消息列表
    messages: Annotated[List[BaseMessage], operator.add]
    # 下一个节点
    next: str
    # 上一个节点
    pre_node: str
    # 问题
    question: str
    # 新问题
    fixed_question: str
    # 聊天历史
    history: list
    # 信息收集序号列表
    information_sequences: list
    # 产品列表
    product_list: list


super = create_team_supervisor(llm, ["信息收集"])

supervisor_node = functools.partial(super_agent_node, agent=super)

flow_graph = StateGraph(FlowState)
flow_graph.add_node("问题修复", functools.partial(fixed_question_node, agent=fix_question(llm)))
flow_graph.add_node("问题分类", supervisor_node)
flow_graph.add_node("闲聊经理", functools.partial(agent_node, agent=chat_manager(llm)))
flow_graph.add_node("信息收集", functools.partial(information_node, agent=information_gathering(llm)))
flow_graph.add_edge("问题修复", "问题分类")

for node in list(flow_graph.nodes.keys()):
    flow_graph.add_edge(node, END)

conditional_map = {k: k for k in list(flow_graph.nodes.keys())}
conditional_map["FINISH"] = END

flow_graph.add_conditional_edges("问题分类", lambda x: x["next"], conditional_map)

flow_graph.set_entry_point("问题修复")
memory = SqliteSaver.from_conn_string("chat_history.db")
chain = flow_graph.compile(
    checkpointer=memory,
)


def run_flow(question: str, config: dict) -> FlowState:
    return chain.invoke({"messages": [HumanMessage(content=question)]}, config)

# flow_graph.add_node("客户意愿确认专家", verify_idea_node)
# flow_graph.add_node("贷款产品推荐官", recommend_node)
