import sys
from unittest.mock import MagicMock, patch


def test_startup_shutdown_resets_chain():
    import sale_app.core.mutil.flow_graph as fg

    fg.shutdown_chain()
    assert fg._chain is None

    mock_graph = MagicMock()
    mock_compiled = MagicMock()
    mock_graph.compile.return_value = mock_compiled

    mock_zhipu_mod = MagicMock()
    mock_zhipu_mod.ZhipuAI.return_value.openai_chat.return_value = MagicMock()

    with patch.dict(sys.modules, {"sale_app.core.moudel.zhipuai": mock_zhipu_mod}):
        with patch.object(fg, "build_flow_graph", return_value=mock_graph):
            with patch.object(fg, "_checkpoint_db_path", return_value=":memory:"):
                with patch("langgraph.checkpoint.sqlite.SqliteSaver") as mock_saver_cls:
                    mock_cm = MagicMock()
                    mock_checkpointer = MagicMock()
                    mock_cm.__enter__.return_value = mock_checkpointer
                    mock_saver_cls.from_conn_string.return_value = mock_cm

                    fg.startup_chain()
                    assert fg._chain is mock_compiled
                    mock_graph.compile.assert_called_once_with(checkpointer=mock_checkpointer)

                    fg.shutdown_chain()
                    assert fg._chain is None
                    mock_cm.__exit__.assert_called_once()
