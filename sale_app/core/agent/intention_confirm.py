from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate


def intention_confirm(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_template(
        [
            ("system", "您是一个擅长{ability}的助手。回答不超过20个字"),
            ("placeholder", "{messages}"),

        ]
    )


