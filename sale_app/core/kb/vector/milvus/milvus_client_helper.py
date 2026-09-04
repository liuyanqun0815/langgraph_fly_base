from pymilvus import MilvusClient

from config import MilvusConfig


def milvus_uri(config: MilvusConfig) -> str:
    return f"http://{config.milvus_host}:{config.milvus_port}"


def build_milvus_client(config: MilvusConfig) -> MilvusClient:
    return MilvusClient(uri=milvus_uri(config))
