from langchain_core.messages import AIMessage, HumanMessage

from sale_app.core.agent.question_class_node import _format_classify_history
from sale_app.core.prompt.question_class_prompt import question_class_prompt


def test_llm_enable_reasoning_default_false():
    from config import llm_enable_reasoning

    assert llm_enable_reasoning() is False


def test_question_class_few_shot_default():
    from config import question_class_few_shot_count

    assert question_class_few_shot_count() in (0, 1, 2)


def test_format_classify_history_limits_turns():
    messages = []
    for index in range(10):
        messages.append(HumanMessage(content=f"用户{index}"))
        messages.append(AIMessage(content=f"助手{index}"))
    messages.append(HumanMessage(content="当前问题"))
    history = _format_classify_history(messages, max_turns=2)
    assert "用户8" in history or "用户9" in history
    assert "用户0" not in history


def test_question_class_prompt_few_shot_zero():
    prompt = question_class_prompt("（无）", "我要申请贷款", [{"category_name": "意图确认"}], few_shot_count=0)
    message_types = [message.__class__.__name__ for message in prompt.messages]
    assert message_types.count("HumanMessage") == 1
    assert message_types.count("AIMessage") == 0


def test_question_class_prompt_few_shot_two():
    prompt = question_class_prompt("（无）", "我要申请贷款", [{"category_name": "意图确认"}], few_shot_count=2)
    message_types = [message.__class__.__name__ for message in prompt.messages]
    assert message_types.count("HumanMessage") == 3
    assert message_types.count("AIMessage") == 2
