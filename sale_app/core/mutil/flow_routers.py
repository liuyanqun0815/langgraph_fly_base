from sale_app.core.mutil.classify_utils import has_recommended, looks_like_conversion_intent, looks_like_product_qa
from sale_app.core.mutil.node_names import NextNode


def decide_router(state):
    from sale_app.core.agent.collection_utils import is_collection_complete

    nxt = state.get("next") or ""
    pre_node = state.get("pre_node") or ""
    question = state.get("question") or ""

    if has_recommended(state):
        if looks_like_conversion_intent(question):
            return NextNode.CONVERSION
        if state.get("awaiting_conversion") and not state.get("conversion_completed"):
            return NextNode.CONVERSION
        if NextNode.QA in nxt and looks_like_product_qa(question):
            return NextNode.QA
        if looks_like_product_qa(question):
            return NextNode.QA
        if NextNode.GATHER in nxt or NextNode.CONFIRM in nxt or NextNode.RECOMMEND in nxt:
            return NextNode.CONVERSION

    if NextNode.QA in nxt:
        return NextNode.QA
    if not state.get("isInfoConfirmed"):
        if pre_node == NextNode.CONFIRM:
            return NextNode.CONFIRM
        if state.get("awaiting_info_confirm"):
            return NextNode.CONFIRM
    if NextNode.RECOMMEND in nxt:
        if not state.get("isInfoConfirmed"):
            if is_collection_complete(state):
                return NextNode.CONFIRM
            if pre_node == NextNode.GATHER:
                return NextNode.GATHER
        return NextNode.RECOMMEND
    if NextNode.GATHER in nxt:
        if has_recommended(state):
            return NextNode.CONVERSION
        return NextNode.GATHER
    if NextNode.GATHER in pre_node and NextNode.QA not in nxt and not has_recommended(state):
        return NextNode.GATHER
    return nxt


def information_router(state):
    from sale_app.core.agent.collection_utils import is_collection_complete

    if state.get("isInfoConfirmed") or has_recommended(state):
        return NextNode.FINISH
    if state.get("isRecommend") and is_collection_complete(state):
        return NextNode.CONFIRM
    return NextNode.FINISH


def confirm_router(state):
    if state.get("isInfoConfirmed"):
        return NextNode.RECOMMEND
    return NextNode.FINISH
