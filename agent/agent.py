"""Planner, Worker, and Reviewer agent node implementations."""

import json
import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langgraph.types import Command
from typing import Literal

from config import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    RAG_TOP_K,
)
from agent.memory import save_candidate_record
from agent.schemas import (
    CandidateInfo,
    JDInfo,
    MatchResult,
    RecruitmentState,
    RouterSchema,
)
from agent.tools import ALL_TOOLS, TOOLS_BY_NAME
from agent.prompt import (
    JD_PARSE_PROMPT,
    PLANNER_SYSTEM_PROMPT,
    REVIEWER_SYSTEM_PROMPT,
    TRIAGE_SYSTEM_PROMPT,
    TRIAGE_USER_PROMPT,
)


def _build_llm(temperature: float = LLM_TEMPERATURE):
    """Build LLM instance, supporting both OpenAI and OpenRouter."""
    if OPENAI_BASE_URL:
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=temperature,
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL,
            default_headers={"HTTP-Referer": "https://github.com/recruitment-agent"},
        )
    return init_chat_model(f"openai:{LLM_MODEL}", temperature=temperature)


_llm = _build_llm()
_llm_router = _llm.with_structured_output(RouterSchema)
_llm_jd = _llm.with_structured_output(JDInfo)
_llm_with_tools = _llm.bind_tools(ALL_TOOLS, tool_choice="any")
_llm_reviewer = _build_llm(temperature=0.3)


def _build_search_query(jd_info: JDInfo, user_input: str) -> str:
    """Create a retrieval query from structured JD info."""
    parts: list[str] = []
    if jd_info.title:
        parts.append(jd_info.title)
    if jd_info.required_skills:
        parts.append("必须技能：" + "、".join(jd_info.required_skills))
    if jd_info.preferred_skills:
        parts.append("加分技能：" + "、".join(jd_info.preferred_skills))
    if jd_info.min_years_experience:
        parts.append(f"{jd_info.min_years_experience}年经验")
    if jd_info.education_requirement:
        parts.append(f"{jd_info.education_requirement}学历")
    if jd_info.description:
        parts.append(jd_info.description)
    return "；".join(parts) or user_input


def _fallback_search_plan(jd_info: JDInfo, user_input: str) -> AIMessage:
    """Create a deterministic search tool call when the planner skips tools."""
    return AIMessage(
        content="先搜索最匹配的候选人。",
        tool_calls=[
            {
                "name": "search_candidates",
                "args": {
                    "query": _build_search_query(jd_info, user_input),
                    "top_k": RAG_TOP_K,
                },
                "id": f"search_{uuid4().hex}",
                "type": "tool_call",
            }
        ],
    )


def _candidate_key(candidate: CandidateInfo) -> str:
    """Create a stable key for candidate deduplication."""
    return candidate.email or candidate.name


def _coerce_candidate(value: CandidateInfo | dict | str) -> CandidateInfo:
    """Convert tool outputs into CandidateInfo."""
    if isinstance(value, CandidateInfo):
        return value
    if isinstance(value, str):
        return CandidateInfo.model_validate_json(value)
    return CandidateInfo.model_validate(value)


def _coerce_match_result(value: MatchResult | dict | str) -> MatchResult:
    """Convert tool outputs into MatchResult."""
    if isinstance(value, MatchResult):
        return value
    if isinstance(value, str):
        return MatchResult.model_validate_json(value)
    return MatchResult.model_validate(value)


def triage_router(state: RecruitmentState) -> Command[Literal["planner_agent", "single_resume_agent", "__end__"]]:
    """Classify the incoming request and route to the appropriate agent."""
    if state.get("resume_text"):
        print("📄 分类：NEW_RESUME → 解析单份简历")
        return Command(
            goto="single_resume_agent",
            update={"classification": "new_resume"},
        )

    result = _llm_router.invoke(
        [
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": TRIAGE_USER_PROMPT.format(user_input=state["user_input"])},
        ]
    )

    classification = result.classification

    if classification == "new_resume":
        print("📄 分类：NEW_RESUME → 解析单份简历")
        return Command(
            goto="single_resume_agent",
            update={"classification": classification},
        )
    if classification == "inquiry":
        print("🔍 分类：INQUIRY → 搜索候选人库")
        return Command(
            goto="planner_agent",
            update={"classification": classification},
        )

    print("🚫 分类：IGNORE → 忽略")
    return Command(
        goto="__end__",
        update={
            "classification": classification,
            "final_report": "此请求已被忽略（无关内容）",
        },
    )


