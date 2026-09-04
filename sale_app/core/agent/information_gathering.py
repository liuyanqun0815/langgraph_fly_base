import os
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from pydantic import BaseModel, Field

from sale_app.config.log import Logger
from sale_app.core.mutil.node_names import NextNode
from sale_app.core.prompt.chat_manager_prompt import INFORMATION_SYSTEM_PROMPT
from sale_app.secrity.sensitive_info import sensitive_info_anonymize
from sale_app.util.history_formate import format_docs

logger = Logger("fly_base")

from sale_app.core.agent.collection_utils import information_count, normalize_sequences

COLLECTION_QUESTIONS = [
    "请问您的贷款用途是什么？（例如：购房、购车、装修、经营等）",
    "请问您期望申请的贷款金额是多少？（单位：万元）",
    "请问您希望的贷款期限是多久？（例如：1年、3年、5年）",
    "请问您的年龄是多少？",
]

COLLECTION_LABELS = ["贷款用途", "贷款金额", "贷款期限", "客户年龄"]


class toBeCollectionInformation(BaseModel):
    """信息收集结构化输出：information 必须是发给客户的下一句问话，不是对用户答案的摘要。"""

    information: str = Field(
        ...,
        title="下一句问话",
        description=(
            "发给客户的完整回复：可先简短确认用户上一答（1句），再提出下一个待收集问题。"
            "禁止只复述用户答案（如「购房和装修」）；必须包含问句。"
        ),
    )
    sequence: int = Field(
        ...,
        title="下一问序号",
        description="即将询问的信息项序号，取值 1～4，与收集顺序一致",
    )
    isRecommend: bool = Field(
        default=False,
        description="四项信息均已收集完毕时为 true，否则为 false",
    )


def _normalize_sequences(raw) -> list[int]:
    return normalize_sequences(raw)


def resolve_collection_progress(state: dict) -> tuple[list[int], int, int]:
    """根据对话进度计算：已完成序号、即将询问序号、本次应写入 state 的增量。"""
    collected = _normalize_sequences(state.get("information_sequences"))
    messages = state.get("messages") or []
    last_message = messages[-1] if messages else None
    pre_node = state.get("pre_node") or ""

    sequences_delta: list[int] = []
    steps_done = len(collected)

    if isinstance(last_message, HumanMessage) and pre_node == NextNode.GATHER and steps_done < information_count:
        newly_completed = steps_done + 1
        if newly_completed not in collected:
            sequences_delta = [newly_completed]
        steps_done = len(collected) + len(sequences_delta)

    next_step = steps_done + 1
    return sequences_delta, steps_done, next_step


def _looks_like_question(text: str) -> bool:
    text = (text or "").strip()
    if not text:
        return False
    if "?" in text or "？" in text:
        return True
    return any(text.startswith(prefix) for prefix in ("请问", "能否", "方便", "您希望", "您期望"))


def _is_echo_of_user(reply: str, user_text: str) -> bool:
    reply = re.sub(r"\s+", "", (reply or "").strip())
    user_text = re.sub(r"\s+", "", (user_text or "").strip())
    if not reply or not user_text:
        return False
    if reply == user_text:
        return True
    if len(reply) <= len(user_text) + 2 and user_text in reply:
        return True
    return False


def build_collection_reply(result: toBeCollectionInformation, next_step: int, user_text: str) -> str:
    """校验 LLM 输出，必要时回退到标准问句模板。"""
    if next_step > information_count:
        return "好的，信息已收集完整，正在为您匹配合适的产品方案。"

    template = COLLECTION_QUESTIONS[next_step - 1]
    reply = (result.information or "").strip()

    if not _looks_like_question(reply) or _is_echo_of_user(reply, user_text):
        logger.info(f"信息收集回复无效，使用模板问句: next_step={next_step} reply={reply}")
        if next_step == 1:
            return template
        label = COLLECTION_LABELS[next_step - 2]
        return f"好的，已了解您的{label}。{template}"

    if result.sequence != next_step:
        logger.info(f"信息收集序号修正: llm={result.sequence} expected={next_step}")
    return reply


def information_gathering(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages([("user", INFORMATION_SYSTEM_PROMPT)])

    return RunnablePassthrough.assign(
        history=lambda x: format_docs(x.get("history", [])),
        question=lambda x: x["question"],
        information_sequences=lambda x: _normalize_sequences(x.get("information_sequences")),
        information_count=lambda x: information_count,
        steps_done=lambda x: resolve_collection_progress(x)[1],
        next_step=lambda x: resolve_collection_progress(x)[2],
        next_question_hint=lambda x: (
            COLLECTION_QUESTIONS[resolve_collection_progress(x)[2] - 1]
            if resolve_collection_progress(x)[2] <= information_count
            else "（已全部收集）"
        ),
        collection_label=lambda x: (
            COLLECTION_LABELS[resolve_collection_progress(x)[2] - 1]
            if 1 <= resolve_collection_progress(x)[2] <= information_count
            else ""
        ),
    ) | prompt | llm.with_structured_output(toBeCollectionInformation)


def information_node(state, agent, name):
    messages = state["messages"]
    state["history"] = messages[:-1]
    last_message = messages[-1]

    sequences_delta, steps_done, next_step = resolve_collection_progress(state)
    # steps_done 已包含本次 sequences_delta，勿重复累加
    completed_steps = steps_done

    if isinstance(last_message, HumanMessage):
        state["question"] = last_message.content
        if os.getenv("USER_INFO_MASK"):
            state["question"] = sensitive_info_anonymize(last_message.content)
            logger.info(f"{name}节点脱敏后: {state['question']}")
    else:
        state["question"] = ""

    if completed_steps >= information_count:
        return {
            "information_sequences": sequences_delta,
            "pre_node": name,
            "isRecommend": True,
        }

    result = agent.invoke(state)
    if not result:
        logger.warning("%s节点返回为空", name)
        fallback = COLLECTION_QUESTIONS[next_step - 1]
        return {
            "messages": [AIMessage(content=fallback)],
            "information_sequences": sequences_delta,
            "pre_node": name,
            "isRecommend": False,
        }

    reply = build_collection_reply(result, next_step, state.get("question") or "")

    logger.info(
        f"{name}节点: steps_done={steps_done} completed={completed_steps} next_step={next_step} reply={reply}"
    )
    return {
        "messages": [AIMessage(content=reply)],
        "information_sequences": sequences_delta,
        "pre_node": name,
        "isRecommend": False,
    }
