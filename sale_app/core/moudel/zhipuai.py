import os
from typing import Optional

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import llm_enable_reasoning


def _env(*keys: str, default: Optional[str] = None) -> Optional[str]:
    for key in keys:
        value = os.environ.get(key)
        if value:
            return value
    return default


class ZhipuAI:
    """LLM 客户端：优先 LLM_*（DashScope 等 OpenAI 兼容接口），回退 ZHIPU_*。"""

    def __init__(
        self,
        openai_api_key: str | None = None,
        openai_api_base: str | None = None,
        model: str | None = None,
        temperature: float | str | None = None,
    ):
        self.openai_api_key = openai_api_key or _env("LLM_API_KEY", "OPENAI_API_KEY", "ZHIPU_API_KEY")
        self.openai_api_base = openai_api_base or _env(
            "LLM_API_BASE",
            "OPENAI_API_BASE",
            "ZHIPU_API_BASE",
            default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        self.model = model or _env("LLM_MODEL", "ZHIPU_MODEL", default="qwen-plus")
        temp = temperature if temperature is not None else _env("LLM_TEMPERATURE", "ZHIPU_TEMPERATURE", default="0.1")
        self.temperature = float(temp) if temp is not None else 0.1
        self._embedding_model = _env("EMBEDDING_MODEL", default="text-embedding-v3")
        self._embedding_dimensions = int(_env("EMBEDDING_DIMENSIONS", default="1024"))

    def _chat_extra_body(self) -> dict | None:
        if not llm_enable_reasoning():
            return None
        # DashScope / 通义千问 OpenAI 兼容：enable_thinking 开启推理模式
        return {"enable_thinking": True}

    def openai_chat(self) -> BaseChatModel:
        extra_body = self._chat_extra_body()
        kwargs = {
            "temperature": self.temperature,
            "model": self.model,
            "openai_api_key": self.openai_api_key,
            "openai_api_base": self.openai_api_base,
        }
        if extra_body:
            kwargs["extra_body"] = extra_body
        return ChatOpenAI(**kwargs)

    def zhipu_chat(self) -> BaseChatModel:
        return self.openai_chat()

    def embedding(self) -> Embeddings:
        return OpenAIEmbeddings(
            model=self._embedding_model,
            openai_api_key=self.openai_api_key,
            openai_api_base=self.openai_api_base,
            dimensions=self._embedding_dimensions,
            check_embedding_ctx_length=False,
        )
