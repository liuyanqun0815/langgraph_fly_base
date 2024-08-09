import functools
import operator
from typing import TypedDict, Annotated, List

from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, END

from sale_app.config.log import Logger
from sale_app.core.agent.recommend_product import extract_node, extract_information, recommend_node, recommend_product
from sale_app.core.moudel.zhipuai import ZhipuAI

llm = ZhipuAI().openai_chat()
logger = Logger("fly_base")


class RecommendState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_info: str  # 提取用户信息


re_graph = StateGraph(RecommendState)

re_graph.add_node("信息提取", functools.partial(extract_node, agent=extract_information(llm)))
re_graph.add_node("产品推荐", functools.partial(recommend_node, agent=recommend_product(llm), name="产品推荐"))

re_graph.add_edge("信息提取", "产品推荐")
re_graph.add_edge("产品推荐", END)

re_graph.set_entry_point("信息提取")
