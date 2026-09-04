from langchain_core.messages import AIMessage, HumanMessage

from config import customer_service_hours, customer_service_phone, offline_branch_hint
from sale_app.config.log import Logger

logger = Logger("fly_base")

_CONVERSION_KEYWORDS = (
    "好的",
    "可以",
    "行",
    "办",
    "办理",
    "申请",
    "想要",
    "需要",
    "同意",
    "没问题",
    "就这个",
    "采纳",
    "接受",
    "试试",
    "感兴趣",
    "怎么联系",
    "联系方式",
    "怎么办理",
    "如何办理",
    "我要办理",
    "我要申请",
    "去哪办",
    "线下办",
)

_REJECTION_KEYWORDS = ("不用", "不要", "再说", "考虑一下", "拒绝", "不感兴趣", "暂时不")


def looks_like_conversion_intent(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if not normalized:
        return False
    if any(keyword in normalized for keyword in _REJECTION_KEYWORDS):
        return False
    if normalized in {"好", "嗯", "ok", "yes"}:
        return True
    return any(keyword in normalized for keyword in _CONVERSION_KEYWORDS)


def looks_like_rejection(text: str) -> bool:
    normalized = (text or "").strip()
    if not normalized:
        return False
    return any(keyword in normalized for keyword in _REJECTION_KEYWORDS)


def build_contact_message() -> str:
    phone = customer_service_phone()
    hours = customer_service_hours()
    branch_hint = offline_branch_hint()
    return (
        "感谢您的认可！如需办理，您可通过以下方式联系我们：\n\n"
        f"📞 人工客服：{phone}（{hours}）\n"
        f"🏢 线下办理：{branch_hint}\n\n"
        "我们的客户经理将协助您完成后续材料提交与审批流程。祝您办理顺利！"
    )


def conversion_node(state, name):
    messages = state.get("messages") or []
    last_message = messages[-1] if messages else None
    user_text = last_message.content if isinstance(last_message, HumanMessage) else ""

    if state.get("conversion_completed"):
        reply = f"{build_contact_message()}\n\n如需了解产品细节，也可继续向我提问。"
        return {"messages": [AIMessage(content=reply)], "pre_node": name}

    if looks_like_rejection(user_text):
        logger.info(f"{name}节点用户暂无意向")
        return {
            "messages": [AIMessage(content="好的，如您后续有贷款需求，欢迎随时联系我们。祝您生活愉快！")],
            "pre_node": name,
            "awaiting_conversion": False,
            "conversion_completed": True,
        }

    if looks_like_conversion_intent(user_text):
        logger.info(f"{name}节点用户有办理意向")
        return {
            "messages": [AIMessage(content=build_contact_message())],
            "pre_node": name,
            "awaiting_conversion": False,
            "conversion_completed": True,
        }

    reply = (
        "如您有意向办理推荐产品，请回复「可以」或「办理」，我将为您提供联系方式；"
        "也可继续提问产品利率、额度等问题。"
    )
    return {
        "messages": [AIMessage(content=reply)],
        "pre_node": name,
        "awaiting_conversion": True,
    }
