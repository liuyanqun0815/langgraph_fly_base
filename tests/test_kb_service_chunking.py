from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from sale_app.core.kb.kb_sevice import KBService


@patch("sale_app.core.kb.kb_sevice.Vector")
@patch("sale_app.core.kb.kb_sevice.chunk_documents")
@patch("sale_app.core.kb.kb_sevice.WordExtractor")
@patch("sale_app.core.kb.kb_sevice.get_env", return_value="loan_qa")
def test_parse_chunks_before_insert(mock_get_env, mock_word_cls, mock_chunk, mock_vector_cls):
    raw_docs = [Document(page_content="x" * 5000, metadata={"file_name": "doc.docx"})]
    mock_word_cls.return_value.extract.return_value = raw_docs
    chunked_docs = [Document(page_content=f"chunk-{i}", metadata={"chunk_index": i}) for i in range(3)]
    mock_chunk.return_value = chunked_docs
    mock_processor = MagicMock()
    mock_vector_cls.return_value.vector_processor = mock_processor

    KBService.parse("sample.docx", collection_name="loan_qa")

    mock_chunk.assert_called_once_with(raw_docs)
    mock_processor.hybrid_add_documents.assert_called_once_with(chunked_docs)
