from sale_app.config.log import Logger
from sale_app.core.mutil.flow_graph import run_flow
from sale_app.core.pre_safety import pre_handle
from sale_app.core.sensitive_info import sensitive_info_anonymize

thread = {"configurable": {"thread_id": "4"}}
logger = Logger("fly_base")


# 流程控制
def flow_control(question: str, sessionId: str):
    # 前置安全校验
    pre_data = pre_handle(question)
    if pre_data:
        logger.info(f"前置安全校验不通过，返回结果:{pre_data}")
        return pre_data
    # 信息脱敏
    question = sensitive_info_anonymize(question)
    logger.info(f"信息脱敏结果:{question}")
    configurable = {
        "configurable": {
            "thread_id": sessionId
        }
    }
    run_flow(question, configurable)
    return question
