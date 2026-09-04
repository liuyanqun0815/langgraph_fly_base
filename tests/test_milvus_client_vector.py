from unittest.mock import MagicMock, patch

from sale_app.core.kb.vector.milvus.milvus_client_helper import milvus_uri
from sale_app.core.kb.vector.milvus.milvus_vector import MilvusVector


def test_milvus_uri():
    config = MagicMock(milvus_host="127.0.0.1", milvus_port=19530)
    assert milvus_uri(config) == "http://127.0.0.1:19530"


@patch("sale_app.core.kb.vector.milvus.milvus_vector.splade_ef")
@patch("sale_app.core.kb.vector.milvus.milvus_vector.ZhipuAI")
@patch("sale_app.core.kb.vector.milvus.milvus_vector.Milvus")
@patch("sale_app.core.kb.vector.milvus.milvus_vector.build_milvus_client")
def test_hybrid_add_documents_uses_milvus_client(mock_build_client, mock_milvus_cls, mock_zhipu, mock_splade):
    mock_client = MagicMock()
    mock_client.has_collection.return_value = True
    mock_build_client.return_value = mock_client

    mock_zhipu.return_value._embedding_dimensions = 1024
    mock_zhipu.return_value.embedding.return_value.embed_documents.return_value = [[0.1, 0.2]]
    mock_splade.embed_documents.return_value = [{1: 0.5}]

    vector = MilvusVector(collection_name="loan_qa", config=MagicMock(), partition_key=None)
    from langchain_core.documents import Document

    vector.hybrid_add_documents([Document(page_content="hello", metadata={"file_name": "a.docx"})])

    mock_client.insert.assert_called_once()
    mock_client.load_collection.assert_called_once_with("loan_qa")
    assert not hasattr(mock_client.insert, "call_args") or mock_client.insert.call_args[0][0] == "loan_qa"
