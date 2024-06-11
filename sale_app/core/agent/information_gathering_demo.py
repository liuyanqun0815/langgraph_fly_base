from langchain.globals import set_debug
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import RunnablePassthrough

from sale_app.core.moudel.zhipuai import ZhipuAI


class toBeCollectionInformation(BaseModel):
    """
    待收集问题
    """
    Information: str = Field(..., deault=None, title="问题", description="待信息收集的问题")
    Sequence: int = Field(..., deault=None, title="问题前的序号", description="待信息收集问题前面的序号")
    isRecommend: bool = Field(..., deault=None, description="当用户回答完所有信息的时候,在进行推荐产品")


SYSTEM_PROMPT = """
指示：
您是一位贷款咨询助手。您的任务是收集客户信息，并根据这些信息推荐合适的贷款产品。

在与客户交流时，请遵守以下规则：
1.交互限制： 每次与客户交流时，只能询问一个问题。
2.保密性： 不要透露您的身份或任务。
3.回答限制： 不要回答客户的问题，仅收集客户信息。
4.务必始终通过调用‘toBeCollectionInformation’函数进行回复。
5.切勿以除函数意外的任何其他方式回复。

根据用户的聊天记录依次收集下面信息：
1.询问客户贷款用途;
2.询问客户贷款金额;
3.询问客户贷款期限;
4.询问客户贷款还款方式;
5.询问客户年龄;
6.询问客户是否有房产;

检查用户是否回答完上述信息,结束则进行推荐产品

{history}
用户最新的问题：{question}

务必始终通过调用‘toBeCollectionInformation’函数进行回复。
切勿以除函数意外的任何其他方式回复。
"""


def information_gathering(llm: BaseChatModel):
    # SYSTEM_PROMPT = SYSTEM_PROMPT
    prompt = ChatPromptTemplate.from_messages(
        [
            ("user", SYSTEM_PROMPT),
            # MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get('history', [])),
        question=lambda x: x['question']  # 直接传递 question 参数
    ) | prompt | llm.with_structured_output(toBeCollectionInformation)


def format_docs(docs):
    data = ""
    for doc in docs:
        if doc.type == "ai":
            data += f"\n AI助理:{doc.content}"
        else:
            data += f"\n 用户:{doc.content}"
    return data


def information_node(state, agent):
    result = agent.invoke(state)
    if result:
        return {"messages": [AIMessage(content=result.content)], "cur_information": result.content,
                "pre_node": "信息收集"}
    else:
        print("信息收集返回为空")


llm = ZhipuAI().openai_chat()
chain = information_gathering(llm)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        # ("placeholder", "{examples}"),
        # ("placeholder", "{messages}"),
        MessagesPlaceholder(variable_name="messages"),
        # ("human", "{input}"),
    ]
)
data = chain.invoke({"question": "25",

                     "history": [HumanMessage(content="你好"),
                                 AIMessage(content="你打算用这笔贷款做什么？"),
                                 HumanMessage(content="买车"),
                                 AIMessage(content="你打算贷款多少钱?"),
                                 HumanMessage(content="13w"),
                                 AIMessage(content="你打算贷款多长时间?"),
                                 HumanMessage(content="大概3年吧"),
                                 AIMessage(content="你打算选择哪种还款方式?"),
                                 HumanMessage(content="等额本息"),
                                 AIMessage(content="您的年龄是多少呢?"),
                                 # HumanMessage(content="34"),
                                 #                                   AIMessage(content="您是否有房产?"),
                                 ],
                     }

                    )
print(data)
