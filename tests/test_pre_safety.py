import sys
from unittest.mock import MagicMock, patch

sys.modules.setdefault("sale_app.core.moudel.zhipuai", MagicMock())
sys.modules.pop("sale_app.secrity.pre_safety", None)

from sale_app.secrity import pre_safety


def test_safe_reject_message_returns_none():
    assert pre_safety._safe_reject_message(RuntimeError("x")) is None


def test_pre_handle_returns_none_on_generic_error():
    mock_chain = MagicMock()
    mock_chain.invoke.side_effect = RuntimeError("boom")
    with patch.object(pre_safety, "ZhipuAI") as mock_zhipu:
        mock_llm = MagicMock()
        mock_zhipu.return_value.openai_chat.return_value = mock_llm
        mock_llm.with_structured_output.return_value = MagicMock()
        with patch.object(pre_safety, "tagging_prompt") as mock_prompt:
            mock_prompt.__or__ = MagicMock(return_value=mock_chain)
            result = pre_safety.pre_handle("你好")
    assert result is None
