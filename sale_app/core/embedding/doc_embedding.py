# import base64
# import logging
# from typing import Optional, cast
#
# import numpy as np
# from langchain_core.embeddings import Embeddings
# from sqlalchemy.exc import IntegrityError
#
# from sale_app.core.moudel.zhipuai import ZhipuAI
#
# logger = logging.getLogger(__name__)
#
#
# class DocEmbedding(Embeddings):
#     def __init__(self) -> None:
#         zhipu = ZhipuAI()
#         self.embedding = zhipu.embedding()
#
#     def embed_documents(self, texts: list[str]) -> list[list[float]]:
#         """Embed search docs in batches of 10."""
#         # use doc embedding cache or store if not exists
#         text_embeddings = [None for _ in range(len(texts))]
#         embedding_queue_indices = []
#         for i, text in enumerate(texts):
#             hash = helper.generate_text_hash(text)
#
#             if embedding:
#                 text_embeddings[i] = embedding.get_embedding()
#
#
#
#         return text_embeddings
#
#     def embed_query(self, text: str) -> list[float]:
#         """Embed query text."""
#         # use doc embedding cache or store if not exists
#         hash = helper.generate_text_hash(text)
#         embedding_cache_key = f'{self._model_instance.provider}_{self._model_instance.model}_{hash}'
#         embedding = redis_client.get(embedding_cache_key)
#         if embedding:
#             redis_client.expire(embedding_cache_key, 600)
#             return list(np.frombuffer(base64.b64decode(embedding), dtype="float"))
#         try:
#             embedding_result = self._model_instance.invoke_text_embedding(
#                 texts=[text],
#                 user=self._user
#             )
#
#             embedding_results = embedding_result.embeddings[0]
#             embedding_results = (embedding_results / np.linalg.norm(embedding_results)).tolist()
#         except Exception as ex:
#             raise ex
#
#         try:
#             # encode embedding to base64
#             embedding_vector = np.array(embedding_results)
#             vector_bytes = embedding_vector.tobytes()
#             # Transform to Base64
#             encoded_vector = base64.b64encode(vector_bytes)
#             # Transform to string
#             encoded_str = encoded_vector.decode("utf-8")
#             redis_client.setex(embedding_cache_key, 600, encoded_str)
#
#         except IntegrityError:
#             db.session.rollback()
#         except:
#             logging.exception('Failed to add embedding to redis')
#
#         return embedding_results
