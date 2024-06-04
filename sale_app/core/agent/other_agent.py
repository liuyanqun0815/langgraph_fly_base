from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from sale_app.core.prompt.chat_manager_prompt import SYSTEM_PROMPT


# 闲聊经理，负责引导用户办理业务
def chat_manager(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )
    return prompt | llm

