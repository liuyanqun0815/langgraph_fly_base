from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnablePassthrough
from langchain_core.pydantic_v1 import BaseModel, Field

from sale_app.core.moudel.zhipuai import ZhipuAI
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
    # contextualize_q_system_prompt = """Given a chat history and the latest user question \
    # which might reference context in the chat history, formulate a standalone question \
    # which can be understood without the chat history. Do NOT answer the question, \
    # just reformulate it if needed and otherwise return it as is"""
    # contextualize_q_system_prompt = """要根据聊天历史记录中可能引用上下文的最新用户问题重新制定独立问题，
    # 最新用户问题：
    # {question}
    #
    # 聊天历史记录:
    # {history}
    #
    # 请执行以下步骤：
    # 确定关键要素：确定用户问题中提到的主要主题和任何具体细节。
    # 检查上下文参考：寻找理解问题所需的聊天前几部分的参考。
    # 重新表述：如果问题依赖于聊天历史中的上下文，请以一种可以理解的方式重新表述。这可能涉及提供必要的背景信息或将问题改写为更笼统的问题。
    # 按原样返回：如果问题已经是独立的，并且不需要聊天历史记录中的任何上下文，则原封不动地返回。
    # 约束规则：
    # 禁止输出步骤，只输出最新用户问题
    # 禁止回答最新用户问题
    #
    # 输出内容
    # 修正后的最新用户问题
    # """

    #     contextualize_q_system_prompt = """你是一名聊天修正助手，你的任务是分析和理解聊天，然后根据这些信息，优化并重新表述用户最新的聊天。
    # #指令：
    # - 绝对不要直接回答用户最新的聊天。
    # - 禁止直接回答用户最新的聊天。
    # - 如果最新的聊天已经足够清晰，无需修改，保持原样。
    # - 绝对改变用户最新的聊天的原意，例如：将原来的陈述句重构成一个问句。
    # - 不要输出思考的过程，只输出最终你的答案
    # - 如果没有聊天历史记录，直接输出原来的最新聊天
    #
    # 使用以下格式:
    # Question: 您必须回答的输入问题
    # Thought: 你应该时刻思考该做什么
    #
    #
    # {history}
    # 最新用户聊天内容：{question}
    #
    # 输出语言形式: 中文
    # """
    contextualize_q_system_prompt = """给我优化下最新的聊天问题，有根据的分析和理解聊天，根据这些信息，优化并重新表述用户最新的问题。
务必始终通过调用‘FixedQuestion’函数进行回复。切勿要求用户提供其他信息。
切勿以除函数意外的任何其他方式回复。
切勿回答问题。
这个问题无需聊天记录即可理解，则按照原样返回；否则重新表述最新问题。
    
{history}
用户最新的问题：{question}
"""

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("user", contextualize_q_system_prompt),
            # MessagesPlaceholder("messages"),
        ]
    )

    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('history', [])),
        question=lambda x: x['question']  # 直接传递 question 参数
    ) | contextualize_q_prompt | llm.with_structured_output(FixedQuestion)



# llm = ZhipuAI().openai_chat()
# #
# fix = fix_question(llm)
# data = fix.invoke({"question": "最近有点缺钱",
#
#                    "history": [
#                        HumanMessage(content='你好'),
#                        AIMessage(
#                            content='您好！很高兴为您服务。如果您有任何贷款需求或对贷款产品有任何疑问，请随时告诉我，我会根据您的具体情况为您推荐合适的产品。玩笑归玩笑，但我是真心希望能帮到您。那么，您是否真的有贷款方面的需求呢？我们可以从这里开始探讨。')
#
#                    ]
#                    }
#                   )
# print(data)
