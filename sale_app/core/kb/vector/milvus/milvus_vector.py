import logging
from typing import Any, Optional, Dict

from langchain_milvus.retrievers import MilvusCollectionHybridSearchRetriever
from langchain_milvus.vectorstores import Milvus
from langchain_core.documents import Document
from pymilvus import FieldSchema, DataType, CollectionSchema, Collection, connections, WeightedRanker
from pymilvus.orm import utility
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
    DENSE_FIELD = "dense_vector"
    SPARSE_FIELD = "sparse_vector"
    PAGE_CONTENT = "page_content"
    PARTITION_KEY = "file_name"
    METADATA = "metadata"

    def __init__(self, collection_name: str, config: MilvusConfig, partition_key: str = None, ):
        super().__init__(collection_name)
        self._config = config
        zhipu = ZhipuAI()
        self._dimension = zhipu._embedding_dimensions
        self._embeddings = zhipu.embedding()
        connections.connect(host=self._config.milvus_host, port=self._config.milvus_port)
        self._partition_key = partition_key
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
            search_params={
                "metric_type": "IP",
                "params": {
                    "nprobe": 64
                }
            },
            consistency_level="Session",
            collection_name=self._collection_name,
            vector_field=MilvusVector.DENSE_FIELD,
            text_field=MilvusVector.PAGE_CONTENT,

        )

    def get_type(self) -> str:
        return VectorType.MILVUS

    def has_collection(self, collection_name: str):
        return utility.has_collection(collection_name)

    def create_collection(self, collection_name: str):
        self._collection_name = collection_name
        pk_field = "pk"
        fields = [
            FieldSchema(name=pk_field, dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100, ),
            FieldSchema(name=MilvusVector.DENSE_FIELD, dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
            FieldSchema(name=MilvusVector.SPARSE_FIELD, dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name=MilvusVector.PAGE_CONTENT, dtype=DataType.VARCHAR, max_length=65_535),
            FieldSchema(name=MilvusVector.PARTITION_KEY, dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name=MilvusVector.METADATA, dtype=DataType.JSON),
        ]

        schema = CollectionSchema(fields=fields, enable_dynamic_field=False,
                                  partition_key_field=MilvusVector.PARTITION_KEY)

        from pymilvus import utility
        if utility.has_collection(collection_name):
            logger.info("collection already exists")
            return
        collection = Collection(
            name=collection_name, schema=schema, consistency_level="Session"
        )

        dense_index = {"index_type": "IVF_FLAT", "metric_type": "IP", "params": {"nlist": 128}}
        collection.create_index(MilvusVector.DENSE_FIELD, dense_index)
        # 在索引过程中要删除的小向量值的比例。
        sparse_index = {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP",
                        "params": {"nlist": 128, "drop_ratio_build": 0.2}}
        collection.create_index(MilvusVector.SPARSE_FIELD, sparse_index)

        collection.create_index(MilvusVector.PARTITION_KEY, {"index_type": "Trie"})
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
            entity = {
                MilvusVector.DENSE_FIELD: dense_embedding_func.embed_documents([doc.page_content])[0],
                MilvusVector.SPARSE_FIELD: splade_ef.embed_documents([doc.page_content])[0],
                MilvusVector.PAGE_CONTENT: doc.page_content,
                MilvusVector.PARTITION_KEY: doc.metadata.get("file_name", ""),
                MilvusVector.METADATA: doc.metadata,
            }
            entities.append(entity)

        if self.has_collection(self._collection_name) is False:
            self.create_collection(self._collection_name)

        collection = Collection(
            name=self._collection_name, consistency_level="Session"
        )
        collection.insert(entities)
        collection.load()

    def hybrid_search(self, query: str, **kwargs: Any) -> list[Document]:
        partition_key = kwargs.get("partition_key", self._partition_key)
        logger.info(f"混合搜索，请求参数：{query},分区键内容:{partition_key}")
        dense_embedding_func = self._embeddings
        sparse_search_params = {"metric_type": "IP"}
        dense_search_params = {"metric_type": "IP", "params": {}}
        dense_field = "dense_vector"
        sparse_field = "sparse_vector"
        text_field = "page_content"

        collection = Collection(
            name=self._collection_name, consistency_level="Session"
        )
        if partition_key is None or partition_key == "":
            retriever = MilvusCollectionHybridSearchRetriever(
                collection=collection,
                rerank=WeightedRanker(0.8, 0.2),
                anns_fields=[MilvusVector.DENSE_FIELD, MilvusVector.SPARSE_FIELD],
                field_embeddings=[dense_embedding_func, splade_ef],
                field_search_params=[dense_search_params, sparse_search_params],
                top_k=3,
                text_field=text_field,
            )
        else:
            retriever = MilvusCollectionHybridSearchRetriever(
                collection=collection,
                rerank=WeightedRanker(0.8, 0.2),
                anns_fields=[dense_field, sparse_field],
                field_embeddings=[dense_embedding_func, splade_ef],
                field_search_params=[dense_search_params, sparse_search_params],
                top_k=3,
                text_field=text_field,
                field_exprs=[f"{MilvusVector.PARTITION_KEY} like '%{partition_key}%'"] * 2
            )
        results = retriever.invoke(query)
        logger.info(f"混合搜索，返回内容：{results}")
        docs = []
        for result in results:
            doc = Document(page_content=result.page_content,
                           metadata=result.metadata)
            docs.append(doc)
        return docs

    def search_by_vector(self, query: str, **kwargs: Any) -> list[Document]:
        partition_key = kwargs.get("partition_key", self._partition_key)
        logger.info(f"语义检索，请求内容：{query},分区键:{partition_key}")
        if partition_key is None or partition_key == "":
            logger.info("未指定分区键，不使用分区键过滤")
            results = self.milvus_store.similarity_search_with_score(
                query=query,
                k=2,
            )
        else:
            results = self.milvus_store.similarity_search_with_score(
                query=query,
                k=2,
                expr=f"{MilvusVector.PARTITION_KEY} like '%{partition_key}%'",
                search_params={"metric_type": "L2", "params": {"nprobe": 10}},
            )
        docs = []
        logger.info(f"语义检索检索结果：{results}")
        for result in results:
            doc = Document(page_content=result[0].page_content,
                           metadata=result[0].metadata.get("metadata"))
            docs.append(doc)
        return docs

    def search_by_keyword(self, query: str, **kwargs: Any) -> list[Document]:
        partition_key = kwargs.get("partition_key", self._partition_key)

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
        if partition_key is None or partition_key == "":
            results = collection.search(
                data=[embedding],  # 查询向量
                anns_field="sparse_vector",  # 稀疏向量字段名
                param=search_params,  # 搜索参数
                limit=3,  # 返回的向量个数
                output_fields=["page_content", "metadata"]  # 返回的字段列表
            )
        else:
            results = collection.search(
                data=[embedding],  # 查询向量
                anns_field="sparse_vector",  # 稀疏向量字段名
                param=search_params,  # 搜索参数
                limit=3,  # 返回的向量个数
                output_fields=["page_content", "metadata"] , # 返回的字段列表
                expr=f"{MilvusVector.PARTITION_KEY} like '%{partition_key}%'"
            )
        docs = []
        for result in results:
            for hit in result:
                logger.info(f"hit: {hit}")
                doc = Document(page_content=hit.fields['page_content'],
                               metadata=hit.fields['metadata'])
                docs.append(doc)
        return docs


class MilvusVectorFactory(AbstractVectorFactory):
    def init_vector(self, collection_name: str = None, **kwargs) -> MilvusVector:
        if collection_name is None:
            collection_name = 'milvus'

        return MilvusVector(
            collection_name=collection_name,
            config=MilvusConfig(),
            partition_key=kwargs.get("partition_key")
        )
