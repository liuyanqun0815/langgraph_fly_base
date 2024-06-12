from sale_app.config.log import Logger
from sale_app.core.moudel.zhipuai import ZhipuAI

logger = Logger("fly_base")


def pre_handle(question: str) -> dict | None:
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
        logger.error(e)
        return e.body.get("message")


from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

tagging_prompt = ChatPromptTemplate.from_template(
    """
从以下段落中提取所需的信息。
必须提取“Classification”功能中提到的属性。

输入内容：
{input}
"""
)

tip = {
    "isPublicSafety": "文本描述是否危害公共安全或恶俗的言论",
    "isPolitical": "文本内容是否涉及法律或政治敏感",
    "isReligiousConflict": "文本内容是否涉及宗教冲突或文化不适的话题",
    "isProgram": "文本内容是否存在编程代码、函数方法相关",
    "isTranslate": "文本内容是否涉及翻译，例如，你好翻译成英文，你好翻译成韩语等",
    "isContentCreation": "文本内容是否涉及内容创作，例如写一篇论文，写一首诗等",
}


class Classification(BaseModel):
    isPublicSafety: int = Field(
        default=1,
        description="文本描述是否危害公共安全或恶俗的言论，数字越高，越危险",
        enum=[1, 2, 3, 4, 5, 6, 7, 8],
    )
    isPolitical: bool = Field(description=tip["isPolitical"],
                              default=False,
                              enum=[True, False])
    isProgram: bool = Field(description=tip["isProgram"],
                            default=False,
                            enum=[True, False])
    isTranslate: bool = Field(description=tip["isTranslate"],
                              default=False,
                              enum=[True, False])
    isReligiousConflict: bool = Field(description=tip["isReligiousConflict"],
                                     default=False,
                                     enum=[True, False])
    isContentCreation: bool = Field(description=tip["isContentCreation"],
                                    default=False,
                                    enum=[True, False])
    isSpecialSymbols: bool = Field(description="文本内容是否带'{'、'['、'('、')'、等符号",
                                   default=False,
                                   enum=[True, False])
    isHtmlSymbols: bool = Field(description="文本内容是否带html标签信息",
                                default=False,
                                enum=[True, False])


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
