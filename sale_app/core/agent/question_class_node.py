
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableLambda

from sale_app.core.prompt.question_class_prompt import question_class_prompt


def question_class_func(llm: BaseChatModel, members: list):
    categories = []
    for member in members:
        categories.append({"category_name": member})

    question_prompt_runnable = RunnableLambda(
        lambda x: question_class_prompt(
            history=x["messages"],
            question=x["question"],
            categories=categories
        )
    )
    return question_prompt_runnable | llm

# history = [
#     {
#         "role": "user",
#         "content": "hello",
#     },
# ]
# list = ["信息收集", "闲聊经理", "意图确认", "产品推荐", "产品解答专家"]
# data = question_class_func(list).invoke({
#     "question": "这个产品怎么样",
#     "history": history,
# })
# print(data)
