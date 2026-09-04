"""知识库文档分块：基于 LangChain RecursiveCharacterTextSplitter。"""

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import get_env
from sale_app.config.log import Logger

logger = Logger("fly_base")

# 中文友好分隔符：优先按段落/换行，再按句号等标点切分
CHINESE_SEPARATORS = ["\n\n", "\n", "。", "！", "？", "；", " ", ""]


def _chunk_size() -> int:
    return int(get_env("KB_CHUNK_SIZE") or 800)


def _chunk_overlap() -> int:
    return int(get_env("KB_CHUNK_OVERLAP") or 120)


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=_chunk_size(),
        chunk_overlap=_chunk_overlap(),
        length_function=len,
        separators=CHINESE_SEPARATORS,
        is_separator_regex=False,
    )


def chunk_documents(documents: list[Document]) -> list[Document]:
    """将提取结果切分为适合向量检索的多个 Document。"""
    if not documents:
        return []

    splitter = get_text_splitter()
    chunk_size = _chunk_size()
    chunked: list[Document] = []

    for doc in documents:
        page_content = doc.page_content if isinstance(doc.page_content, str) else str(doc.page_content or "")
        if not page_content.strip():
            continue

        base_metadata = dict(doc.metadata or {})
        if len(page_content) <= chunk_size:
            chunked.append(Document(page_content=page_content, metadata=base_metadata))
            continue

        splits = splitter.split_documents([Document(page_content=page_content, metadata=base_metadata)])
        total = len(splits)
        for idx, split_doc in enumerate(splits):
            split_doc.metadata = {
                **base_metadata,
                "chunk_index": idx,
                "chunk_total": total,
            }
            chunked.append(split_doc)

    logger.info(f"文档分块完成: 输入 {len(documents)} 段, 输出 {len(chunked)} 块")
    return chunked
