from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.kb.kb_sevice import KBService
logger = Logger("fly_base")

# 定义用于生成 AI 响应的提示模板
PROMPT_TEMPLATE = """你是贷款经理，擅长解答贷款问题，尽可能使用基于事实和统计的信息来回答问题。
使用以下信息为 <question> 标签中的问题提供简洁的答案。
如果您不知道答案，就说您不知道，不要试图编造答案。
<context>
{context}
</context>

<question>
{question}
</question>

答案应该具体，并尽可能使用统计数据或数字。

输出:"""

# 使用定义的模板和输入变量创建 PromptTemplate 实例
prompt = PromptTemplate(
    template=PROMPT_TEMPLATE, input_variables=["context", "question"]
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
