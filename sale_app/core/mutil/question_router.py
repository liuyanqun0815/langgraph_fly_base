from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

from sale_app.core.prompt.question_router import ROUTER_SYSTEM


@tool("路由执行任务")
def super_next_agent(next: str) -> dict:
    """选择合适的工作人员处理请求"""
    return {"next": next}


def create_team_supervisor(llm: BaseChatModel, members):
    """团队管理者，负责任务分发."""

    # 如果当前工作人员回答不合理，在换其他的工作人员处理。
    system_prompt = ROUTER_SYSTEM.format(team_members=members, tools=super_next_agent.name)
    options = ["FINISH"] + members
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
            # (
            #     "system",
            #     """鉴于上述对话，, 接下来应该由谁来执行下一步动作?
            #       选择以下一项：{options}"""
            # ),
        ]
    ).partial(options=str(options), team_members=", ".join(members))
    return prompt | llm.bind_tools(tools=[super_next_agent])
