import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch


def test_startup_shutdown_resets_chain():
    import sale_app.core.mutil.flow_graph as fg

    asyncio.run(fg.shutdown_chain())
    assert fg._chain is None

    mock_graph = MagicMock()
    mock_compiled = MagicMock()
    mock_graph.compile.return_value = mock_compiled

    mock_zhipu_mod = MagicMock()
    mock_zhipu_mod.ZhipuAI.return_value.openai_chat.return_value = MagicMock()

    async def _run_lifecycle():
        with patch.dict(sys.modules, {"sale_app.core.moudel.zhipuai": mock_zhipu_mod}):
            with patch.object(fg, "build_flow_graph", return_value=mock_graph):
                with patch.object(fg, "_checkpoint_db_path", return_value=":memory:"):
                    with patch("langgraph.checkpoint.sqlite.aio.AsyncSqliteSaver") as mock_saver_cls:
                        mock_cm = MagicMock()
                        mock_checkpointer = MagicMock()
                        mock_cm.__aenter__ = AsyncMock(return_value=mock_checkpointer)
                        mock_cm.__aexit__ = AsyncMock(return_value=None)
                        mock_saver_cls.from_conn_string.return_value = mock_cm

                        await fg.startup_chain()
                        assert fg._chain is mock_compiled
                        mock_graph.compile.assert_called_once_with(checkpointer=mock_checkpointer)

                        await fg.shutdown_chain()
                        assert fg._chain is None
                        mock_cm.__aexit__.assert_awaited_once()

    asyncio.run(_run_lifecycle())
