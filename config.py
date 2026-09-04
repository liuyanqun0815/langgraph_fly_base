import os
from pathlib import Path

import dotenv

BASE_DIR = Path(__file__).resolve().parent


def _is_truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def configure_langsmith() -> None:
    """关闭 LangSmith 时清除 tracing 相关环境变量，避免仍向 api.smith.langchain.com 上报。"""
    dotenv.load_dotenv(override=True)
    tracing_on = _is_truthy(os.environ.get("LANGCHAIN_TRACING_V2")) or _is_truthy(
        os.environ.get("LANGSMITH_TRACING")
    )
    if tracing_on:
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGSMITH_TRACING"] = "false"
    for key in ("LANGCHAIN_API_KEY", "LANGSMITH_API_KEY", "LANGCHAIN_ENDPOINT"):
        os.environ.pop(key, None)


configure_langsmith()
DEFAULTS = {
    'VECTOR_TYPE': 'milvus',
    'MILVUS_HOST': 'localhost',
    'MILVUS_PORT': 19530,
    'MILVUS_PASSWORD': None,
    'MILVUS_DATABASE': 'default',
    # 推荐集合默认配置
    'RECOMMEND_COLLECTION_NAME': 'recommend_product',
    'RECOMMEND_TOP_K': 5,
    'DEFAULT_KB_COLLECTION': 'loan_qa',

    'SERVICE_API_URL': 'http://127.0.0.1:8000',
    'APP_SECRET_KEY': 'dev-only-change-me',
    'DATABASE_URL': 'sqlite:///./db.sqlite3',
    'MEDIA_ROOT': str(BASE_DIR / 'storage'),
    'KB_FILE_ROOT': str(BASE_DIR / 'storage' / 'kb_file'),
    'IMAGE_DIR': str(BASE_DIR / 'storage' / 'image_file'),
    # LLM（DashScope OpenAI 兼容模式）
    'LLM_API_BASE': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    'LLM_MODEL': 'qwen-plus',
    'LLM_TEMPERATURE': '0.1',
    # 是否开启模型推理/思考（DashScope: enable_thinking；默认关闭以提速）
    'LLM_ENABLE_REASONING': 'false',
    # 问题分类：few-shot 示例条数（0=关闭，1~2=保留示例；越少越快）
    'QUESTION_CLASS_FEW_SHOT': '1',
    # 问题分类：带入的历史对话轮数（仅最近 N 轮用户/助手消息）
    'QUESTION_CLASS_HISTORY_TURNS': '4',
    'EMBEDDING_MODEL': 'text-embedding-v3',
    'EMBEDDING_DIMENSIONS': 1024,
    # 知识库文档分块（字符数）
    'KB_CHUNK_SIZE': 800,
    'KB_CHUNK_OVERLAP': 120,
    # 客户转化 / 客服联系方式
    'CUSTOMER_SERVICE_PHONE': '400-888-0000',
    'CUSTOMER_SERVICE_HOURS': '工作日 9:00-18:00',
    'OFFLINE_BRANCH_HINT': '请携带身份证及相关材料前往就近网点办理，或通过人工客服预约客户经理上门服务',
}


class MilvusConfig:
    def __init__(self):
        self.milvus_host = get_env('MILVUS_HOST')
        self.milvus_port = get_env('MILVUS_PORT')
        self.milvus_password = get_env('MILVUS_PASSWORD')
        self.milvus_databases = get_env('MILVUS_DATABASE')


def get_env(key):
    return os.environ.get(key, DEFAULTS.get(key))


def recommend_collection_name():
    return get_env('RECOMMEND_COLLECTION_NAME')


def recommend_top_k() -> int:
    return int(get_env('RECOMMEND_TOP_K') or 5)


def app_secret_key():
    return get_env('APP_SECRET_KEY') or get_env('DJANGO_SECRET_KEY')


def media_root():
    return get_env('MEDIA_ROOT')


def kb_file_root():
    return get_env('KB_FILE_ROOT')


def image_dir():
    return get_env('IMAGE_DIR')


def customer_service_phone():
    return get_env('CUSTOMER_SERVICE_PHONE')


def customer_service_hours():
    return get_env('CUSTOMER_SERVICE_HOURS')


def offline_branch_hint():
    return get_env('OFFLINE_BRANCH_HINT')


def llm_enable_reasoning() -> bool:
    return _is_truthy(get_env('LLM_ENABLE_REASONING'))


def question_class_few_shot_count() -> int:
    try:
        return max(0, min(2, int(get_env('QUESTION_CLASS_FEW_SHOT') or 1)))
    except (TypeError, ValueError):
        return 1


def question_class_history_turns() -> int:
    try:
        return max(0, int(get_env('QUESTION_CLASS_HISTORY_TURNS') or 4))
    except (TypeError, ValueError):
        return 4
