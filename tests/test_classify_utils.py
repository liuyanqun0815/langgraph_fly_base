from sale_app.core.mutil.classify_utils import (
    fallback_category,
    looks_like_product_qa,
    parse_category_name,
    route_after_recommendation,
    suggest_category_from_state,
)
from sale_app.core.mutil.node_names import NextNode


def test_parse_category_name_from_json():
    content = '{"keywords": ["利率"], "category_name": "产品解答专家"}'
    assert parse_category_name(content) == NextNode.QA


def test_parse_category_name_empty_content():
    assert parse_category_name("") == NextNode.CHAT
    assert parse_category_name("   ", fallback=NextNode.QA) == NextNode.QA


def test_parse_category_name_invalid_json_with_embedded_category():
    content = "分类结果：产品解答专家"
    assert parse_category_name(content, fallback=NextNode.CHAT) == NextNode.QA


def test_suggest_qa_after_recommendation():
    state = {
        "pre_node": "产品推荐",
        "isInfoConfirmed": True,
        "product_list": "安馨贷",
        "question": "这个产品利率多少",
    }
    assert suggest_category_from_state(state) == NextNode.QA


def test_suggest_qa_after_recommendation():
    state = {
        "pre_node": "产品推荐",
        "isInfoConfirmed": True,
        "product_list": "安馨贷",
        "question": "这个产品利率多少",
    }
    assert suggest_category_from_state(state) == NextNode.QA


def test_suggest_conversion_after_recommendation():
    state = {
        "pre_node": "产品推荐",
        "product_list": "安馨贷",
        "awaiting_conversion": True,
        "question": "好的，可以",
    }
    assert suggest_category_from_state(state) == NextNode.CONVERSION


def test_how_to_apply_routes_to_conversion():
    state = {
        "product_list": "安馨贷",
        "awaiting_conversion": True,
        "question": "这个怎么办理",
    }
    assert route_after_recommendation(state, "这个怎么办理") == NextNode.CONVERSION


def test_fallback_category_for_rate_question():
    state = {
        "pre_node": "产品推荐",
        "isInfoConfirmed": True,
        "product_list": "安馨贷",
        "question": "这个产品利率多少",
    }
    assert fallback_category(state) == NextNode.QA


def test_looks_like_product_qa():
    assert looks_like_product_qa("这个产品利率多少")
    assert not looks_like_product_qa("你好")
