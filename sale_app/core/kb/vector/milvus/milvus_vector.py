import logging
from typing import Any, Optional, Dict

from langchain_milvus.retrievers import MilvusCollectionHybridSearchRetriever
from langchain_milvus.vectorstores import Milvus
from langchain_core.documents import Document
from pymilvus import FieldSchema, DataType, CollectionSchema, Collection, connections, WeightedRanker
from scipy.sparse import csr_array  # type: ignore

from config import MilvusConfig
from sale_app.core.embedding.splade_embedding_model import SpladeEmbeddingModel
from sale_app.core.kb.vector.vector_base import BaseVector
from sale_app.core.kb.vector.vector_factory import AbstractVectorFactory
from sale_app.core.kb.vector.vector_type import VectorType
from sale_app.core.moudel.zhipuai import ZhipuAI
from sale_app.config.log import Logger

splade_ef = SpladeEmbeddingModel()

logger = Logger("fly_base")



class MilvusVector(BaseVector):

    def __init__(self, collection_name: str, config: MilvusConfig):
        super().__init__(collection_name)
        self._config = config
        zhipu = ZhipuAI()
        self._dimension = zhipu._embedding_dimensions
        self._embeddings = zhipu.embedding()
        connections.connect(host=self._config.milvus_host, port=self._config.milvus_port)

        self.milvus_store = self._init(config)

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
            vector_field="dense_vector",
            text_field="page_content",

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

        dense_index = {"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 128}}
        collection.create_index("dense_vector", dense_index)
        sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP", "params": {"nlist": 128}}
        collection.create_index("sparse_vector", sparse_index)
        collection.flush()

    def add_documents(self, documents: list[Document]):
        self.milvus_store.from_documents(documents, self._embeddings, collection_name=self._collection_name)

    def _sparse_to_dict(self, sparse_array: csr_array) -> Dict[int, float]:
        row_indices, col_indices = sparse_array.nonzero()
        non_zero_values = sparse_array.data
        result_dict = {}
        for col_index, value in zip(col_indices, non_zero_values):
            result_dict[col_index] = value
        return result_dict

    def hybrid_add_documents(self, documents: list[Document]):
        dense_embedding_func = self._embeddings
        # sparse_embedding_func = BM25SparseEmbedding(language='zh', corpus=[doc.page_content for doc in documents])
        entities = []
        for doc in documents:
            dense_field = "dense_vector"
            sparse_field = "sparse_vector"
            page_content = 'page_content'
            metadata = 'metadata'
            entity = {
                dense_field: dense_embedding_func.embed_documents([doc.page_content])[0],
                sparse_field: splade_ef.embed_documents([doc.page_content])[0],
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
        # sparse_embedding_func = BM25SparseEmbedding(language='zh', corpus=[query])
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
            field_embeddings=[dense_embedding_func, splade_ef],
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
        logger.info(f"语义检索，请求内容：{query}")
        results = self.milvus_store.similarity_search_with_score(
            query=query,
            k=2,
        )
        docs = []
        for result in results:
            doc = Document(page_content=result[0].page_content,
                           metadata=result[0].metadata.get("metadata"))
            docs.append(doc)
        return docs

    def search_by_keyword(self, query: str, **kwargs: Any) -> list[Document]:

        collection = Collection(
            name=self._collection_name, consistency_level="Session"
        )

        # 执行搜索，设置搜索参数，如查询的向量数（nprobe）、搜索的向量数（limit）等
        search_params = {
            "metric_type": "IP",  # 使用 L2 距离作为相似度度量
            "params": {"drop_ratio_search": 0.4},  # 查询向量中要忽略的最小值的比例。
            "limit": 4,
        }
        embedding = splade_ef.embed_query(query)
        # 稀疏向量检索
        results = collection.search(
            data=[embedding],  # 查询向量
            anns_field="sparse_vector",  # 稀疏向量字段名
            param=search_params,  # 搜索参数
            limit=3,  # 返回的向量个数
            output_fields=["page_content", "metadata"]  # 返回的字段列表
        )
        docs = []
        for result in results:
            for hit in result:
                print(f"hit: {hit}")
                doc = Document(page_content=hit.fields['page_content'],
                               metadata=hit.fields['metadata'])
                docs.append(doc)
        return docs


class MilvusVectorFactory(AbstractVectorFactory):
    def init_vector(self, collection_name: str = None) -> MilvusVector:
        if collection_name is None:
            collection_name = 'milvus'

        return MilvusVector(
            collection_name=collection_name,
            config=MilvusConfig()
        )
