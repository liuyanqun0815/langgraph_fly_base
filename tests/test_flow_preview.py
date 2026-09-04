from langchain_core.messages import HumanMessage

from sale_app.core.mutil.flow_graph import _is_graph_node_chain_event, _preview_value


def test_preview_value_human_message():
    text = _preview_value(HumanMessage(content="你好"))
    assert text == "你好"


def test_preview_value_truncates_long_text():
    text = _preview_value("a" * 1000, max_len=50)
    assert len(text) <= 51
    assert text.endswith("…")


def test_is_graph_node_chain_event_accepts_top_level_node():
    event = {
        "name": "问题修复",
        "tags": [],
        "metadata": {"langgraph_node": "问题修复", "langgraph_checkpoint_ns": "问题修复:1"},
    }
    assert _is_graph_node_chain_event(event) is True


def test_is_graph_node_chain_event_rejects_internal_runnable():
    event = {
        "name": "RunnableSequence",
        "tags": [],
        "metadata": {"langgraph_node": "问题修复"},
    }
    assert _is_graph_node_chain_event(event) is False


def test_is_graph_node_chain_event_rejects_subgraph_internal():
    event = {
        "name": "信息提取",
        "tags": [],
        "metadata": {
            "langgraph_node": "信息提取",
            "langgraph_checkpoint_ns": "产品推荐:1|信息提取:2",
        },
    }
    assert _is_graph_node_chain_event(event) is False
