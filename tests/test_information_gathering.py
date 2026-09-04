from langchain_core.messages import AIMessage, HumanMessage

from sale_app.core.agent.collection_utils import is_collection_complete
from sale_app.core.agent.information_gathering import (
    build_collection_reply,
    resolve_collection_progress,
    toBeCollectionInformation,
)
from sale_app.core.mutil.flow_routers import information_router
from sale_app.core.mutil.node_names import NextNode


def test_is_collection_complete_requires_all_steps():
    assert not is_collection_complete({"information_sequences": [1, 2, 3]})
    assert is_collection_complete({"information_sequences": [1, 2, 3, 4]})


def test_information_router_blocks_recommend_until_complete():
    incomplete = {"isRecommend": True, "information_sequences": [1, 2, 3]}
    assert information_router(incomplete) == NextNode.FINISH

    complete = {"isRecommend": True, "information_sequences": [1, 2, 3, 4]}
    assert information_router(complete) == NextNode.CONFIRM


def test_resolve_collection_fourth_answer_triggers_complete():
    state = {
        "pre_node": NextNode.GATHER,
        "information_sequences": [1, 2, 3],
        "messages": [
            AIMessage(content="请问您的年龄是多少？"),
            HumanMessage(content="35岁"),
        ],
    }
    delta, steps_done, next_step = resolve_collection_progress(state)
    assert delta == [4]
    assert steps_done == 4
    assert next_step == 5
    merged_state = {"information_sequences": [1, 2, 3, 4]}
    assert is_collection_complete(merged_state)


def test_resolve_collection_third_answer_not_complete():
    state = {
        "pre_node": NextNode.GATHER,
        "information_sequences": [1, 2],
        "messages": [
            AIMessage(content="请问您希望的贷款期限是多久？"),
            HumanMessage(content="4年"),
        ],
    }
    delta, steps_done, next_step = resolve_collection_progress(state)
    assert delta == [3]
    assert steps_done == 3
    assert next_step == 4
    merged_state = {"information_sequences": [1, 2, 3]}
    assert not is_collection_complete(merged_state)


def test_resolve_collection_first_turn():
    state = {
        "pre_node": NextNode.INTENT,
        "information_sequences": [],
        "messages": [HumanMessage(content="我想申请贷款")],
    }
    delta, steps_done, next_step = resolve_collection_progress(state)
    assert delta == []
    assert steps_done == 0
    assert next_step == 1


def test_resolve_collection_after_user_answer():
    state = {
        "pre_node": NextNode.GATHER,
        "information_sequences": [],
        "messages": [
            AIMessage(content="请问您的贷款用途是什么？"),
            HumanMessage(content="可能会购房和装修"),
        ],
    }
    delta, steps_done, next_step = resolve_collection_progress(state)
    assert delta == [1]
    assert steps_done == 1
    assert next_step == 2


def test_build_collection_reply_rejects_echo():
    result = toBeCollectionInformation(information="购房和装修", sequence=2, isRecommend=False)
    reply = build_collection_reply(result, next_step=2, user_text="可能会购房和装修")
    assert "贷款金额" in reply
    assert "？" in reply


def test_build_collection_reply_accepts_valid_question():
    result = toBeCollectionInformation(
        information="好的，了解到您可能用于购房和装修。请问您期望申请的贷款金额是多少？",
        sequence=2,
        isRecommend=False,
    )
    reply = build_collection_reply(result, next_step=2, user_text="可能会购房和装修")
    assert "贷款金额" in reply


def test_third_answer_does_not_trigger_complete_without_message():
    import os
    import sys
    from unittest.mock import MagicMock

    sys.modules.setdefault("sale_app.secrity.sensitive_info", MagicMock())
    sys.modules.pop("sale_app.core.agent.information_gathering", None)
    from sale_app.core.agent.information_gathering import information_node

    agent = MagicMock()
    agent.invoke.return_value = toBeCollectionInformation(
        information="好的，了解到您希望的贷款期限是3年。请问您的年龄是多少？",
        sequence=4,
        isRecommend=False,
    )
    state = {
        "pre_node": NextNode.GATHER,
        "information_sequences": [1, 2],
        "messages": [
            AIMessage(content="请问您希望的贷款期限是多久？"),
            HumanMessage(content="3年"),
        ],
    }
    old_mask = os.environ.pop("USER_INFO_MASK", None)
    try:
        result = information_node(state, agent, NextNode.GATHER)
    finally:
        if old_mask is not None:
            os.environ["USER_INFO_MASK"] = old_mask

    assert result["isRecommend"] is False
    assert "年龄" in result["messages"][0].content
    agent.invoke.assert_called_once()
