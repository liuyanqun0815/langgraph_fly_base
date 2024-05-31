from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.language_models import BaseChatModel


# 问题修正节点
def fix_question(llm: BaseChatModel):
    """
    根据上下文，重新构造问题
    """
    # contextualize_q_system_prompt = """Given a chat history and the latest user question \
    # which might reference context in the chat history, formulate a standalone question \
    # which can be understood without the chat history. Do NOT answer the question, \
    # just reformulate it if needed and otherwise return it as is"""

    contextualize_q_system_prompt = """你是一名问题重构专家，你的任务是分析和理解对话上下文，然后根据这些信息，优化并重新表述用户最新提出的问题。你的目标是通过重构问题来引导对话，而不是直接提供答案。

    #指令：
    - 绝对不要直接回答用户的问题。
    - 专注于理解对话的流程和意图。
    - 根据对话历史，改进问题的表述，使其更清晰、更具体或更具指导性。
    - 如果问题已经足够清晰，无需修改，保持原样。
    - 请不要添加任何额外的信息。
    - 言简意赅的问题更容易理解。

    请根据这些指导原则，处理用户的问题。
    """

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("messages"),
            ("human", "{question}"),
        ]
    )
    return contextualize_q_prompt | llm
    # return chain.invoke({"input": question})

#
# fix = fix_question()
# data = fix.invoke({"messages": [{"role": "user", "content": "my name is liuyanqun"}]})
# print(data)
