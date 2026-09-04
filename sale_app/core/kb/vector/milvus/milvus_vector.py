from typing import Any, Dict, List, Optional

from langchain_core.documents import Document
from langchain_milvus.vectorstores import Milvus
from pymilvus import (
    AnnSearchRequest,
    CollectionSchema,
    DataType,
    FieldSchema,
    WeightedRanker,
)

from config import MilvusConfig
from sale_app.config.log import Logger
from sale_app.core.embedding.splade_embedding_model import SpladeEmbeddingModel
from sale_app.core.kb.vector.fly_document import FlyDocument
from sale_app.core.kb.vector.milvus.milvus_client_helper import build_milvus_client
from sale_app.core.kb.vector.vector_base import BaseVector
from sale_app.core.kb.vector.vector_factory import AbstractVectorFactory
from sale_app.core.kb.vector.vector_type import VectorType
from sale_app.core.moudel.zhipuai import ZhipuAI

splade_ef = SpladeEmbeddingModel()

logger = Logger("fly_base")


class MilvusVector(BaseVector):
    DENSE_FIELD = "dense_vector"
    SPARSE_FIELD = "sparse_vector"
    PAGE_CONTENT = "page_content"
    PARTITION_KEY = "file_name"
    METADATA = "metadata"

    def __init__(self, collection_name: str, config: MilvusConfig, partition_key: str = None):
        super().__init__(collection_name)
        self._config = config
        self._client = build_milvus_client(config)
        zhipu = ZhipuAI()
        self._dimension = zhipu._embedding_dimensions
        self._embeddings = zhipu.embedding()
        self._partition_key = partition_key
        self.milvus_store = self._init(config)

    def _init(self, config) -> Milvus:
        return Milvus(
            embedding_function=self._embeddings,
            connection_args={
                "port": config.milvus_port,
                "host": config.milvus_host,
            },
            index_params={
                "metric_type": "L2",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024},
            },
            search_params={
                "metric_type": "IP",
                "params": {
                    "nprobe": 64,
                },
            },
            consistency_level="Session",
            collection_name=self._collection_name,
            vector_field=MilvusVector.DENSE_FIELD,
            text_field=MilvusVector.PAGE_CONTENT,
        )

    def get_type(self) -> str:
        return VectorType.MILVUS

    def has_collection(self, collection_name: str) -> bool:
        return self._client.has_collection(collection_name)

    def create_collection(self, collection_name: str):
        self._collection_name = collection_name
        if self._client.has_collection(collection_name):
            logger.info("collection already exists")
            return

        pk_field = "pk"
        fields = [
            FieldSchema(name=pk_field, dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
            FieldSchema(name=MilvusVector.DENSE_FIELD, dtype=DataType.FLOAT_VECTOR, dim=self._dimension),
            FieldSchema(name=MilvusVector.SPARSE_FIELD, dtype=DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema(name=MilvusVector.PAGE_CONTENT, dtype=DataType.VARCHAR, max_length=65_535),
            FieldSchema(name=MilvusVector.PARTITION_KEY, dtype=DataType.VARCHAR, max_length=64),
            FieldSchema(name=MilvusVector.METADATA, dtype=DataType.JSON),
        ]
        schema = CollectionSchema(
            fields=fields,
            enable_dynamic_field=False,
            partition_key_field=MilvusVector.PARTITION_KEY,
        )

        index_params = self._client.prepare_index_params()
        index_params.add_index(
            field_name=MilvusVector.DENSE_FIELD,
            index_type="IVF_FLAT",
            metric_type="IP",
            params={"nlist": 128},
        )
        index_params.add_index(
            field_name=MilvusVector.SPARSE_FIELD,
            index_type="SPARSE_INVERTED_INDEX",
            metric_type="IP",
            params={"nlist": 128, "drop_ratio_build": 0.2},
        )
        index_params.add_index(field_name=MilvusVector.PARTITION_KEY, index_type="Trie")

        self._client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
            consistency_level="Session",
        )
        self._client.flush(collection_name)

    def add_documents(self, documents: list[Document]):
        self.milvus_store.from_documents(documents, self._embeddings, collection_name=self._collection_name)

    def hybrid_add_documents(self, documents: list[Document]):
        dense_embedding_func = self._embeddings
        entities = []
        for doc in documents:
            page_content = doc.page_content if isinstance(doc.page_content, str) else str(doc.page_content or "")
            if not page_content.strip():
                logger.info("跳过空文档片段")
                continue
            entity = {
                MilvusVector.DENSE_FIELD: dense_embedding_func.embed_documents([page_content])[0],
                MilvusVector.SPARSE_FIELD: splade_ef.embed_documents([page_content])[0],
                MilvusVector.PAGE_CONTENT: page_content,
                MilvusVector.PARTITION_KEY: doc.metadata.get("file_name", ""),
                MilvusVector.METADATA: doc.metadata,
            }
            entities.append(entity)

        if not entities:
            logger.warning("无有效文档可入库，跳过插入")
            return

        if not self.has_collection(self._collection_name):
            self.create_collection(self._collection_name)

        self._client.insert(self._collection_name, entities)
        self._client.load_collection(self._collection_name)

    def _partition_filter(self, partition_key: Optional[str]) -> str:
        if partition_key:
            return f"{MilvusVector.PARTITION_KEY} like '%{partition_key}%'"
        return ""

    @staticmethod
    def _hits_to_documents(hits: List[dict]) -> list[FlyDocument]:
        docs = []
        for hit in hits:
            entity = hit.get("entity") or {}
            docs.append(
                FlyDocument(
                    page_content=entity.get(MilvusVector.PAGE_CONTENT, ""),
                    metadata=entity.get(MilvusVector.METADATA, {}),
                    score=hit.get("distance", 0),
                )
            )
        return docs

    def hybrid_search(self, query: str, **kwargs: Any) -> list[FlyDocument]:
        partition_key = kwargs.get("partition_key", self._partition_key)
        top_k = int(kwargs.get("top_k") or 3)
        logger.info(f"混合搜索，请求参数：{query},分区键内容:{partition_key},top_k:{top_k}")
        filter_expr = self._partition_filter(partition_key)

        dense_search_params = {"metric_type": "IP", "params": {}}
        sparse_search_params = {"metric_type": "IP"}
        dense_request = AnnSearchRequest(
            data=[self._embeddings.embed_query(query)],
            anns_field=MilvusVector.DENSE_FIELD,
            param=dense_search_params,
            limit=top_k,
            expr=filter_expr or None,
        )
        sparse_request = AnnSearchRequest(
            data=[splade_ef.embed_query(query)],
            anns_field=MilvusVector.SPARSE_FIELD,
            param=sparse_search_params,
            limit=top_k,
            expr=filter_expr or None,
        )

        self._client.load_collection(self._collection_name)
        results = self._client.hybrid_search(
            collection_name=self._collection_name,
            reqs=[dense_request, sparse_request],
            ranker=WeightedRanker(0.8, 0.2),
            limit=top_k,
            output_fields=[MilvusVector.PAGE_CONTENT, MilvusVector.METADATA],
        )
        docs = self._hits_to_documents(results[0] if results else [])
        logger.info(f"混合搜索，返回内容：{docs}")
        return docs

    def search_by_vector(self, query: str, **kwargs: Any) -> list[FlyDocument]:
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
            doc = FlyDocument(
                page_content=result[0].page_content,
                metadata=result[0].metadata.get("metadata"),
                score=result[1],
            )
            docs.append(doc)
        return docs

    def search_by_keyword(self, query: str, **kwargs: Any) -> list[FlyDocument]:
        partition_key = kwargs.get("partition_key", self._partition_key)
        search_params = {
            "metric_type": "IP",
            "params": {"drop_ratio_search": 0.4},
        }
        embedding = splade_ef.embed_query(query)
        filter_expr = self._partition_filter(partition_key)

        self._client.load_collection(self._collection_name)
        results = self._client.search(
            collection_name=self._collection_name,
            data=[embedding],
            anns_field=MilvusVector.SPARSE_FIELD,
            search_params=search_params,
            limit=3,
            output_fields=[MilvusVector.PAGE_CONTENT, MilvusVector.METADATA],
            filter=filter_expr,
        )

        docs = []
        for hit in results[0] if results else []:
            logger.info(f"hit: {hit}")
            entity = hit.get("entity") or {}
            docs.append(
                FlyDocument(
                    page_content=entity.get(MilvusVector.PAGE_CONTENT, ""),
                    metadata=entity.get(MilvusVector.METADATA, {}),
                    score=hit.get("distance", 0),
                )
            )
        return docs


class MilvusVectorFactory(AbstractVectorFactory):
    def init_vector(self, collection_name: str = None, **kwargs) -> MilvusVector:
        if collection_name is None:
            collection_name = "milvus"

        return MilvusVector(
            collection_name=collection_name,
            config=MilvusConfig(),
            partition_key=kwargs.get("partition_key"),
        )