def _parse_jd(user_input: str) -> JDInfo:
    """Parse job description from user input."""
    return _llm_jd.invoke(JD_PARSE_PROMPT.format(user_input=user_input))


def planner_agent(state: RecruitmentState) -> dict:
    """Planner: parse JD and decide which tools to call."""
    jd_info = state.get("jd_info") or _parse_jd(state["user_input"])
    print(f"📋 JD 解析完成：{jd_info.title or '未命名岗位'}")

    if state.get("match_results"):
        return {
            "jd_info": jd_info,
            "messages": [AIMessage(content="已完成候选人检索与评分，进入 Reviewer 阶段。")],
            "next_action": "reviewer",
        }

    response = _llm_with_tools.invoke(
        [
            {
                "role": "system",
                "content": PLANNER_SYSTEM_PROMPT.format(
                    user_input=state["user_input"],
                    jd_info=jd_info.model_dump_json(ensure_ascii=False),
                ),
            },
            *state.get("messages", []),
            {
                "role": "user",
                "content": (
                    "请开始执行招聘任务。"
                    "如果还没有检索结果，请优先调用 search_candidates。"
                    "如果已经有完整候选人评分结果，就不要再调用工具。"
                ),
            },
        ]
    )

    if not getattr(response, "tool_calls", None) and not state.get("candidates"):
        response = _fallback_search_plan(jd_info, state["user_input"])

    return {
        "jd_info": jd_info,
        "messages": [response],
        "next_action": "execute_tools" if getattr(response, "tool_calls", None) else "reviewer",
    }


def worker_agent(state: RecruitmentState) -> dict:
    """Worker: execute tool calls requested by the planner."""
    last_message = state["messages"][-1]
    results = []
    jd_info = state.get("jd_info")
    jd_json = jd_info.model_dump_json(ensure_ascii=False) if jd_info else "{}"

    candidate_map = {
        _candidate_key(_coerce_candidate(candidate)): _coerce_candidate(candidate)
        for candidate in state.get("candidates", [])
    }
    match_map = {
        _coerce_match_result(result).candidate_name or f"candidate_{index}": _coerce_match_result(result)
        for index, result in enumerate(state.get("match_results", []))
    }

    for tool_call in last_message.tool_calls:
        tool = TOOLS_BY_NAME[tool_call["name"]]
        print(f"⚙️  调用工具：{tool_call['name']}")
        observation = tool.invoke(tool_call["args"])
        results.append(
            {
                "role": "tool",
                "content": observation,
                "tool_call_id": tool_call["id"],
            }
        )

        if tool_call["name"] == "search_candidates":
            candidates = json.loads(observation)
            for candidate_payload in candidates:
                resume_text = candidate_payload.get("resume_text") or candidate_payload.get("content", "")
                if not resume_text:
                    continue

                candidate_json = TOOLS_BY_NAME["analyze_resume"].invoke({"resume_text": resume_text})
                candidate = _coerce_candidate(candidate_json)
                if not candidate.name:
                    candidate.name = candidate_payload.get("name", "")
                if not candidate.email:
                    candidate.email = candidate_payload.get("email", "")

                candidate_map[_candidate_key(candidate)] = candidate

                match_json = TOOLS_BY_NAME["score_match"].invoke(
                    {
                        "candidate_json": candidate.model_dump_json(ensure_ascii=False),
                        "jd_json": jd_json,
                    }
                )
                match_result = _coerce_match_result(match_json)
                if not match_result.candidate_name:
                    match_result.candidate_name = candidate.name
                match_result.resume_source = candidate_payload.get("source", "")
                match_result.resume_text = resume_text
                match_map[match_result.candidate_name] = match_result

        elif tool_call["name"] == "analyze_resume":
            candidate = _coerce_candidate(observation)
            candidate_map[_candidate_key(candidate)] = candidate

        elif tool_call["name"] == "score_match":
            match_result = _coerce_match_result(observation)
            match_map[match_result.candidate_name] = match_result

    sorted_matches = sorted(match_map.values(), key=lambda item: item.match_score, reverse=True)

    return {
        "messages": results,
        "candidates": list(candidate_map.values()),
        "match_results": sorted_matches,
        "next_action": "reviewer" if sorted_matches else "execute_tools",
    }


