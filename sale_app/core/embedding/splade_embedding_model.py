from typing import Dict, List
from scipy.sparse import csr_array  # type: ignore

from langchain_milvus.utils.sparse import BaseSparseEmbedding


class SpladeEmbeddingModel(BaseSparseEmbedding):

    def __init__(self):
        from milvus_model.sparse.splade import SpladeEmbeddingFunction
        self.splade_ef = SpladeEmbeddingFunction(
            model_name="naver/splade-cocondenser-selfdistil",
            device="cpu",
            # k_tokens_query=64,
            # k_tokens_document=128
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
