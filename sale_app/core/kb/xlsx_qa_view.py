import os

from langchain_core.documents import Document

from fly_base.settings import KB_FILE_ROOT
from sale_app.config.log import Logger
from sale_app.core.kb.loader.excel_loader import xlsx_loader
from sale_app.core.kb.vector.qdrant_vector import qdrant_client

logger = Logger("fly_base")


def xlsx_qa_upload(f):
    # 如果不存在文件，则创建
    if not os.path.exists(KB_FILE_ROOT):
        os.makedirs(KB_FILE_ROOT)
    file_path = os.path.join(KB_FILE_ROOT, f.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    logger.info(f"文件存储位置:{file_path}")
    file_docs = xlsx_loader(file_path)
    # 写入到向量库
    logger.info(f"文件内容:{file_docs}")
    qdrant = qdrant_client()
    # 将file_docs 转成List[Document]格式
    docs = [Document(page_content=doc['question'],
                     metadata={'question': doc['question'], 'answer': doc['answer']}) for doc in file_docs]
    # qdrant.

    vector = qdrant.add_documents(docs)
    logger.info(f"向量库写入成功")
