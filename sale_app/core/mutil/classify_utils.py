import json

from langchain_core.messages import AIMessage

from sale_app.core.agent.customer_conversion import looks_like_conversion_intent
from sale_app.core.mutil.node_names import NextNode

VALID_CLASSIFY_CATEGORIES = (
    NextNode.GATHER,
    NextNode.CHAT,
    NextNode.INTENT,
    NextNode.RECOMMEND,
    NextNode.QA,
)

PRODUCT_QA_KEYWORDS = (
    "利率",
    "额度",
    "期限",
    "产品",
    "贷款",
    "材料",
    "审批",
    "担保",
    "还款",
    "多少",
    "条件",
    "准入",
)

CONVERSION_PHRASES = (
    "怎么办理",
    "如何办理",
    "我要办理",
    "怎么申请",
    "如何申请",
    "去哪办理",
    "线下办理",
    "联系方式",
    "人工客服",
)


def _message_indicates_recommendation(messages) -> bool:
    markers = ("推荐产品名称", "推荐理由", "安馨贷", "永续贷")
    for message in reversed(messages or []):
        if not isinstance(message, AIMessage):
            continue
        content = message.content if isinstance(message.content, str) else str(message.content)
        if any(marker in content for marker in markers):
            return True
    return False


def has_recommended(state: dict) -> bool:
    if state.get("product_list") or state.get("awaiting_conversion"):
        return True
    if state.get("isInfoConfirmed") and _message_indicates_recommendation(state.get("messages")):
        return True
    return False


def looks_like_product_qa(question: str) -> bool:
    text = (question or "").strip()
    if not text:
        return False
    if looks_like_conversion_intent(text):
        return False
    if any(phrase in text for phrase in CONVERSION_PHRASES):
        return False
    if any(keyword in text for keyword in ("怎么", "如何")) and any(
        word in text for word in ("办理", "申请", "联系", "客服")
    ):
        return False
    return any(keyword in text for keyword in PRODUCT_QA_KEYWORDS)


def route_after_recommendation(state: dict, question: str) -> str | None:
    """推荐完成后的优先路由；返回 None 表示走常规分类。"""
    if not has_recommended(state):
        return None
    if looks_like_conversion_intent(question):
        return NextNode.CONVERSION
    if any(phrase in (question or "") for phrase in CONVERSION_PHRASES):
        return NextNode.CONVERSION
    if looks_like_product_qa(question):
        return NextNode.QA
    if state.get("awaiting_conversion") and not state.get("conversion_completed"):
        return NextNode.CONVERSION
    return None


def extract_json_text(content: str) -> str:
    text = (content or "").strip()
    if not text:
        return ""
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_category_name(content: str, fallback: str = NextNode.CHAT) -> str:
    text = extract_json_text(content)
    if not text:
        return fallback
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        for name in VALID_CLASSIFY_CATEGORIES:
            if name in text:
                return name
        return fallback
    category_name = (data or {}).get("category_name")
    if category_name in VALID_CLASSIFY_CATEGORIES:
        return category_name
    return fallback


def fallback_category(state: dict) -> str:
    question = (state.get("question") or "").strip()

    post_recommend = route_after_recommendation(state, question)
    if post_recommend:
        return post_recommend

    if state.get("awaiting_info_confirm") and not state.get("isInfoConfirmed"):
        return NextNode.CONFIRM

    if state.get("pre_node") == NextNode.CONFIRM and not state.get("isInfoConfirmed"):
        return NextNode.CONFIRM

    if state.get("pre_node") == NextNode.GATHER and not state.get("isInfoConfirmed"):
        from sale_app.core.agent.collection_utils import is_collection_complete

        if not is_collection_complete(state):
            return NextNode.GATHER

    return NextNode.CHAT


def suggest_category_from_state(state: dict) -> str | None:
    """规则快速路由；返回 None 表示仍需调用分类 LLM。"""
    question = (state.get("question") or "").strip()
    pre_node = state.get("pre_node") or ""

    post_recommend = route_after_recommendation(state, question)
    if post_recommend:
        return post_recommend

    if state.get("awaiting_info_confirm") and not state.get("isInfoConfirmed"):
        return NextNode.CONFIRM

    if pre_node == NextNode.CONFIRM and not state.get("isInfoConfirmed"):
        return NextNode.CONFIRM

    if state.get("awaiting_conversion") and not state.get("conversion_completed"):
        return NextNode.CONVERSION

    return None
