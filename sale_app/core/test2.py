from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from sale_app.core.moudel.zhipuai import ZhipuAI


# 问题修正节点
def fix_question():
    """
    根据上下文，重新构造问题
    """
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as is"""
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("messages"),
            # ("human", "{question}"),
        ]
    )
    llm = ZhipuAI().openai_chat()
    return contextualize_q_prompt | llm
    # return chain.invoke({"input": question})


fix = fix_question()
data = fix.invoke({"messages": [{"role": "user", "content": "my name is liuyanqun"}]})
print(data)
