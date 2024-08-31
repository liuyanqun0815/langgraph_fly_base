from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from sale_app.config.log import Logger
from sale_app.core.mutil.flow_graph import run_flow
from sale_app.secrity.pre_safety import pre_handle
from sale_app.secrity.sensitive_info import sensitive_info_anonymize
from langchain.globals import set_verbose

# thread = {"configurable": {"thread_id": "4"}}
logger = Logger("fly_base")

set_verbose(True)


# 流程控制
def flow_control(question: str, sessionId: str):
    # 前置安全校验
    pre_data = pre_handle(question)
    if pre_data:
        logger.info(f"前置安全校验不通过，返回结果:{pre_data}")
        return pre_data
    configurable = {
        "configurable": {
            "thread_id": sessionId
        }
    }
    data = run_flow(question, configurable)
    messages = data['messages']
    message = [mess for mess in messages if (isinstance(mess, AIMessage) or isinstance(mess, HumanMessage))]
    return message
    # last_message = meessage["messages"][-1]
    # if isinstance(last_message, AIMessage):
    #     logger.info(f"返回结果:{last_message.content}")
    #     return last_message.content
    # return meessage["messages"][-2].content
