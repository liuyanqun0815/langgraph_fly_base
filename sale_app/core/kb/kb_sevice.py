from langchain_core.documents import Document

from sale_app.core.kb.loader.excel_loader import xlsx_loader
from sale_app.core.kb.vector.vector_factory import Vector


class KBService:

    def similarity_search(query: str):
        vector = Vector()
        return vector.vector_processor.search_by_vector(query)

    def create_collection(collection_name: str):
        vector = Vector()
        return vector.vector_processor.create_collection(collection_name)

    @classmethod
    def parse_excel(cls, excel_file):
        excel_data = xlsx_loader(excel_file)
        docs = [Document(page_content=doc['question'],
                         metadata={'question': doc['question'], 'answer': doc['answer']}) for doc in excel_data]
        vector = Vector(collection_name='test_json')
        # docs = docs[:1]
        vector.vector_processor.hybrid_add_documents(docs)

    @classmethod
    def hybrid_search(cls, query):
        vector = Vector(collection_name='test_json')
        return vector.vector_processor.hybrid_search(query)


