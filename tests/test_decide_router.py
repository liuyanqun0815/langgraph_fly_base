from sale_app.core.mutil.node_names import NextNode


def _decide_router(state):
    """与 flow_graph.decide_router 保持同逻辑的可导入副本验证；实现后改为直接 import。"""
    from sale_app.core.mutil.flow_routers import decide_router

    return decide_router(state)


def test_router_qa():
    assert _decide_router({"next": NextNode.QA}) == NextNode.QA


def test_router_recommend():
    assert _decide_router({"next": NextNode.RECOMMEND}) == NextNode.RECOMMEND


def test_router_gather_sticky():
    state = {"next": NextNode.CHAT, "pre_node": NextNode.GATHER}
    assert _decide_router(state) == NextNode.GATHER


def test_router_gather_to_qa_allowed():
    state = {"next": NextNode.QA, "pre_node": NextNode.GATHER}
    assert _decide_router(state) == NextNode.QA


def test_router_recommend_blocked_until_collection_complete():
    state = {
        "next": NextNode.RECOMMEND,
        "pre_node": NextNode.GATHER,
        "information_sequences": [1, 2, 3],
    }
    assert _decide_router(state) == NextNode.GATHER


def test_router_recommend_redirects_to_confirm_when_not_confirmed():
    state = {
        "next": NextNode.RECOMMEND,
        "pre_node": NextNode.CONFIRM,
        "information_sequences": [1, 2, 3, 4],
        "isInfoConfirmed": False,
    }
    assert _decide_router(state) == NextNode.CONFIRM


def test_router_confirm_sticky():
    state = {
        "next": NextNode.CHAT,
        "pre_node": NextNode.CONFIRM,
        "awaiting_info_confirm": True,
        "isInfoConfirmed": False,
    }
    assert _decide_router(state) == NextNode.CONFIRM
