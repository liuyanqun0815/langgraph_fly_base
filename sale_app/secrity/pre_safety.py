from sale_app.config.log import Logger
from sale_app.core.moudel.zhipuai import ZhipuAI

logger = Logger("fly_base")


def _safe_reject_message(exc: Exception) -> None:
    """安全模块失败时放行到主流程，避免因 LLM 异常导致整站不可用。"""
    return None


def pre_handle(question: str) -> str | None:
    llm = ZhipuAI().openai_chat()
    model = llm.with_structured_output(
        Classification
    )
    tagging_chain = tagging_prompt | model
    try:
        obj = tagging_chain.invoke({"input": question})
        logger.info("敏感信息过滤:{}".format(obj))
        # 遍历对象的属性
        return cicile_attribute(obj)
    except Exception as e:
        logger.logger.exception("pre_handle failed: %s", e)
        return _safe_reject_message(e)


from langchain_core.prompts import ChatPromptTemplate
from typing import Literal

from pydantic import BaseModel, Field

tagging_prompt = ChatPromptTemplate.from_template(
    """
从以下段落中提取所需的信息。
必须提取“Classification”功能中提到的属性。

输入内容：
{input}
"""
)

tip = {
    "isPublicSafety": "文本描述危害公共安全或恶俗的言论",
    "isPolitical": "文本内容涉及法律或政治敏感",
    "isReligiousConflict": "文本内容涉及宗教冲突或文化不适的话题",
    "isProgram": "文本内容存在编程代码、函数方法相关",
    "isTranslate": "文本内容涉及翻译，例如，你好翻译成英文，你好翻译成韩语等",
    "isContentCreation": "文本内容涉及内容创作，例如写一篇论文，写一首诗等",
}


class Classification(BaseModel):
    isPublicSafety: Literal[1, 2, 3, 4, 5, 6, 7, 8] = Field(
        default=1,
        description="文本描述是否危害公共安全或恶俗的言论，数字越高，越危险",
    )
    isPolitical: bool = Field(description=tip["isPolitical"], default=False)
    isProgram: bool = Field(description=tip["isProgram"], default=False)
    isTranslate: bool = Field(description=tip["isTranslate"], default=False)
    isReligiousConflict: bool = Field(description=tip["isReligiousConflict"], default=False)
    isContentCreation: bool = Field(description=tip["isContentCreation"], default=False)
    isSpecialSymbols: bool = Field(description="文本内容是否带'{'、'['、'('、')'、等符号", default=False)
    isHtmlSymbols: bool = Field(description="文本内容是否带html标签信息", default=False)


def cicile_attribute(obj: Classification) -> str | None:
    for attr in dir(obj):
        # 忽略魔术方法和属性
        if not attr.startswith('__'):
            # 检查属性是否存在并且获取其值
            if hasattr(obj, attr):
                value = getattr(obj, attr)
                # 判断属性值是否为True
                if isinstance(value, bool):
                    if value is True:
                        return tip[attr]
                if isinstance(value, int):
                    if value > 3:
                        return tip[attr]
    return None


# LLM


# if __name__ == '__main__':
#     d = pre_handle("美国文化是垃圾")
#     print(d)
