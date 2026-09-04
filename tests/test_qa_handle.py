from langchain_core.documents import Document

from sale_app.core.agent.qa_handle import format_kb_context


def test_format_kb_context_uses_page_content_not_only_metadata():
    docs = [
        Document(
            page_content="额度范围：10万元-500万元\n年利率：4.5%-8%",
            metadata={"source": "贷款产品合集.docx"},
        )
    ]
    context = format_kb_context(docs)
    assert "10万元-500万元" in context
    assert "4.5%-8%" in context
    assert "贷款产品合集.docx" in context


def test_format_kb_context_skips_empty_page_content():
    docs = [Document(page_content="", metadata={"source": "empty.docx"})]
    assert format_kb_context(docs) == ""
