
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from sale_app.database.product import get_product_info
from sale_app.util.history_formate import format_docs

SYSTEM_CONTENT = """
约束：
提取用户信息尽可能的简洁，每个信息点控制在15个字以内
切勿生成聊天内容不存在的信息

请分析这段聊天内容
{history}

从中提取用户信息

如果聊天记录为空，请输出“暂无用户信息”
"""


def extract_information(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", SYSTEM_CONTENT),
        ]
    )
    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('messages', [])),
    ) | prompt | llm


def extract_node(state, agent):
    result = agent.invoke(state)
    if result:
        return {"user_info": result.content}




PRODUCT_RECOMMENDER = """
你的任务是根据用户信息从产品信息中选择合适的产品推荐给客户。

约束：
切勿输出思考过程
切勿输出不存在的产品

用户信息：
{user_info}

产品信息：
{product_info_list}

思维链：
1. 结合<用户信息>和<产品信息>逐个产品来做判断；
2. 根据用户信息有根据的评估每个产品的优劣；
2. 最后，综合所有的合适产品，把最合适的产品推荐给客户。

-输出内容。
推荐的产品，包括产品名称、推荐的依据
"""

def recommend_product(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", PRODUCT_RECOMMENDER),
        ]
    )
    return RunnablePassthrough.assign(
        user_info=lambda x: x.get('user_info', {}),
        product_info_list=lambda x: get_product_info(),
    ) | prompt | llm


def recommend_node(state, agent):
    result = agent.invoke(state)
    if result:
        return {"messages": [AIMessage(content=result.content)],"product_list": result.content}