from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.prompt.chat_manager_prompt import USER_EXTRACT_SYSTEM_CONTENT, PRODUCT_RECOMMENDER_SYSTEM
from sale_app.database.product import get_product_info
from sale_app.util.history_formate import format_docs

logger = Logger("fly_base")


def extract_information(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", USER_EXTRACT_SYSTEM_CONTENT),
        ]
    )
    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('messages', [])),
    ) | prompt | llm


def extract_node(state, agent):
    logger.info(f"信息提取节点:{state.get('history')}")
    result = agent.invoke(state)
    if result:
        return {"user_info": result.content}


def recommend_product(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", PRODUCT_RECOMMENDER_SYSTEM),
        ]
    )
    return RunnablePassthrough.assign(
        user_info=lambda x: x.get('user_info', {}),
        product_info_list=lambda x: get_product_info(),
    ) | prompt | llm


def recommend_node(state, agent, name):
    logger.info(f"{name}节点内容:{state}")
    result = agent.invoke(state)
    if result:
        return {"messages": [AIMessage(content=result.content)], "product_list": result.content, "pre_node": name}
