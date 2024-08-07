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
    def hybrid_search(cls, query, collection_name: str = 'test_json'):
        vector = Vector(collection_name=collection_name)
        return vector.vector_processor.hybrid_search(query)

    @classmethod
    def keyword_search(cls, query: str, collection_name: str = 'test_json'):
        vector = Vector(collection_name=collection_name)
        return vector.vector_processor.search_by_keyword(query)
