from langchain_core.messages import HumanMessage, AIMessage


def format_docs(docs):
    data = ""
    for doc in docs:
        if doc.type == "ai":
            data += f"\n AI助理:{doc.content}"
        else:
            data += f"\n 用户:{doc.content}"
    return data

list =[
                       HumanMessage(content="我喜欢吃苹果")
                       , AIMessage(content="苹果富含很高的维生素，具有很高的营养价值")
                       # , HumanMessage(content="你认为中国是哪个国家的首都？")
                       # , AIMessage(content="中国是哪个国家的首都？")
                       # , HumanMessage(content="你认为中国是哪个国家的首都？")
                   ]

d =format_docs(list)
print(d)