from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from sale_app.config.log import Logger
from sale_app.core.prompt.chat_manager_prompt import OTHER_SYSTEM_PROMPT

logger = Logger("fly_base")


# 闲聊经理，负责引导用户办理业务
def chat_manager(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", OTHER_SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )
    return prompt | llm


def agent_node(state, agent, name):
    logger.info(f"{name}节点内容: {state['question']}")
    result = agent.invoke(state)
    return {"messages": [AIMessage(content=result.content)], "pre_node": name}
