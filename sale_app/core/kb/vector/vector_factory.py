from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings

from config import  get_env

from sale_app.core.kb.vector.vector_base import BaseVector
from sale_app.core.kb.vector.vector_type import VectorType
from sale_app.core.moudel.zhipuai import ZhipuAI


class AbstractVectorFactory(ABC):
    @abstractmethod
    def init_vector(self, collection_name: str = None) -> BaseVector:
        raise NotImplementedError



class Vector:
    def __init__(self, collection_name: str = None):
        self._collection_name = collection_name
        self.vector_processor = self._init_vector()

    def _init_vector(self) -> BaseVector:
        vector_type = get_env('VECTOR_TYPE')

        if not vector_type:
            raise ValueError("向量存储类型未设置.")

        vector_factory_cls = self.get_vector_factory(vector_type)
        return vector_factory_cls().init_vector(self._collection_name)

    @staticmethod
    def get_vector_factory(vector_type: str) -> type[AbstractVectorFactory]:
        match vector_type:
            case VectorType.MILVUS:
                from sale_app.core.kb.vector.milvus.milvus_vector import MilvusVectorFactory
                return MilvusVectorFactory
            # case VectorType.QDRANT:
            #     return QdrantVectorFactory
            # case VectorType.WEAVIATE:
            #     return WeaviateVectorFactory
            case _:
                raise ValueError(f"不支持的向量存储类型: {vector_type} ")

