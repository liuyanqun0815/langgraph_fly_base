from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from sale_app.core.moudel.zhipuai import ZhipuAI
from sale_app.core.prompt.question_class_prompt import question_class_prompt

history = [
]

# input_text = "我想买一个苹果手机13"

categories = [{"category_name": "意愿确认"}, {"category_name": "产品推荐"}, {"category_name": "产品问答"},
              {"category_name": "闲聊"}]

llm = ZhipuAI().openai_chat()


messages = question_class_prompt(history, input_text, categories)
prompt = ChatPromptTemplate.from_messages(
    messages
)

chain = RunnablePassthrough.assign(
        history=lambda x: x.get('history', []),
        inputText=lambda x: x['question']  # 直接传递 question 参数
    )| question_class_prompt(history=history, input_text=inputText, categories) | llm

data = chain.invoke({
    "input_text": input_text,
    "history": history,
})