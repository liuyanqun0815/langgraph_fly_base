import sys
from unittest.mock import MagicMock, patch

from sale_app.core.kb.loader.pdf_extractor import PdfExtractor


def _make_page(text):
    text_page = MagicMock()
    text_page.get_text_range.return_value = text
    page = MagicMock()
    page.get_textpage.return_value = text_page
    return page, text_page


def _extract_with_pages(tmp_path, pages, filename="sample.pdf"):
    pdf_path = tmp_path / filename
    pdf_path.write_bytes(b"%PDF-1.4 dummy")

    mock_pdfium = MagicMock()
    mock_reader = MagicMock()
    mock_reader.__iter__.return_value = iter(pages)
    mock_pdfium.PdfDocument.return_value = mock_reader

    with patch.dict(sys.modules, {"pypdfium2": mock_pdfium}):
        extractor = PdfExtractor(str(pdf_path))
        return extractor.extract(), mock_reader


def test_pdf_extractor_skips_blank_and_whitespace_pages(tmp_path):
    blank_page, blank_text_page = _make_page("")
    whitespace_page, whitespace_text_page = _make_page("  \n\t  ")
    text_page, content_text_page = _make_page("贷款额度说明")

    docs, _ = _extract_with_pages(tmp_path, [blank_page, whitespace_page, text_page])

    assert len(docs) == 1
    assert docs[0].page_content == "贷款额度说明"
    assert docs[0].metadata["page"] == 2
    assert docs[0].metadata["file_name"] == "sample"
    blank_page.close.assert_called_once()
    blank_text_page.close.assert_called_once()
    whitespace_page.close.assert_called_once()
    whitespace_text_page.close.assert_called_once()
    text_page.close.assert_called_once()
    content_text_page.close.assert_called_once()


def test_pdf_extractor_skips_none_text(tmp_path):
    none_page, _ = _make_page(None)
    text_page, _ = _make_page("有效内容")

    docs, _ = _extract_with_pages(tmp_path, [none_page, text_page])

    assert len(docs) == 1
    assert docs[0].page_content == "有效内容"
    assert docs[0].metadata["page"] == 1


def test_pdf_extractor_all_blank_returns_empty(tmp_path):
    blank_page, _ = _make_page("")
    whitespace_page, _ = _make_page("\r\n")

    docs, mock_reader = _extract_with_pages(tmp_path, [blank_page, whitespace_page])

    assert docs == []
    mock_reader.close.assert_called_once()
