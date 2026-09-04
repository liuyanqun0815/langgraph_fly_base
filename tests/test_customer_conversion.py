from langchain_core.messages import HumanMessage

from sale_app.core.agent.customer_conversion import (
    build_contact_message,
    conversion_node,
    looks_like_conversion_intent,
)
from sale_app.core.mutil.classify_utils import route_after_recommendation
from sale_app.core.mutil.flow_routers import decide_router
from sale_app.core.mutil.node_names import NextNode


def test_looks_like_conversion_intent():
    assert looks_like_conversion_intent("好的，可以")
    assert looks_like_conversion_intent("我要办理这个")
    assert looks_like_conversion_intent("这个怎么办理")
    assert not looks_like_conversion_intent("不用了")


def test_route_after_recommendation_to_conversion():
    state = {"product_list": "安馨贷", "awaiting_conversion": True}
    assert route_after_recommendation(state, "好的，可以") == NextNode.CONVERSION
    assert route_after_recommendation(state, "这个怎么办理") == NextNode.CONVERSION
    assert route_after_recommendation(state, "利率多少") == NextNode.QA


def test_has_recommended_from_messages_fallback():
    from langchain_core.messages import AIMessage

    from sale_app.core.mutil.classify_utils import has_recommended

    state = {
        "isInfoConfirmed": True,
        "messages": [AIMessage(content="推荐产品名称：安馨贷\n推荐理由：...")],
    }
    assert has_recommended(state)


def test_decide_router_blocks_reconfirm_after_recommend():
    state = {
        "next": "信息收集",
        "pre_node": "产品推荐",
        "product_list": "安馨贷",
        "question": "好的，可以",
    }
    assert decide_router(state) == NextNode.CONVERSION


def test_conversion_node_returns_contact_info():
    state = {
        "messages": [HumanMessage(content="好的，可以")],
        "product_list": "安馨贷",
    }
    result = conversion_node(state, NextNode.CONVERSION)
    assert result["conversion_completed"] is True
    assert "人工客服" in result["messages"][0].content
    assert customer_service_phone_in_message(result["messages"][0].content)


def customer_service_phone_in_message(text: str) -> bool:
    return "400" in text or "客服" in text


def test_build_contact_message_contains_phone():
    message = build_contact_message()
    assert "人工客服" in message
    assert "线下办理" in message
