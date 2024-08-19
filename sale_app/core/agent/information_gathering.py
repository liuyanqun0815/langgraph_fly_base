import os

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.prompt.chat_manager_prompt import INFORMATION_SYSTEM_PROMPT
from sale_app.secrity.sensitive_info import sensitive_info_anonymize
from sale_app.util.history_formate import format_docs

logger = Logger("fly_base")


class toBeCollectionInformation(BaseModel):
    """
    待收集问题
    """
    information: str = Field(..., deault=None, title="问题", description="待信息收集的问题")
    sequence: int = Field(..., deault=None, title="问题前的序号", description="待信息收集问题前面的序号")
    isRecommend: bool = Field(..., deault=None, description="当用户回答完所有信息的时候,在进行推荐产品")


information_count = 4


def information_gathering(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", INFORMATION_SYSTEM_PROMPT),
            # MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('history', [])),
        question=lambda x: x['question'],  # 直接传递 question 参数
        information_sequences=lambda x: x['information_sequences'],
        information_count=lambda x: information_count,
    ) | prompt | llm.with_structured_output(toBeCollectionInformation)


def information_node(state, agent, name):
    messages = state["messages"]
    state["history"] = messages[:-1]
    last_message = messages[-1]
    logger.info(f"{name}节点信息:{last_message.content}")
    if isinstance(last_message, HumanMessage):
        state["question"] = last_message.content
        if os.getenv("USER_INFO_MASK"):
            state["question"] = sensitive_info_anonymize(last_message.content)
            logger.info(f"{name}节点信息:{last_message.content},脱敏后信息：{state['question']}")
    result = agent.invoke(state)
    if result:
        recommend = True if result.information is '' and result.isRecommend else False
        if recommend is False:
            logger.info(f"{name}节点信息:{result}")
            recommend = True if result.sequence >= information_count else False
        return {"messages": [AIMessage(content=result.information)],
                "information_sequences": [result.sequence],
                "pre_node": name,
                "isRecommend": recommend
                }
    else:
        print("信息收集返回为空")
