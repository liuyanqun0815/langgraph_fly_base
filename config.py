import os

import dotenv

dotenv.load_dotenv()

DEFAULTS = {
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


def get_env(key):
    return os.environ.get(key, DEFAULTS.get(key))
