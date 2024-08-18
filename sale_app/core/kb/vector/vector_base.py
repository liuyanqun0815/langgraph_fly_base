from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings


class BaseVector(ABC):

    def __init__(self, collection_name: str):
        self._collection_name = collection_name

    @abstractmethod
    def get_type(self) -> str:
        raise NotImplementedError

    def create_collection(self,collection_name:str):
        raise NotImplementedError

    @abstractmethod
    def has_collection(self, collection_name: str):
        raise NotImplementedError


    @abstractmethod
    def add_documents(self, documents: list[Document]):
        raise NotImplementedError

    @abstractmethod
    def hybrid_add_documents(self, documents: list[Document]):
        raise NotImplementedError



    @abstractmethod
    def hybrid_search(self, query: str, **kwargs: Any) -> list[Document]:
        raise NotImplementedError


    @abstractmethod
    def search_by_vector(
            self,
            query: str,
            **kwargs: Any
    ) -> list[Document]:
        raise NotImplementedError

    @abstractmethod
    def search_by_keyword(
            self, query: str,
            **kwargs: Any
    ) -> list[Document]:
        raise NotImplementedError


    def _filter_duplicate_texts(self, texts: list[Document]) -> list[Document]:
        for text in texts:
            doc_id = text.metadata['doc_id']
            exists_duplicate_node = self.text_exists(doc_id)
            if exists_duplicate_node:
                texts.remove(text)

        return texts

    def _get_uuids(self, texts: list[Document]) -> list[str]:
        return [text.metadata['doc_id'] for text in texts]
