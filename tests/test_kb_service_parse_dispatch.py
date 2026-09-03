import inspect
from unittest.mock import MagicMock, patch

import pytest

from sale_app.core.kb.kb_sevice import KBService


def test_parse_rejects_unknown_suffix():
    try:
        KBService.parse("a.txt", collection_name="t")
        assert False, "should raise"
    except ValueError as e:
        assert "不支持" in str(e)


@pytest.mark.parametrize(
    "method_name",
    ["similarity_search", "hybrid_search", "keyword_search", "xlsx_qa_upload"],
)
def test_search_methods_default_collection_none(method_name):
    sig = inspect.signature(getattr(KBService, method_name))
    assert sig.parameters["collection_name"].default is None


@patch("sale_app.core.kb.kb_sevice.Vector")
@patch("sale_app.core.kb.kb_sevice.get_env", return_value="loan_qa")
def test_similarity_search_uses_default_kb_collection(mock_get_env, mock_vector_cls):
    mock_processor = MagicMock()
    mock_vector_cls.return_value.vector_processor = mock_processor

    KBService.similarity_search("query")

    mock_get_env.assert_called_once_with("DEFAULT_KB_COLLECTION")
    mock_vector_cls.assert_called_once_with(collection_name="loan_qa", partition_key=None)
    mock_processor.search_by_vector.assert_called_once_with("query")
