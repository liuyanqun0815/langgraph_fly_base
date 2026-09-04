import functools
import operator
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import END, StateGraph

from sale_app.core.mutil.node_names import NextNode
from sale_app.config.log import Logger
from sale_app.core.agent.recommend_product import (
    extract_node,
    extract_information,
    recommend_node,
    recommend_product,
)

logger = Logger("fly_base")


class RecommendState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_info: str
    product_list: str
    pre_node: str
    awaiting_conversion: bool
    awaiting_info_confirm: bool


def recommend_graph_node(state, compiled_graph):
    """子图执行后将推荐结果写回主图 state（子图 schema 与主图对齐）。"""
    output = compiled_graph.invoke(state)
    product_list = output.get("product_list")
    if not product_list:
        from langchain_core.messages import AIMessage

        for message in reversed(output.get("messages") or []):
            if isinstance(message, AIMessage) and message.content:
                product_list = message.content
                break
    return {
        "messages": output.get("messages") or [],
        "user_info": output.get("user_info"),
        "product_list": product_list,
        "pre_node": NextNode.RECOMMEND,
        "awaiting_conversion": True,
        "awaiting_info_confirm": False,
    }


def build_recommend_graph(llm):
    re_graph = StateGraph(RecommendState)
    re_graph.add_node(
        "信息提取", functools.partial(extract_node, agent=extract_information(llm))
    )
    re_graph.add_node(
        "产品推荐",
        functools.partial(
            recommend_node, agent=recommend_product(llm), name="产品推荐"
        ),
    )
    re_graph.add_edge("信息提取", "产品推荐")
    re_graph.add_edge("产品推荐", END)
    re_graph.set_entry_point("信息提取")
    return re_graph
