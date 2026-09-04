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
# 任务
对用户输入进行安全与合规分类，提取 Classification 模型所需的全部字段。

# 评分与判断要求
- isPublicSafety：1～8 分，分数越高表示危害公共安全或低俗恶俗程度越高；≥4 视为需拦截。
- 其余布尔字段：仅当内容 **明确符合** 字段描述时为 true，不确定时为 false。
- 不要过度敏感，正常的贷款业务咨询不应误判。

# 用户输入
{input}

请输出结构化 Classification 结果。
"""
)

tip = {
    "isPublicSafety": "含暴力威胁、极端言论、色情低俗、人身攻击等危害公共安全或恶俗内容",
    "isPolitical": "涉及敏感政治话题、煽动对立或不当政治言论",
    "isReligiousConflict": "涉及宗教冲突、歧视或可能引发文化对立的内容",
    "isProgram": "以编写/调试代码、函数、脚本为主要诉求（非业务咨询）",
    "isTranslate": "主要诉求为语言翻译（如「你好翻译成英文」）",
    "isContentCreation": "主要诉求为代写长文、论文、诗歌等创作任务",
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
