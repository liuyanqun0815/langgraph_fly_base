from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI
import os
from langchain_zhipu import ChatZhipuAI, ZhipuAIEmbeddings



class ZhipuAI:

    def __init__(self, openai_api_key: str = None,
                 openai_api_base: str = None,
                 model: str = None,
                 temperature: float = None):
        if openai_api_key is None:
            self.openai_api_key = os.environ.get("ZHIPU_API_KEY")
        if openai_api_base is None:
            self.openai_api_base = os.environ.get("ZHIPU_API_BASE")
        if model is None:
            self.model = os.environ.get("ZHIPU_MODEL")
        if temperature is None:
            self.temperature = os.environ.get("ZHIPU_TEMPERATURE")

        self._embedding_dimensions = 1024

    def openai_chat(self) -> BaseChatModel:
        return ChatOpenAI(
            temperature=self.temperature,
            model=self.model,
            openai_api_key=self.openai_api_key,
            openai_api_base=self.openai_api_base
        )

    def zhipu_chat(self) -> BaseChatModel:
        return ChatZhipuAI(
            temperature=self.temperature,
            api_key=self.openai_api_key,
            model=self.model
        )


    def embedding(self):
        return ZhipuAIEmbeddings(api_key=self.openai_api_key)
