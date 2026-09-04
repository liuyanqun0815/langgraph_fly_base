from unittest.mock import MagicMock, patch

from sale_app.database.product import (
    ProductCandidate,
    _merge_candidates,
    _query_sqlite_topn,
    get_product_info,
)


def test_merge_candidates_deduplicates_by_product_name():
    default_items = [
        ProductCandidate("永续贷", "永续贷", "default-content", "default", 90.0),
    ]
    vector_items = [
        ProductCandidate("永续贷", "永续贷", "vector-content", "vector", 80.0),
        ProductCandidate("安馨贷", "安馨贷", "other-content", "vector", 70.0),
    ]
    merged = _merge_candidates(default_items, vector_items)
    keys = {item.product_key for item in merged}
    assert keys == {"永续贷", "安馨贷"}
    assert merged[0].product_name == "永续贷"


@patch("sale_app.database.product.get_db_session")
def test_query_sqlite_topn_respects_limit(mock_session):
    product_a = MagicMock(product_name="A", product_info="info-a", product_priority=1)
    product_b = MagicMock(product_name="B", product_info="info-b", product_priority=2)
    product_c = MagicMock(product_name="C", product_info="info-c", product_priority=3)
    mock_session.return_value.__enter__.return_value.query.return_value.all.return_value = [
        product_c,
        product_b,
        product_a,
    ]

    items = _query_sqlite_topn("年龄35岁", 2)
    assert len(items) == 2


@patch("sale_app.database.product._query_vector_topn", return_value=[])
@patch("sale_app.database.product._query_sqlite_topn")
def test_get_product_info_parallel_merge(mock_sqlite, mock_vector):
    mock_sqlite.return_value = [
        ProductCandidate("a", "产品A", "content-a", "default", 90.0),
    ]
    result = get_product_info("年龄35岁，想申请经营贷")
    assert "content-a" in result
    assert "来源:默认库" in result
    mock_sqlite.assert_called_once()
    mock_vector.assert_called_once()


@patch("sale_app.database.product._query_sqlite_topn")
def test_get_product_info_no_user_info_only_default(mock_sqlite):
    mock_sqlite.return_value = [ProductCandidate("a", "产品A", "content-a", "default", 90.0)]
    result = get_product_info("暂无用户信息")
    assert "content-a" in result
    mock_sqlite.assert_called_once()
