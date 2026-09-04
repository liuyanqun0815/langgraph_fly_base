from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from sale_app.core.agent.information_confirm import (
    _looks_confirmed,
    _looks_like_correction,
    information_confirm_node,
)
from sale_app.core.mutil.flow_routers import confirm_router, information_router
from sale_app.core.mutil.node_names import NextNode


def test_looks_confirmed():
    assert _looks_confirmed("确认")
    assert _looks_confirmed("没问题，确认")
    assert not _looks_confirmed("年龄改成40岁")


def test_looks_like_correction():
    assert _looks_like_correction("年龄改成40岁")
    assert not _looks_like_correction("确认")


def test_information_router_routes_to_confirm_when_complete():
    complete = {"isRecommend": True, "information_sequences": [1, 2, 3, 4]}
    assert information_router(complete) == NextNode.CONFIRM


def test_confirm_router_requires_confirmation():
    assert confirm_router({"isInfoConfirmed": False}) == NextNode.FINISH
    assert confirm_router({"isInfoConfirmed": True}) == NextNode.RECOMMEND


def test_confirm_node_generates_summary_after_gather():
    summary_agent = MagicMock()
    summary_agent.invoke.return_value = AIMessage(
        content="贷款用途：购房\n贷款金额：50万元\n贷款期限：3年\n客户年龄：35岁"
    )

    state = {
        "pre_node": NextNode.GATHER,
        "messages": [HumanMessage(content="35岁")],
        "information_sequences": [1, 2, 3, 4],
    }
    result = information_confirm_node(state, summary_agent, "信息确认")
    assert result["awaiting_info_confirm"] is True
    assert result["isInfoConfirmed"] is False
    assert "贷款用途" in result["messages"][0].content
    assert "确认" in result["messages"][0].content


def test_confirm_node_starts_recommend_after_user_confirms():
    summary_agent = MagicMock()

    state = {
        "pre_node": NextNode.CONFIRM,
        "awaiting_info_confirm": True,
        "info_summary": "贷款用途：购房",
        "messages": [
            AIMessage(content="请确认信息"),
            HumanMessage(content="确认"),
        ],
    }
    result = information_confirm_node(state, summary_agent, "信息确认")
    assert result["isInfoConfirmed"] is True
    assert result["awaiting_info_confirm"] is False
    summary_agent.invoke.assert_not_called()
