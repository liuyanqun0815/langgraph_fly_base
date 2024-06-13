import functools
import json
import operator
import os
import re
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage, AIMessage, ToolMessage, HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, END

from sale_app.core.agent.information_gathering import information_node, information_gathering
from sale_app.core.agent.intention_confirm import intention_confirm, intention_node
from sale_app.core.agent.other_agent import chat_manager
from sale_app.core.mutil.fix_question import fix_question, fixed_question_node
from sale_app.core.mutil.question_router import create_team_supervisor
from sale_app.core.moudel.zhipuai import ZhipuAI
from sale_app.core.mutil.recommend_product_graph import re_graph

llm = ZhipuAI().openai_chat()

current_file_path = os.path.abspath(__file__)
current_dir_path = os.path.dirname(current_file_path)
memory = SqliteSaver.from_conn_string(current_dir_path + "/chat_history.db")
def agent_node(state, agent):
    # state["messages"] = state["messages"][:-1]
    result = agent.invoke(state)
    return {"messages": [AIMessage(content=result.content)]}


def super_agent_node(state, agent, name):
    # name = "FINISH"
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
                name = state["pre_node"] if state["pre_node"] else "闲聊经理"
        # messages.append(result)
    # else:
    # messages.append(result)
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
    information_sequences: Annotated[list, operator.add]
    # 产品列表
    product_list: list
    # 是否推荐产品
    isRecommend: bool


super = create_team_supervisor(llm, ["信息收集", "闲聊经理", "意图确认", "产品推荐"])

supervisor_node = functools.partial(super_agent_node, agent=super, name="问题分类")

flow_graph = StateGraph(FlowState)
flow_graph.add_node("问题修复", functools.partial(fixed_question_node, agent=fix_question(llm)))
flow_graph.add_node("问题分类", supervisor_node)

flow_graph.add_node("闲聊经理", functools.partial(agent_node, agent=chat_manager(llm)))
flow_graph.add_node("意图确认", functools.partial(intention_node, agent=intention_confirm(llm), name="意图确认"))
flow_graph.add_node("信息收集", functools.partial(information_node, agent=information_gathering(llm), name="信息收集"))
# 添加一个子链
flow_graph.add_node("产品推荐", re_graph.compile())

flow_graph.add_edge("问题修复", "问题分类")


def decide_router(state):
    if state.get("next") == "产品问答":
        return "产品问答"
    if state.get("next") == "产品推荐":
        return state.get('next')
    elif state.get('pre_node') == "信息收集" and state.get("next") != "产品问答":
        return "信息收集"
    else:
        return state.get('next')


flow_graph.add_conditional_edges("问题分类", decide_router, {
    "闲聊经理": "闲聊经理",
    "意图确认": "意图确认",
    "信息收集": "信息收集",
    "产品推荐": "产品推荐",
})
flow_graph.add_conditional_edges("意图确认", lambda x: x["next"], {
    "信息收集": "信息收集",
    "闲聊经理": "闲聊经理",
})


def information_router(state):
    if state.get("isRecommend"):
        return "产品推荐"
    else:
        return "FINISH"


for node in list(flow_graph.nodes.keys()):
    flow_graph.add_edge(node, END)

flow_graph.add_conditional_edges("信息收集", information_router, {
    "FINISH": END,
    "产品推荐": "产品推荐",
})

# for node in list(flow_graph.nodes.keys()):
#     flow_graph.add_edge(node, END)
#
# conditional_map = {k: k for k in list(flow_graph.nodes.keys())}
# conditional_map["FINISH"] = END

# flow_graph.add_conditional_edges("问题分类", lambda x: x["next"], conditional_map)

flow_graph.set_entry_point("问题修复")


chain = flow_graph.compile(
    checkpointer=memory,
)
# chain.get_graph().draw_png(output_file_path="grap.png", fontname="SimHei")

def run_flow(question: str, config: dict) -> FlowState:
    return chain.invoke({"messages": [HumanMessage(content=question)]}, config)
