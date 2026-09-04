from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.kb.kb_sevice import KBService
from sale_app.core.prompt.chat_manager_prompt import QUESTION_PROMPT_TEMPLATE

logger = Logger("fly_base")


def format_kb_context(docs) -> str:
    """将检索文档格式化为 LLM 可用的 context，优先使用 page_content。"""
    if not docs:
        return ""
    blocks = []
    for index, doc in enumerate(docs, start=1):
        page_content = (getattr(doc, "page_content", "") or "").strip()
        if not page_content:
            continue
        metadata = getattr(doc, "metadata", None) or {}
        if not isinstance(metadata, dict):
            metadata = {}
        source = metadata.get("source") or metadata.get("file_name") or ""
        header = f"[资料{index}]"
        if source:
            header += f" 来源:{source}"
        blocks.append(f"{header}\n{page_content}")
    return "\n\n".join(blocks)


def _retrieve_context(question: str) -> str:
    if not question:
        return ""
    docs = KBService.hybrid_search(question, top_k=5)
    if not docs:
        docs = KBService.similarity_search(question)
    context = format_kb_context(docs)
    logger.info(f"QA检索命中 {len(docs)} 条，context 长度={len(context)}")
    return context


# 使用定义的模板和输入变量创建 PromptTemplate 实例
prompt = PromptTemplate(
    template=QUESTION_PROMPT_TEMPLATE, input_variables=["context", "question"]
)


class QAHandle(BaseModel):
    """
    客户意图确认
    """
    isIntention: bool = Field(default=None, description="是否存在意图")


def qa_agent(llm: BaseChatModel):
    rag_chain = (
        RunnablePassthrough.assign(
            context=lambda x: _retrieve_context(x.get("question") or ""),
            question=lambda x: x["question"],
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
