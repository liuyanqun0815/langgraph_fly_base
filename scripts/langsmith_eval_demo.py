from langchain_core.prompts import ChatPromptTemplate
# from langsmith import as_runnable
from langsmith.evaluation import evaluate, LangChainStringEvaluator
from langsmith.schemas import Run, Example

from sale_app.core.moudel.zhipuai import ZhipuAI

cot_qa_evaluator = LangChainStringEvaluator("cot_qa")
context_qa_evaluator = LangChainStringEvaluator("context_qa")

llm = ZhipuAI().openai_chat()

# prompt = ChatPromptTemplate.from_messages(
#     ("system","你是一个有用的助手")
#     ,("messages")
# )
#
# runer = prompt | llm
from langchain_core.runnables import chain as as_runnable


def accuracy(run: Run, example: Example):
    # Row-level evaluator for accuracy.

    pred = run.outputs["output"]
    expected = example.outputs["answer"]
    return {"score": expected.lower() == pred.lower()}


@as_runnable
def nested_predict(inputs):
    return {"output": "Yes"}


@as_runnable
def lc_predict(inputs):
    return nested_predict.invoke(inputs)


results = evaluate(

    lc_predict,

    data="ds-enchanted-melon-70",

    evaluators=[accuracy],

    description="This time we're evaluating a LangChain object.",

)  # doctest: +ELLIPSIS



lc_predict.invoke("你好")