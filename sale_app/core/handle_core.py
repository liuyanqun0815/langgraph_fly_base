from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

from sale_app.config.log import Logger
from sale_app.core.mutil.flow_graph import astream_flow, run_flow
from sale_app.secrity.pre_safety import pre_handle
from sale_app.secrity.sensitive_info import sensitive_info_anonymize
from langchain_core.globals import set_verbose

# thread = {"configurable": {"thread_id": "4"}}
logger = Logger("fly_base")

set_verbose(True)


# 流程控制
def flow_control(question: str, sessionId: str):
    # 前置安全校验
    pre_data = pre_handle(question)
    if pre_data:
        logger.info(f"前置安全校验不通过，返回结果:{pre_data}")
        return [HumanMessage(content=question), AIMessage(content=pre_data)]
    configurable = {
        "configurable": {
            "thread_id": sessionId
        }
    }
    data = run_flow(question, configurable)
    messages = data['messages']
    message = [mess for mess in messages if (isinstance(mess, AIMessage) or isinstance(mess, HumanMessage))]
    return message


async def stream_flow_control(question: str, session_id: str):
    """SSE 流式：前置安全校验后推送 LangGraph token 与工作流步骤事件。"""
    import asyncio

    from sale_app.core.mutil.flow_graph import ESTIMATED_WORKFLOW_STEPS

    yield {"type": "progress", "current": 0, "total": ESTIMATED_WORKFLOW_STEPS, "label": "准备执行…"}

    yield {"type": "step_start", "step": 1, "node": "前置安全校验", "input": question}
    pre_data = await asyncio.to_thread(pre_handle, question)
    if pre_data:
        logger.info(f"前置安全校验不通过，返回结果:{pre_data}")
        yield {
            "type": "step_end",
            "step": 1,
            "node": "前置安全校验",
            "output": pre_data,
            "status": "blocked",
        }
        yield {"type": "progress", "current": 1, "total": 1, "label": "安全校验拦截"}
        yield {"type": "token", "text": pre_data}
        return

    yield {"type": "step_end", "step": 1, "node": "前置安全校验", "output": "通过", "status": "ok", "duration_ms": 0}

    config = {"configurable": {"thread_id": session_id}}
    async for event in astream_flow(question, config, step_offset=1):
        yield event
