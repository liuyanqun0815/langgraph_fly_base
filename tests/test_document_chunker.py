from langchain_core.documents import Document

from sale_app.core.kb.loader.document_chunker import chunk_documents


def test_chunk_documents_short_text_unchanged():
    docs = [Document(page_content="短文本", metadata={"file_name": "a.docx"})]
    result = chunk_documents(docs)
    assert len(result) == 1
    assert result[0].page_content == "短文本"
    assert "chunk_index" not in result[0].metadata


def test_chunk_documents_long_text_splits_with_metadata():
    paragraph = "这是测试段落。" * 200
    docs = [Document(page_content=paragraph, metadata={"file_name": "long.docx", "source": "/tmp/long.docx"})]
    result = chunk_documents(docs)
    assert len(result) > 1
    assert all(doc.metadata["file_name"] == "long.docx" for doc in result)
    assert all(doc.metadata["chunk_total"] == len(result) for doc in result)
    assert [doc.metadata["chunk_index"] for doc in result] == list(range(len(result)))


def test_chunk_documents_skips_empty():
    docs = [
        Document(page_content="   ", metadata={"file_name": "empty.docx"}),
        Document(page_content="有效内容", metadata={"file_name": "ok.docx"}),
    ]
    result = chunk_documents(docs)
    assert len(result) == 1
    assert result[0].page_content == "有效内容"
