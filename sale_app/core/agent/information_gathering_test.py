from langchain.globals import set_debug
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field

from sale_app.core.moudel.zhipuai import ZhipuAI


class toBeCollectionInformation(BaseModel):
    """
    待收集问题
    """
    nextInformation: str = Field(..., deault=None, title="问题", description="待信息收集的问题")
    # nextSequence: int = Field(..., deault=None, title="问题前的序号", description="待信息收集问题前面的序号")

# set_debug(True)
# SYSTEM_PROMPT = """
# 指示：
# 您是一位贷款咨询助手。您的任务是收集客户信息，并根据这些信息推荐合适的贷款产品。在与客户交流时，请遵守以下规则：
#   1.交互限制： 每次与客户交流时，只能询问一个问题。
#   2.保密性： 不要透露您的身份或任务。
#   3.回答限制： 不要回答客户的问题，仅收集客户信息。
#   4.必须使用工具或函数进行输出结果
# 信息收集顺序：
# 1.询问客户贷款用途;
# 2.询问客户贷款金额;
# 3.询问客户贷款期限;
# 4.询问客户贷款还款方式;
# 5.询问客户年龄;
# 6.询问客户是否有房产;
#
# 已经收集信息:{cur_information}
# 请继续收集下一个信息
# """
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

务必始终通过调用‘toBeCollectionInformation’函数进行回复。
切勿以除函数意外的任何其他方式回复。
"""


def information_gathering(llm: BaseChatModel):
    # SYSTEM_PROMPT = SYSTEM_PROMPT
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )

    return prompt | llm.with_structured_output(toBeCollectionInformation)


def information_node(state, agent, name):
    result = agent.invoke(state)
    if result:
        return {"messages": [AIMessage(content=result.content)], "cur_information": result.content,
                "pre_node": name}
    else:
        print("信息收集返回为空")
#
# llm = ZhipuAI().openai_chat()
# chain = information_gathering(llm)
# prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", SYSTEM_PROMPT),
#             # ("placeholder", "{examples}"),
#             # ("placeholder", "{messages}"),
#             MessagesPlaceholder(variable_name="messages"),
#             # ("human", "{input}"),
#         ]
#     )
# data = chain.invoke({"messages": [HumanMessage(content="你好"),
#                                   AIMessage(content="你打算用这笔贷款做什么？"),
#                                   HumanMessage(content="买车"),
#                                   AIMessage(content="你打算贷款多少钱?"),
#                                   HumanMessage(content="13w")
#                                   ],
#                      }
#
#                     )
# print(data)
