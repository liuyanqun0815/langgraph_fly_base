import logging
from typing import Any, Optional
from uuid import uuid4

# from langchain_milvus import MilvusCollectionHybridSearchRetriever
from langchain_milvus.retrievers import MilvusCollectionHybridSearchRetriever
from langchain_milvus.utils.sparse import BM25SparseEmbedding
from langchain_milvus.vectorstores import Milvus
from langchain_core.documents import Document
from pymilvus import FieldSchema, DataType, CollectionSchema, Collection, connections, WeightedRanker

from config import MilvusConfig
from sale_app.core.kb.vector.vector_base import BaseVector
from sale_app.core.kb.vector.vector_factory import AbstractVectorFactory
from sale_app.core.kb.vector.vector_type import VectorType
from sale_app.core.moudel.zhipuai import ZhipuAI

logger = logging.getLogger(__name__)
logger.level = logging.DEBUG


class MilvusVector(BaseVector):

    def __init__(self, collection_name: str, config: MilvusConfig):
        super().__init__(collection_name)
        self._config = config
        zhipu = ZhipuAI()
        self._dimension = zhipu._embedding_dimensions
        self._embeddings = zhipu.embedding()
        connections.connect(host=self._config.milvus_host, port=self._config.milvus_port)

        # self.milvus_store = self._init(config)

    def _init(self, config) -> Milvus:
        return Milvus(
            embedding_function=self._embeddings,
            connection_args={
                "port": config.milvus_port,
                "host": config.milvus_host
            },
            index_params={
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            },
            consistency_level="Session",
            collection_name=self._collection_name,
        )

    def get_type(self) -> str:
        return VectorType.MILVUS

    def create_collection(self, collection_name: str):
        self._collection_name = collection_name
        pk_field = "pk"
        dense_field = "dense_vector"
        sparse_field = "sparse_vector"
        question = "question"
        answer = "answer"
        page_content = "page_content"
        metadata = "metadata"
        fields = [
            FieldSchema(
                name=pk_field,
                dtype=DataType.VARCHAR,
                is_primary=True,
                auto_id=True,
                max_length=100,
            ),
            FieldSchema(name=dense_field, dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
            FieldSchema(name=sparse_field, dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name=page_content, dtype=DataType.VARCHAR, max_length=65_535),
            FieldSchema(name=metadata, dtype=DataType.JSON),
            # FieldSchema(name=answer, dtype=DataType.VARCHAR, max_length=65_535),
        ]

        schema = CollectionSchema(fields=fields, enable_dynamic_field=False)

        from pymilvus import utility
        if utility.has_collection(collection_name):
            logger.info("collection already exists")
            return
        collection = Collection(
            name=collection_name, schema=schema, consistency_level="Session"
        )

        dense_index = {"index_type": "FLAT", "metric_type": "IP"}
        collection.create_index("dense_vector", dense_index)
        sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"}
        collection.create_index("sparse_vector", sparse_index)
        collection.flush()

    def add_documents(self, documents: list[Document]):
        self.milvus_store.from_documents(documents, self._embeddings, collection_name=self._collection_name)

    def hybrid_add_documents(self, documents: list[Document]):
        dense_embedding_func = self._embeddings
        sparse_embedding_func = BM25SparseEmbedding(language='zh', corpus=[doc.page_content for doc in documents])
        entities = []
        for doc in documents:
            dense_field = "dense_vector"
            sparse_field = "sparse_vector"
            page_content = 'page_content'
            metadata = 'metadata'
            entity = {
                dense_field: dense_embedding_func.embed_documents([doc.page_content])[0],
                sparse_field: sparse_embedding_func.embed_documents([doc.page_content])[0],
                page_content: doc.page_content,
                metadata: {
                    "question": doc.metadata.get("question"),
                    "answer": doc.metadata.get("answer"),
                },
            }
            entities.append(entity)

        collection = Collection(
            name=self._collection_name, consistency_level="Session"
        )
        collection.insert(entities)
        collection.load()

    def hybrid_search(self, query: str, **kwargs: Any) -> list[Document]:
        dense_embedding_func = self._embeddings
        sparse_embedding_func = BM25SparseEmbedding(language='zh', corpus=[query])
        sparse_search_params = {"metric_type": "IP"}
        dense_search_params = {"metric_type": "IP", "params": {}}
        dense_field = "dense_vector"
        sparse_field = "sparse_vector"
        text_field = "page_content"

        collection = Collection(
            name=self._collection_name, consistency_level="Session"
        )

        retriever = MilvusCollectionHybridSearchRetriever(
            collection=collection,
            rerank=WeightedRanker(0.5, 0.5),
            anns_fields=[dense_field, sparse_field],
            field_embeddings=[dense_embedding_func, sparse_embedding_func],
            field_search_params=[dense_search_params, sparse_search_params],
            top_k=3,
            text_field=text_field,
        )
        results = retriever.invoke(query)

        docs = []
        for result in results:
            doc = Document(page_content=result.page_content,
                           metadata=result.metadata)
            docs.append(doc)
        return docs

    def search_by_vector(self, query: str, **kwargs: Any) -> list[Document]:
        results = self.milvus_store.similarity_search(
            query=query,
            k=2,
        )
        docs = []
        for result in results:
            doc = Document(page_content=result.page_content,
                           metadata=result.metadata)
            docs.append(doc)
        return docs


def search_by_full_text(self, query: str, **kwargs: Any) -> list[Document]:
    # milvus/zilliz doesn't support bm25 search
    return []


# def _init_client(self, config) -> MilvusClient:
#     if config.secure:
#         uri = "https://" + str(config.host) + ":" + str(config.port)
#     else:
#         uri = "http://" + str(config.host) + ":" + str(config.port)
#     client = MilvusClient(uri=uri, user=config.user, password=config.password, db_name=config.database)
#     return client


class MilvusVectorFactory(AbstractVectorFactory):
    def init_vector(self, collection_name: str = None) -> MilvusVector:
        if collection_name is None:
            collection_name = 'milvus'

        return MilvusVector(
            collection_name=collection_name,
            config=MilvusConfig()
        )
