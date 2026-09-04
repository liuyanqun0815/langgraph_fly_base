import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from config import recommend_collection_name, recommend_top_k
from sale_app.config.log import Logger
from sale_app.database.session import get_db_session
from sale_app.database.sqlalchemy_models import Product

logger = Logger("fly_base")


@dataclass
class ProductCandidate:
    product_key: str
    product_name: str
    content: str
    source: str
    score: float = 0.0


def _recommend_top_k_value() -> int:
    return recommend_top_k()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()


def _extract_product_name(content: str, metadata: dict | None = None) -> str:
    metadata = metadata or {}
    for key in ("产品名称", "product_name", "name"):
        value = metadata.get(key)
        if value:
            return str(value).strip()
    match = re.search(r"产品名称[：:]\s*(.+)", content or "")
    if match:
        return match.group(1).split("\n")[0].strip()
    first_line = (content or "").strip().split("\n", 1)[0]
    return first_line[:32] if first_line else "unknown"


def _score_sqlite_product(product: Product, user_info: str) -> float:
    if not user_info or "暂无用户信息" in user_info:
        return float(100 - product.product_priority)

    text = f"{product.product_name} {product.product_info}"
    normalized = _normalize_text(text)
    score = float(100 - product.product_priority)
    for token in re.findall(r"[\u4e00-\u9fff]{2,}|\d+", user_info):
        if token and token in normalized:
            score += 10
    return score


def _query_sqlite_topn(user_info: str, top_k: int) -> list[ProductCandidate]:
    with get_db_session() as session:
        products = session.query(Product).all()

    ranked = sorted(
        products,
        key=lambda product: _score_sqlite_product(product, user_info),
        reverse=True,
    )[:top_k]

    candidates = []
    for product in ranked:
        content = f"产品名称：{product.product_name}\n产品信息：{product.product_info}"
        candidates.append(
            ProductCandidate(
                product_key=_normalize_text(product.product_name),
                product_name=product.product_name,
                content=content,
                source="default",
                score=_score_sqlite_product(product, user_info),
            )
        )
    return candidates


def _doc_to_candidate(doc, source: str = "vector") -> ProductCandidate:
    metadata = getattr(doc, "metadata", None) or {}
    page_content = getattr(doc, "page_content", "") or ""
    product_name = _extract_product_name(page_content, metadata if isinstance(metadata, dict) else None)
    score = float(getattr(doc, "score", 0) or 0)
    return ProductCandidate(
        product_key=_normalize_text(product_name),
        product_name=product_name,
        content=page_content,
        source=source,
        score=score,
    )


def _query_vector_topn(user_info: str, top_k: int) -> list[ProductCandidate]:
    from sale_app.core.kb.kb_sevice import KBService
    from sale_app.core.kb.vector.vector_factory import Vector

    collection_name = recommend_collection_name()
    try:
        vector = Vector(collection_name=collection_name)
        if not vector.vector_processor.has_collection(collection_name):
            logger.warning(f"推荐向量集合 {collection_name} 不存在，跳过向量检索")
            return []

        docs = KBService.hybrid_search(user_info, collection_name, top_k=top_k)
        return [_doc_to_candidate(doc) for doc in docs if getattr(doc, "page_content", "")]
    except Exception as exc:
        logger.warning(f"推荐向量检索失败，跳过向量结果: {exc}")
        return []


def _merge_candidates(default_items: list[ProductCandidate], vector_items: list[ProductCandidate]) -> list[ProductCandidate]:
    merged: dict[str, ProductCandidate] = {}
    for item in default_items + vector_items:
        existing = merged.get(item.product_key)
        if existing is None or item.score > existing.score:
            merged[item.product_key] = item
        elif existing.source != item.source:
            merged[item.product_key] = ProductCandidate(
                product_key=item.product_key,
                product_name=item.product_name,
                content=existing.content,
                source="default+vector",
                score=max(existing.score, item.score),
            )
    return sorted(merged.values(), key=lambda candidate: candidate.score, reverse=True)


def _format_candidates(candidates: list[ProductCandidate]) -> str:
    if not candidates:
        return ""
    blocks = []
    for index, candidate in enumerate(candidates, start=1):
        source_label = {"default": "默认库", "vector": "向量库", "default+vector": "默认库+向量库"}.get(
            candidate.source, candidate.source
        )
        blocks.append(
            f"[候选{index} | 来源:{source_label} | 评分:{candidate.score:.1f}]\n{candidate.content}"
        )
    return "\n\n".join(blocks)


def get_product_info(user_info: str) -> str:
    top_k = _recommend_top_k_value()
    logger.info(f"推荐检索开始，用户信息:{user_info}, top_k={top_k}")

    if not user_info or "暂无用户信息" in user_info:
        candidates = _query_sqlite_topn(user_info, top_k)
        return _format_candidates(candidates)

    with ThreadPoolExecutor(max_workers=2) as executor:
        default_future = executor.submit(_query_sqlite_topn, user_info, top_k)
        vector_future = executor.submit(_query_vector_topn, user_info, top_k)
        default_items = default_future.result()
        vector_items = vector_future.result()

    candidates = _merge_candidates(default_items, vector_items)
    if not candidates:
        logger.warning("双路检索均无结果，回退默认库 TopN")
        candidates = _query_sqlite_topn(user_info, top_k)

    product_str = _format_candidates(candidates)
    logger.info(f"推荐检索完成，合并候选数:{len(candidates)}")
    return product_str
