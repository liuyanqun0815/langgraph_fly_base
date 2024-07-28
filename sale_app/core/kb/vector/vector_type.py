from enum import Enum


class VectorType(str, Enum):
    QDRANT = 'qdrant'
    WEAVIATE = 'weaviate'
    MILVUS = 'milvus'
