from typing import Any

from langchain_core.documents import Document


class FlyDocument(Document):
    score: float

    def __init__(self, page_content: str, **kwargs: Any) -> None:
        super().__init__(page_content=page_content, **kwargs)
        self.score = kwargs.get("score", 0)
