import functools
import json
import operator
import re
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END

from sale_app.core.mutil.fix_question import fix_question
from sale_app.core.mutil.question_router import create_team_supervisor

llm = ZhipuAI().openai_chat()


def fixed_question_node(state, agent):
    messages = state["messages"]
    last_message = messages[-1]
    #如果是客户提问，就修正问题
    if isinstance(last_message, HumanMessage):
        state["question"] = last_message.content
    result = agent.invoke(state)
    return {"new_question": result.content}


def agent_node(state, agent, name):
    result = agent.invoke(state)
    return {"messages": [AIMessage(content=result["output"], name=name)]}


def super_agent_node(state, agent, name):
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
    new_question: str
    # 信息收集列表
    info_collect: list
    # 产品列表
    product_list: list


super = create_team_supervisor(llm, ["闲聊", "贷款经理"])

supervisor_node = functools.partial(super_agent_node, agent=super, name="router")

fixed_node = functools.partial(
    fixed_question_node, agent=fix_question(llm)
)
flow_graph = StateGraph(FlowState)
flow_graph.add_node("问题修复", fixed_node)
flow_graph.add_node("问题分类", supervisor_node)

flow_graph.add_edge("问题修复", "问题分类")
flow_graph.add_edge("问题分类", END)

flow_graph.set_entry_point("问题修复")
memory = SqliteSaver.from_conn_string("chat_history.db")
chain = flow_graph.compile(
    checkpointer=memory,
)


def run_flow(question: str, config: dict) -> FlowState:
    return chain.invoke({"messages": [HumanMessage(content=question)]}, config)

# flow_graph.add_node("客户意愿确认专家", verify_idea_node)
# flow_graph.add_node("贷款产品推荐官", recommend_node)
