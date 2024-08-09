from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.prompt.chat_manager_prompt import INTENTION_SYSTEM_CONTENT
from sale_app.util.history_formate import format_docs

logger = Logger("fly_base")


class IntentionConfirm(BaseModel):
    """
    客户意图确认
    """
    isIntention: bool = Field(..., deault=None, description="是否存在意图")


def intention_confirm(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", INTENTION_SYSTEM_CONTENT),
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
    logger.info(f"{name}节点信息:{last_message.content}")
    if isinstance(last_message, HumanMessage):
        state["question"] = last_message.content
    result = agent.invoke(state)
    if result:
        return {"pre_node": name, "next": "信息收集" if result.isIntention else "闲聊经理"}
