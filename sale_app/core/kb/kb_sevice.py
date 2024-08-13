import json
import re

from langchain_core.documents import Document

from sale_app.core.kb.loader.excel_loader import xlsx_loader
from sale_app.core.kb.vector.vector_factory import Vector


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
    def text_insert(cls, text:str, collection_name: str = 'test_json'):
        # 定义正则表达式来匹配各个指标
        patterns = {
            "产品名称": r"产品名称：(.*?)\n",
            "年龄要求": r"年龄要求：(.*?)\n",
            "申请条件": r"申请条件：(.*?)\n",
            "贷款对象": r"贷款对象：(.*?)\n",
            "贷款额度": r"贷款额度：(.*?)\n",
            "贷款期限": r"贷款期限：(.*?)\n",
            "贷款用途": r"贷款用途：(.*?)\n",
            "产品特色": r"产品特色：(.*?)\n"
        }

        # 使用正则表达式提取每个指标的内容，并整合成字典
        results = {key: re.search(pattern, text).group(1).strip() for key, pattern in patterns.items()}
        # 将结果转换为JSON格式字符串
        results_json = json.dumps(results, ensure_ascii=False, indent=4)
        # 将JSON字符串转换回字典
        results_dict = json.loads(results_json)
        metadata = {}
        # 删除指定的key
        key_to_remove = "产品名称"
        if key_to_remove in results_dict:
            metadata['product_name'] = results_dict[key_to_remove]
            del results_dict[key_to_remove]
        key_to_remove = "产品特色"
        if key_to_remove in results_dict:
            metadata['product_feature'] = results_dict[key_to_remove]
            del results_dict[key_to_remove]

        content = json.dumps(results_dict, ensure_ascii=False, indent=4)

        docs = [Document(page_content=content,metadata=metadata)]
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
