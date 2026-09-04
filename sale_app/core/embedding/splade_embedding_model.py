import os
from typing import Any, Dict, List

from langchain_milvus.utils.sparse import BaseSparseEmbedding
from scipy.sparse import csr_array  # type: ignore

from sale_app.config.log import Logger

logger = Logger("fly_base")


def _patch_transformers_compat(splade_ef: Any) -> None:
    """milvus_model 仍调用 batch_encode_plus，transformers>=5 已移除该 API。"""
    tokenizer = splade_ef.model.tokenizer
    if hasattr(tokenizer, "batch_encode_plus"):
        return

    def batch_encode_plus(texts: List[str], **kwargs: Any) -> Dict[str, Any]:
        return tokenizer(texts, **kwargs)

    tokenizer.batch_encode_plus = batch_encode_plus


class SpladeEmbeddingModel(BaseSparseEmbedding):

    def __init__(self):
        from milvus_model.sparse.splade import SpladeEmbeddingFunction

        if os.name == "nt":
            logger.info("当前环境是window")
            home_dir = os.path.expanduser("~")
            cache_dir = os.path.join(
                home_dir,
                ".cache",
                "huggingface",
                "hub",
                "models--naver--splade-cocondenser-selfdistil",
                "snapshots",
                "0f718e09b0540c68c15c5c2b50de731b6e89090a",
            )
            logger.info(f"模型目录为：{cache_dir}")
            model_name = cache_dir if os.path.exists(cache_dir) else "naver/splade-cocondenser-selfdistil"
        else:
            model_name = "naver/splade-cocondenser-selfdistil"

        self.splade_ef = SpladeEmbeddingFunction(
            model_name=model_name,
            device="cpu",
            k_tokens_query=64,
            k_tokens_document=128,
        )
        _patch_transformers_compat(self.splade_ef)

    def embed_query(self, text: str) -> Dict[int, float]:
        return self._sparse_to_dict(self.splade_ef.encode_queries([text]))

    def embed_documents(self, texts: List[str]) -> List[Dict[int, float]]:
        sparse_arrays = self.splade_ef.encode_documents(texts)
        return [self._sparse_to_dict(sparse_array) for sparse_array in sparse_arrays]

    def _sparse_to_dict(self, sparse_array: csr_array) -> Dict[int, float]:
        coo = sparse_array.tocoo()
        return {int(col_index): float(value) for col_index, value in zip(coo.col, coo.data)}
