from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.kb.kb_sevice import KBService
from sale_app.core.prompt.chat_manager_prompt import QUESTION_PROMPT_TEMPLATE

logger = Logger("fly_base")



# 使用定义的模板和输入变量创建 PromptTemplate 实例
prompt = PromptTemplate(
    template=QUESTION_PROMPT_TEMPLATE, input_variables=["context", "question"]
)


# 定义一个函数来格式化检索到的文档


class QAHandle(BaseModel):
    """
    客户意图确认
    """
    isIntention: bool = Field(..., deault=None, description="是否存在意图")


def format_docs(docs):
    return "\n\n".join(doc.metadata.__str__() for doc in docs)


def qa_agent(llm: BaseChatModel):
    rag_chain = (
            RunnablePassthrough.assign(
                context=lambda x: format_docs(KBService.similarity_search(x.get('question'))),
                question=lambda x: x['question'],  # 直接传递 question 参数
            )
            | prompt
            | llm
    )
    return rag_chain


def qa_node(state, agent, name):
    messages = state["messages"]
    state["history"] = messages[:-1]
    logger.info(f"{name}节点内容: {state['fixed_question']}")
    last_message = messages[-1]
    if isinstance(last_message, HumanMessage):
        state["question"] = state["fixed_question"]
    result = agent.invoke(state)
    if result:
        return {"messages": [AIMessage(content=result.content)], "pre_node": name}
