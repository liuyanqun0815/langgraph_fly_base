from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore
from qdrant_client.models import VectorParams, Distance

from config import QdrantConfig
from qdrant_client import QdrantClient
from langchain_qdrant import Qdrant

from sale_app.config.log import Logger
from sale_app.core.moudel.zhipuai import ZhipuAI

logger = Logger("fly_base")


def qdrant_client(embeddings: Embeddings = None, collection_name: str = None) -> VectorStore:
    qdrant_config = QdrantConfig()
    client = _client()
    collection_name = collection_name or qdrant_config.collection_name
    # 判断索引是否存在，不存在创建索引
    if client.collection_exists(collection_name) is False:
        create_collection(collection_name)
    zhipuEmbeddings = ZhipuAI()
    embeddings = embeddings or zhipuEmbeddings.embedding()
    return Qdrant(client, collection_name, embeddings)


def _client():
    qdrant_config = QdrantConfig()
    location = qdrant_config.type
    logger.info(f"qdrant_config: {qdrant_config}")
    if location not in ["local", "remote", ":memory:"]:
        logger.error(f"存储类型至少是local, remote, :memory:中的一种。")
        raise ValueError(
            "存储类型至少是local, remote, :memory:中的一种。"
        )
    if location == "local" and not qdrant_config.qdrant_disk_path:
        logger.error(f"本地存储类型需要设置qdrant_disk_path")
        raise ValueError(
            "本地存储类型需要设置qdrant_disk_path"
        )
    if location == "remote" and not qdrant_config.url and not qdrant_config.port:
        logger.error(f"远程存储类型需要设置url和port")
        raise ValueError(
            "远程存储类型需要设置url和port"
        )
    location_value = ":memory:" if location == ":memory:" else None
    disk_path = qdrant_config.qdrant_disk_path if location == "local" else None
    url = qdrant_config.url if location == "remote" else None
    return QdrantClient(
        location=location_value,
        url=url,
        port=qdrant_config.port,
        # api_key=qdrant_config.api_key,
        # prefer_grpc=True,
        path=disk_path,
        timeout=15
    )


def create_collection(collection_name: str = None):
    qdrant_config = QdrantConfig()

    if not collection_name:
        logger.error(f"集合名称不能为空")
        raise ValueError(
            "集合名称不能为空"
        )
    client = _client()
    # 创建集合，维度暂时固定1024，后面在通过传参遍历设置
    vectors_config = VectorParams(
                        size=qdrant_config.vector_dimensions,
                        distance=Distance.COSINE,
                    )
    client.create_collection(
        collection_name=collection_name,
        vectors_config=vectors_config,
    )
    logger.info(f"创建集合{collection_name}成功")
