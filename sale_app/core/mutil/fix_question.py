from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnablePassthrough
from langchain_core.pydantic_v1 import BaseModel, Field

from sale_app.core.prompt.chat_manager_prompt import CONTEXTUALIZE_Q_SYSTEM_PROMPT
from sale_app.util.history_formate import format_docs


class FixedQuestion(BaseModel):
    """重构最新问题"""
    fixQuestion: str = Field(..., deault=None, title="最新问题",
                             description="使用大模型结合聊天记录，经过大模型修正后的最新问题")


def fixed_question_node(state, agent):
    messages = state["messages"]
    last_message = messages[-1]
    # 如果是客户提问，就修正问题
    state["history"] = messages[:-1]
    if isinstance(last_message, HumanMessage):
        state["question"] = last_message.content
    result = agent.invoke(state)
    return {"fixed_question": result.fixQuestion, "question": state["question"]}


# 问题修正节点
def fix_question(llm: BaseChatModel):
    """
    根据上下文，重新构造问题
    """

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("user", CONTEXTUALIZE_Q_SYSTEM_PROMPT),
            # MessagesPlaceholder("messages"),
        ]
    )

    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('history', [])),
        question=lambda x: x['question']  # 直接传递 question 参数
    ) | contextualize_q_prompt | llm.with_structured_output(FixedQuestion)