def reviewer_agent(state: RecruitmentState) -> dict:
    """Reviewer: evaluate all match results and generate final report."""
    match_results = [_coerce_match_result(result) for result in state.get("match_results", [])]
    jd_info = state.get("jd_info")

    if not match_results:
        return {"final_report": "未找到可推荐的候选人，请尝试调整岗位描述或补充简历库。"}

    match_results = sorted(match_results, key=lambda item: item.match_score, reverse=True)
    hr_approved = state.get("hr_approved")
    hr_feedback = state.get("hr_feedback", "").strip()

    if hr_approved is False:
        summary_lines = ["HR 未批准当前候选人推荐结果。"]
        if hr_feedback:
            summary_lines.append(f"HR 反馈：{hr_feedback}")
        summary_lines.append("候选人评分概览：")
        for result in match_results:
            summary_lines.append(f"- {result.candidate_name}: {result.match_score}/100")
        return {"final_report": "\n".join(summary_lines), "match_results": match_results}

    match_results_str = json.dumps(
        [result.model_dump() for result in match_results],
        ensure_ascii=False,
        indent=2,
    )
    jd_str = jd_info.model_dump_json(ensure_ascii=False) if jd_info else state.get("user_input", "")

    reviewer_request = "请生成最终推荐报告。"
    if hr_approved is True:
        reviewer_request = "HR 已审核通过，请在最终报告中体现 HR 的确认意见。"
    if hr_feedback:
        reviewer_request += f"\nHR 反馈：{hr_feedback}"

    report = _llm_reviewer.invoke(
        [
            {
                "role": "system",
                "content": REVIEWER_SYSTEM_PROMPT.format(
                    jd_info=jd_str,
                    match_results=match_results_str,
                ),
            },
            {"role": "user", "content": reviewer_request},
        ]
    )

    position = jd_info.title if jd_info else state.get("user_input", "")
    for result in match_results:
        decision = "approved" if hr_approved else "recommended"
        if not result.should_proceed:
            decision = "hold"
        save_candidate_record(
            candidate_name=result.candidate_name,
            match_score=result.match_score,
            position=position,
            decision=decision,
        )

    print("✅ Reviewer 报告生成完成")
    return {
        "final_report": report.content,
        "match_results": match_results,
    }


def single_resume_agent(state: RecruitmentState) -> dict:
    """Handle a single resume submission: parse, score, and report."""
    from agent.tools import analyze_resume, score_match

    resume_text = state.get("resume_text", "") or state.get("user_input", "")
    if not resume_text:
        return {"final_report": "请提供 resume_text 以评估单份简历。"}

    jd_info = _parse_jd(state["user_input"]) if not state.get("jd_info") else state["jd_info"]

    candidate_json = analyze_resume.invoke({"resume_text": resume_text})
    print("📄 简历解析完成")

    match_json = score_match.invoke(
        {
            "candidate_json": candidate_json,
            "jd_json": jd_info.model_dump_json(ensure_ascii=False) if jd_info else "{}",
        }
    )
    match_result = MatchResult.model_validate_json(match_json)
    match_result.resume_text = resume_text
    print(f"📊 匹配分数：{match_result.match_score}")

    return {
        "jd_info": jd_info,
        "match_results": [match_result],
        "final_report": (
            f"候选人 {match_result.candidate_name} 匹配分数：{match_result.match_score}/100\n"
            f"匹配技能：{', '.join(match_result.matched_skills)}\n"
            f"缺失技能：{', '.join(match_result.missing_skills)}\n"
            f"建议：{match_result.recommendation}"
        ),
    }


def should_continue_planning(state: RecruitmentState) -> Literal["worker_agent", "reviewer_agent"]:
    """Route: if planner produced tool calls → worker; else → reviewer."""
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "worker_agent"
    return "reviewer_agent"
