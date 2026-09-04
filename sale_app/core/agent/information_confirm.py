from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from sale_app.config.log import Logger
from sale_app.core.mutil.node_names import NextNode
from sale_app.core.prompt.chat_manager_prompt import INFORMATION_SUMMARY_PROMPT
from sale_app.util.history_formate import format_docs

logger = Logger("fly_base")

_CONFIRM_KEYWORDS = ("确认", "没问题", "正确", "对的", "可以", "是的", "好的", "ok", "yes")
_CORRECTION_KEYWORDS = ("改", "修改", "不对", "错了", "更正", "补充", "换成", "应该是")
_DEFAULT_CONFIRM_SUFFIX = "以上信息是否正确？如无问题请回复「确认」，如需修改请直接说明。"


def _looks_confirmed(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    if normalized in _CONFIRM_KEYWORDS:
        return True
    return any(keyword in normalized for keyword in _CONFIRM_KEYWORDS if len(keyword) > 1)


def _looks_like_correction(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    return any(keyword in normalized for keyword in _CORRECTION_KEYWORDS)


def _extract_text(result) -> str:
    if result is None:
        return ""
    content = getattr(result, "content", result)
    if isinstance(content, str):
        return content.strip()
    return str(content).strip()


def _build_summary_message(content: str) -> str:
    text = (content or "").strip()
    if not text:
        return _DEFAULT_CONFIRM_SUFFIX
    if _DEFAULT_CONFIRM_SUFFIX in text or "请回复「确认」" in text:
        return text
    return f"{text}\n\n{_DEFAULT_CONFIRM_SUFFIX}"


def information_summary(llm: BaseChatModel):
    """使用普通文本输出，避免 DashScope structured_output grammar 编译超时。"""
    prompt = ChatPromptTemplate.from_messages([("user", INFORMATION_SUMMARY_PROMPT)])
    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get("messages", [])),
    ) | prompt | llm


def information_confirm_node(state, summary_agent, name):
    messages = state.get("messages") or []
    last_message = messages[-1] if messages else None
    pre_node = state.get("pre_node") or ""

    entering_from_gather = pre_node == NextNode.GATHER and not state.get("awaiting_info_confirm")
    if entering_from_gather or not state.get("info_summary"):
        summary_result = summary_agent.invoke(state)
        summary_text = _build_summary_message(_extract_text(summary_result))
        logger.info(f"{name}节点生成摘要")
        return {
            "messages": [AIMessage(content=summary_text)],
            "pre_node": name,
            "awaiting_info_confirm": True,
            "isInfoConfirmed": False,
            "info_summary": summary_text,
        }

    if not isinstance(last_message, HumanMessage):
        fallback = state.get("info_summary") or _DEFAULT_CONFIRM_SUFFIX
        return {
            "messages": [AIMessage(content=fallback)],
            "pre_node": name,
            "awaiting_info_confirm": True,
            "isInfoConfirmed": False,
        }

    user_text = last_message.content or ""
    state["question"] = user_text

    if _looks_confirmed(user_text) and not _looks_like_correction(user_text):
        logger.info(f"{name}节点用户已确认")
        return {
            "messages": [AIMessage(content="好的，已确认您的信息，正在为您匹配推荐方案…")],
            "pre_node": name,
            "awaiting_info_confirm": False,
            "isInfoConfirmed": True,
        }

    if _looks_like_correction(user_text):
        summary_result = summary_agent.invoke(state)
        summary_text = _build_summary_message(_extract_text(summary_result))
        logger.info(f"{name}节点用户提出修改，已更新摘要")
        return {
            "messages": [AIMessage(content=f"好的，已记录您的修改。\n\n{summary_text}")],
            "pre_node": name,
            "awaiting_info_confirm": True,
            "isInfoConfirmed": False,
            "info_summary": summary_text,
        }

    reply = "请确认以上信息是否正确？回复「确认」或说明需要修改的内容。"
    return {
        "messages": [AIMessage(content=reply)],
        "pre_node": name,
        "awaiting_info_confirm": True,
        "isInfoConfirmed": False,
    }
