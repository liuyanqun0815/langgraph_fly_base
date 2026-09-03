from sale_app.core.kb.kb_sevice import KBService


def test_parse_rejects_unknown_suffix():
    try:
        KBService.parse("a.txt", collection_name="t")
        assert False, "should raise"
    except ValueError as e:
        assert "不支持" in str(e)
