import json

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

from config import question_class_few_shot_count
from sale_app.core.prompt.question_class_value import (
    ASSISTANT_PROMPT_1,
    ASSISTANT_PROMPT_2,
    SYSTEM_PROMPT,
    USER_PROMPT_1,
    USER_PROMPT_2,
    USER_PROMPT_3,
)

_FEW_SHOT_BLOCKS = (
    (USER_PROMPT_1, ASSISTANT_PROMPT_1),
    (USER_PROMPT_2, ASSISTANT_PROMPT_2),
)


def question_class_prompt(history, question, categories, few_shot_count: int | None = None):
    shot_count = question_class_few_shot_count() if few_shot_count is None else max(0, min(2, few_shot_count))
    prompt_messages = [
        SystemMessage(content=SYSTEM_PROMPT.format(histories=history)),
    ]
    for user_prompt, assistant_prompt in _FEW_SHOT_BLOCKS[:shot_count]:
        prompt_messages.append(HumanMessage(content=user_prompt))
        prompt_messages.append(AIMessage(content=assistant_prompt))
    prompt_messages.append(
        HumanMessage(
            content=USER_PROMPT_3.format(
                input_text=question,
                categories=json.dumps(categories, ensure_ascii=False),
            )
        )
    )
    return ChatPromptTemplate.from_messages(prompt_messages)
