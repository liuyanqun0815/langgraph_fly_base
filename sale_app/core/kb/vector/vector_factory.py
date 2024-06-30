from abc import ABC, abstractmethod

from langchain_core.embeddings import Embeddings

from config import WeaviateConfig
from sale_app.core.kb.vector.vector_base import BaseVector
from sale_app.core.kb.vector.vector_type import VectorType
from sale_app.models import Datasets


class AbstractVectorFactory(ABC):
    @abstractmethod
    def init_vector(self, dataset: Datasets, attributes: list, embeddings: Embeddings) -> BaseVector:
        raise NotImplementedError

    @staticmethod
    def gen_index_struct_dict(vector_type: VectorType, collection_name: str) -> dict:
        index_struct_dict = {
            "type": vector_type,
            "vector_store": {"class_prefix": collection_name}
        }
        return index_struct_dict


class VectorFactory:

    def __init__(self, vector_type: str = None,embeddings: Embeddings = None, collection_name: str = None):
        #如果vector_type 为 weaviate 则创建weaviate_client

        if vector_type == "weaviate":
            weaviateConfig=WeaviateConfig()
            import weaviate
            # auth_client_secret = (weaviate.AuthApiKey(api_key=os.getenv("WEAVIATE_API_KEY")),)
            client = weaviate.Client(
                url=weaviateConfig.url,
                # additional_headers={
                #     "X-Openai-Api-Key": os.getenv("OPENAI_API_KEY"),
                # },
            )
        # elif vector_type == "qdrant":



