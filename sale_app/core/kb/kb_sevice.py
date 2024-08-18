import json
import re

from langchain_core.documents import Document

from config import recommend_collection_name
from sale_app.config.log import Logger
from sale_app.core.kb.loader.excel_loader import xlsx_loader
from sale_app.core.kb.vector.vector_factory import Vector

logger = Logger("fly_base")


class KBService:

    def similarity_search(query: str, collection_name: str = 'test_json'):
        vector = Vector(collection_name=collection_name)
        return vector.vector_processor.search_by_vector(query)

    def create_collection(collection_name: str):
        vector = Vector()
        return vector.vector_processor.create_collection(collection_name)

    @classmethod
    def parse_excel(cls, excel_file, collection_name: str = 'test_json'):
        excel_data = xlsx_loader(excel_file)
        docs = [Document(page_content=doc['question'],
                         metadata={'question': doc['question'], 'answer': doc['answer']}) for doc in excel_data]
        vector = Vector(collection_name=collection_name)
        # docs = docs[:1]
        vector.vector_processor.hybrid_add_documents(docs)

    @classmethod
    def text_insert(cls, text: str, collection_name: str = recommend_collection_name()):
        logger.info(f'text_insert:{text},collection_name:{collection_name}')
        # 使用正则表达式提取各个字段
        results = {
            "产品名称": re.search(r"产品名称：(.*?)年龄要求", text).group(1).strip(),
            "年龄要求": re.search(r"年龄要求：(.*?)申请条件", text).group(1).strip(),
            "申请条件": re.search(r"申请条件：(.*?)贷款对象", text).group(1).strip(),
            "贷款对象": re.search(r"贷款对象：(.*?)贷款额度", text).group(1).strip(),
            "贷款额度": re.search(r"贷款额度：(.*?)贷款期限", text).group(1).strip(),
            "贷款期限": re.search(r"贷款期限：(.*?)贷款用途", text).group(1).strip(),
            "贷款用途": re.search(r"贷款用途：(.*?)贷款特色", text).group(1).strip(),
            "贷款特色": re.search(r"贷款特色：(.*)", text).group(1).strip()
        }

        # 使用正则表达式提取每个指标的内容，并整合成字典
        # results = {key: re.search(pattern, text).group(1).strip() for key, pattern in patterns.items()}
        # 将结果转换为JSON格式字符串
        results_json = json.dumps(results, ensure_ascii=False, indent=4)
        # 将JSON字符串转换回字典
        results_dict = json.loads(results_json)
        metadata = text
        # 删除指定的key
        key_to_remove = "产品名称"
        if key_to_remove in results_dict:
            # metadata['product_name'] = results_dict[key_to_remove]
            del results_dict[key_to_remove]
        key_to_remove = "贷款特色"
        if key_to_remove in results_dict:
            # metadata['product_feature'] = results_dict[key_to_remove]
            del results_dict[key_to_remove]

        content = json.dumps(results_dict, ensure_ascii=False, indent=4)

        docs = [Document(page_content=content, metadata=metadata)]
        vector = Vector(collection_name=collection_name)
        # docs = docs[:1]
        vector.vector_processor.hybrid_add_documents(docs)

    @classmethod
    def hybrid_search(cls, query, collection_name: str = 'test_json'):
        vector = Vector(collection_name=collection_name)
        return vector.vector_processor.hybrid_search(query)

    @classmethod
    def keyword_search(cls, query: str, collection_name: str = 'test_json'):
        vector = Vector(collection_name=collection_name)
        return vector.vector_processor.search_by_keyword(query)
