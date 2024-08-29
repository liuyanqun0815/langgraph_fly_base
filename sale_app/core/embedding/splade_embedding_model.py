import os
from typing import Dict, List
from scipy.sparse import csr_array  # type: ignore

from langchain_milvus.utils.sparse import BaseSparseEmbedding

from sale_app.config.log import Logger

logger = Logger("fly_base")


class SpladeEmbeddingModel(BaseSparseEmbedding):

    def __init__(self):
        from milvus_model.sparse.splade import SpladeEmbeddingFunction
        # 判断当前环境是window还是linux
        if os.name == 'nt':
            logger.info("当前环境是window")
            home_dir = os.path.expanduser('~')
            cache_dir = os.path.join(home_dir, '.cache', 'huggingface', 'hub',
                                     'models--naver--splade-cocondenser-selfdistil', 'snapshots',
                                     '0f718e09b0540c68c15c5c2b50de731b6e89090a')
            logger.info(f'模型目录为：{cache_dir}')
            # 判断目录是否存在，不存在下载模型
            if not os.path.exists(cache_dir):
                self.splade_ef = SpladeEmbeddingFunction(
                    model_name="naver/splade-cocondenser-selfdistil",
                    device="cpu",
                    k_tokens_query=64,
                    k_tokens_document=128
                )
            else:
                self.splade_ef = SpladeEmbeddingFunction(
                    model_name=cache_dir,
                    device="cpu",
                    k_tokens_query=64,
                    k_tokens_document=128
                )

    def embed_query(self, text: str) -> Dict[int, float]:
        return self._sparse_to_dict(self.splade_ef.encode_queries([text]))

    def embed_documents(self, texts: List[str]) -> List[Dict[int, float]]:
        sparse_arrays = self.splade_ef.encode_documents(texts)
        return [self._sparse_to_dict(sparse_array) for sparse_array in sparse_arrays]

    def _sparse_to_dict(self, sparse_array: csr_array) -> Dict[int, float]:
        row_indices, col_indices = sparse_array.nonzero()
        non_zero_values = sparse_array.data
        result_dict = {}
        for col_index, value in zip(col_indices, non_zero_values):
            result_dict[col_index] = value
        return result_dict
