from sale_app.config.log import Logger
from sale_app.core.pre_safety import pre_handle

thread = {"configurable": {"thread_id": "4"}}
logger = Logger("fly_base")


# 流程控制
def flow_control(question: str, configuable: dict):
    # 前置安全校验
    pre_data = pre_handle(question)
    if pre_data:
        return pre_data

    #信息脱敏





