from sale_app.core.moudel.zhipuai import ZhipuAI


def test_embedding_disables_ctx_length_check_for_compatible_api():
    embed = ZhipuAI().embedding()
    assert embed.check_embedding_ctx_length is False
