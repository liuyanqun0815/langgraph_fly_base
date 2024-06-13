from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.util.history_formate import format_docs

SYSTEM_CONTENT = """
你是银行贷款营销经理，你的任务根据客户的聊天内容，能够判断客户是否存在贷款意图

{history}
用户最新的问题：{question}

务必始终通过调用‘IntentionConfirm’函数进行回复。
切勿以除函数意外的任何其他方式回复。
"""


class IntentionConfirm(BaseModel):
    """
    客户意图确认
    """
    isIntention: bool = Field(..., deault=None, description="是否存在意图")


def intention_confirm(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", SYSTEM_CONTENT),
        ]
    )
    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('history', [])),
        question=lambda x: x['question'],  # 直接传递 question 参数
    ) | prompt | llm.with_structured_output(IntentionConfirm)


def intention_node(state, agent, name):
    messages = state["messages"]
    state["history"] = messages[:-1]
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        state["question"] = last_message.content
    result = agent.invoke(state)
    if result:
        return {"pre_node": name, "next": "信息收集" if result.isIntention else "闲聊经理"}

