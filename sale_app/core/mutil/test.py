import functools
import json

from langchain_core.messages import AIMessage, ToolMessage
from mpmath import re

from sale_app.core.moudel.zhipuai import ZhipuAI
from sale_app.core.mutil.question_router import create_team_supervisor


def agent_node(state, agent):
    # state["messages"] = state["messages"][:-1]
    result = agent.invoke(state)
    return {"messages": [AIMessage(content=result.content)]}


def super_agent_node(state, agent, name):
    # name = "FINISH"
    messages = state["messages"]
    last_message = messages[-1]
    if isinstance(last_message, AIMessage):
        return {
            "next": name,
        }
    result = agent.invoke(state)
    if isinstance(result, ToolMessage):
        pass
    if isinstance(result, AIMessage):
        result = AIMessage(**result.dict(exclude={"type", "name"}), name=name)
        if result.additional_kwargs:
            next_node = result.additional_kwargs["tool_calls"][0]["function"]["arguments"]
            name = json.loads(next_node)["next"]
        else:
            text = result.content
            match = re.search(r"next='([^']+)'", text)
            if match:
                name = match.group(1)
            else:
                name = state["pre_node"] if state["pre_node"] else "闲聊经理"
        # messages.append(result)
    # else:
    # messages.append(result)
    return {
        "next": name,
    }


llm = ZhipuAI().openai_chat()
super = create_team_supervisor(llm, ["信息收集", "闲聊经理", "意图确认", "产品推荐", "产品解答专家"])

# supervisor_node = functools.partial(super_agent_node, agent=super, name="问题分类")
data = agent_node({"messages":[AIMessage(content="你好")]}, super)
print(data)
