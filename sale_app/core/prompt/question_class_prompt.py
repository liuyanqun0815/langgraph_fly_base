import json

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

from sale_app.core.prompt.question_class_value import SYSTEM_PROMPT, USER_PROMPT_1, USER_PROMPT_2, ASSISTANT_PROMPT_1, \
    ASSISTANT_PROMPT_2, USER_PROMPT_3


def question_class_prompt(history, question, categories):

    prompt_messages = []
    system_prompt_messages = SystemMessage(
        content=SYSTEM_PROMPT.format(histories=history)
    )
    prompt_messages.append(system_prompt_messages)
    user_prompt_message_1 = HumanMessage(
        content=USER_PROMPT_1
    )
    prompt_messages.append(user_prompt_message_1)
    assistant_prompt_message_1 = AIMessage(
        content=ASSISTANT_PROMPT_1
    )
    prompt_messages.append(assistant_prompt_message_1)
    user_prompt_message_2 = HumanMessage(
        content=USER_PROMPT_2
    )
    prompt_messages.append(user_prompt_message_2)
    assistant_prompt_message_2 = AIMessage(
        content=ASSISTANT_PROMPT_2

    )
    prompt_messages.append(assistant_prompt_message_2)
    user_prompt_message_3 = HumanMessage(
        content=USER_PROMPT_3.format(input_text=question,
                                     categories=json.dumps(categories, ensure_ascii=False))
    )
    prompt_messages.append(user_prompt_message_3)
    prompt = ChatPromptTemplate.from_messages(
        prompt_messages
    )
    return prompt
