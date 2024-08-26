from collections.abc import Iterator

from langchain_core.documents import Document
from langchain_core.documents.base import Blob

from sale_app.core.kb.loader.extractor_base import BaseExtractor


class PdfExtractor(BaseExtractor):
    """加载PDF文件。

    该类负责从指定的文件路径加载PDF文件，并能够逐页解析文件内容。

    参数:
        file_path: 要加载的文件的路径。
    """

    def __init__(
            self,
            file_path: str,
    ):
        """使用文件路径初始化PdfExtractor。

        参数:
            file_path: PDF文件的路径。
        """
        self._file_path = file_path

    def extract(self) -> list[Document]:
        """提取PDF文件中的所有文本内容并返回文档列表。

        返回:
            一个Document对象列表，每个对象包含一页的PDF内容。
        """
        documents = list(self.load())
        text_list = []
        for document in documents:
            text_list.append(document.page_content)
        text = "\n\n".join(text_list)
        return documents

    def load(
            self,
    ) -> Iterator[Document]:
        """惰性加载指定路径的PDF文件为页面。

        逐页生成PDF文档的文本内容，以便于处理大文件时不会一次性加载所有内容到内存中。

        返回:
            一个生成器，每个生成的Document对象包含一页的PDF内容。
        """
        blob = Blob.from_path(self._file_path)
        yield from self.parse(blob)

    def parse(self, blob: Blob) -> Iterator[Document]:
        """惰性解析blob对象为多个文档。

        使用pypdfium2库逐页解析PDF内容，同时尽量减少内存占用。

        参数:
            blob: 一个Blob对象，代表要解析的PDF文件。

        返回:
            一个生成器，每个生成的Document对象包含从blob中提取的一页PDF内容。
        """
        import pypdfium2

        with blob.as_bytes_io() as file_path:
            pdf_reader = pypdfium2.PdfDocument(file_path, autoclose=True)
            try:
                for page_number, page in enumerate(pdf_reader):
                    text_page = page.get_textpage()
                    content = text_page.get_text_range()
                    text_page.close()
                    page.close()
                    metadata = {"source": blob.source, "page": page_number}
                    yield Document(page_content=content, metadata=metadata)
            finally:
                pdf_reader.close()
