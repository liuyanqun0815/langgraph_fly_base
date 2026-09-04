def test_fixed_question_fields_accept_defaults():
    from sale_app.core.mutil.fix_question import FixedQuestion

    fq = FixedQuestion()
    assert fq.fixQuestion is None


def test_intention_confirm_fields_accept_defaults():
    from sale_app.core.agent.intention_confirm import IntentionConfirm

    ic = IntentionConfirm()
    assert ic.isIntention is None


def test_information_fields_accept_defaults():
    import sys
    from unittest.mock import MagicMock

    sys.modules.setdefault("sale_app.secrity.sensitive_info", MagicMock())
    sys.modules.pop("sale_app.core.agent.information_gathering", None)

    from sale_app.core.agent.information_gathering import toBeCollectionInformation

    info = toBeCollectionInformation()
    assert info.information is None
    assert info.sequence is None
    assert info.isRecommend is None


def test_qa_handle_fields_accept_defaults():
    import sys
    from unittest.mock import MagicMock

    sys.modules.setdefault("sale_app.core.kb.kb_sevice", MagicMock())
    sys.modules.pop("sale_app.core.agent.qa_handle", None)

    from sale_app.core.agent.qa_handle import QAHandle

    qa = QAHandle()
    assert qa.isIntention is None


def test_product_str_returns_name():
    from sale_app.database.sqlalchemy_models import Product

    p = Product(product_name="测试贷", product_info="info")
    assert str(p) == "测试贷"
