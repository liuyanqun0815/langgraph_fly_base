from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableLambda

from config import question_class_history_turns
from sale_app.core.prompt.question_class_prompt import question_class_prompt
from sale_app.util.history_formate import format_docs


def _format_classify_history(messages, max_turns: int | None = None) -> str:
    turns = question_class_history_turns() if max_turns is None else max(0, max_turns)
    if not messages:
        return "（无）"
    # 分类时 question 单独传入，历史中排除最后一条用户消息
    history_messages = list(messages)
    if history_messages and isinstance(history_messages[-1], HumanMessage):
        history_messages = history_messages[:-1]
    if not history_messages or turns == 0:
        return "（无）"
    limit = turns * 2
    return format_docs(history_messages[-limit:])


def question_class_func(llm: BaseChatModel, members: list):
    categories = [{"category_name": member} for member in members]

    question_prompt_runnable = RunnableLambda(
        lambda x: question_class_prompt(
            history=_format_classify_history(x.get("messages")),
            question=x.get("question") or "",
            categories=categories,
        )
    )
    return question_prompt_runnable | llm
