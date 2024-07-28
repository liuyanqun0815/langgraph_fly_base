import os

import dotenv

dotenv.load_dotenv()

DEFAULTS = {
    'VECTOR_TYPE': 'milvus',
    'WEAVIATE_URL': 'localhost',
    'WEAVIATE_API_KEY': None,
    'WEAVIATE_COLLECTION_NAME': 'sale_app',
    'WEAVIATE_BATCH_SIZE': 100,
    'MILVUS_HOST': 'localhost',
    'MILVUS_PORT': 19530,
    'MILVUS_PASSWORD': None,
    'MILVUS_DATABASE': 'default',
    'QDRANT_URL': 'localhost',
    'QDRANT_PORT': 6333,
    'QDRANT_API_KEY': None,
    'QDRANT_TYPE': 'memory',
    'QDRANT_DISK_PATH': '/opt/local_qdrant',
    'QDRANT_COLLECTION_NAME': 'sale_app',
    'QDRANT_VECTOR_DIMENSIONS': 1024
}


class QdrantConfig:

    def __init__(self):
        self.type = get_env('QDRANT_TYPE')
        self.url = get_env('QDRANT_URL')
        self.port = get_env('QDRANT_PORT')
        self.api_key = get_env('QDRANT_API_KEY')
        self.qdrant_disk_path = get_env('QDRANT_DISK_PATH')
        self.collection_name = get_env('QDRANT_COLLECTION_NAME')
        self.vector_dimensions = get_env('QDRANT_VECTOR_DIMENSIONS')


class WeaviateConfig:

    def __init__(self):
        self.url = get_env('WEAVIATE_URL')
        self.collection_name = get_env('WEAVIATE_COLLECTION_NAME')
        self.api_key = get_env('WEAVIATE_API_KEY')
        self.batch_size = get_env('WEAVIATE_BATCH_SIZE')


class MilvusConfig:
    def __init__(self):
        self.milvus_host = get_env('MILVUS_HOST')
        self.milvus_port = get_env('MILVUS_PORT')
        self.milvus_password = get_env('MILVUS_PASSWORD')
        self.milvus_databases = get_env('MILVUS_DATABASE')


def get_env(key):
    return os.environ.get(key, DEFAULTS.get(key))
