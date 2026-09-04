import sys
from unittest.mock import MagicMock

_mock_handle_core = MagicMock()
_mock_handle_core.flow_control = MagicMock(return_value=[])
sys.modules.setdefault("sale_app.core.handle_core", _mock_handle_core)
sys.modules.setdefault("fasttext", MagicMock())

_mock_langchain_zhipu = MagicMock()
_mock_langchain_zhipu.ChatZhipuAI = MagicMock()
_mock_langchain_zhipu.ZhipuAIEmbeddings = MagicMock()
sys.modules.setdefault("langchain_zhipu", _mock_langchain_zhipu)
sys.modules.setdefault("zhipuai", MagicMock())
