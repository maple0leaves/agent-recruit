"""State and schema definitions for the recruitment agent system."""

import re
from typing import Annotated, Optional
from typing_extensions import NotRequired, TypedDict
from pydantic import BaseModel, Field, field_validator
from langgraph.graph.message import add_messages


# ── Candidate ──────────────────────────────────────────────────────────────

class CandidateInfo(BaseModel):
    """Structured candidate information extracted from resume."""

    name: str = Field(default="", description="候选人姓名")
    email: str = Field(default="", description="联系邮箱")
    skills: list[str] = Field(default_factory=list, description="技能列表")
    years_of_experience: int = Field(default=0, description="工作年限")
    education: str = Field(default="", description="最高学历")
    summary: str = Field(default="", description="简历摘要")

    @field_validator("skills", mode="before")
    @classmethod
    def _coerce_skills(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in re.split(r"[,，、;；\n]", value) if item.strip()]
        return value

    @field_validator("education", "summary", mode="before")
    @classmethod
    def _coerce_text(cls, value):
        if value is None:
            return ""
        if isinstance(value, list):
            return "；".join(str(item) for item in value if item is not None)
        if isinstance(value, dict):
            return "；".join(str(item) for item in value.values() if item is not None)
        return str(value)

    @field_validator("years_of_experience", mode="before")
    @classmethod
    def _coerce_years(cls, value):
        if value is None or value == "":
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        return int(float(match.group(0))) if match else 0


class MatchResult(BaseModel):
    """Candidate-JD match evaluation result."""

    candidate_name: str = Field(default="", description="候选人姓名")
    match_score: int = Field(default=0, ge=0, le=100, description="匹配分数 0-100")
    matched_skills: list[str] = Field(default_factory=list, description="匹配的技能")
    missing_skills: list[str] = Field(default_factory=list, description="缺失的技能")
    recommendation: str = Field(default="", description="推荐意见")
    should_proceed: bool = Field(default=False, description="是否进入面试")
    resume_source: str = Field(default="", description="简历来源文件路径（可选）")
    resume_text: str = Field(default="", description="简历全文（可选）")

    @field_validator("matched_skills", "missing_skills", mode="before")
    @classmethod
    def _coerce_skill_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in re.split(r"[,，、;；\n]", value) if item.strip()]
        return value

    @field_validator("recommendation", "resume_source", "resume_text", mode="before")
    @classmethod
    def _coerce_text(cls, value):
        if value is None:
            return ""
        if isinstance(value, list):
            return "；".join(str(item) for item in value if item is not None)
        if isinstance(value, dict):
            return "；".join(str(item) for item in value.values() if item is not None)
        return str(value)

    @field_validator("match_score", mode="before")
    @classmethod
    def _coerce_score(cls, value):
        if value is None or value == "":
            return 0
        if isinstance(value, (int, float)):
            return max(0, min(100, int(value)))
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        return max(0, min(100, int(float(match.group(0))))) if match else 0

    @field_validator("should_proceed", mode="before")
    @classmethod
    def _coerce_bool(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in {"true", "yes", "y", "1", "是", "建议", "推荐"}


# ── Approval ──

class CandidateApproval(BaseModel):
    """Per-candidate approval decision from HR review (D-09, D-10)."""
    candidate_name: str = Field(description="候选人姓名")
    approved: bool = Field(description="是否通过")
    feedback: str = Field(default="", description="审核备注（驳回必填）")


# ── JD ─────────────────────────────────────────────────────────────────────

class JDInfo(BaseModel):
    """Structured job description information."""

    title: str = Field(default="", description="岗位名称")
    required_skills: list[str] = Field(default_factory=list, description="必须技能")
    preferred_skills: list[str] = Field(default_factory=list, description="加分技能")
    min_years_experience: int = Field(default=0, description="最低工作年限要求")
    education_requirement: str = Field(default="", description="学历要求")
    description: str = Field(default="", description="岗位描述")

    @field_validator("required_skills", "preferred_skills", mode="before")
    @classmethod
    def _coerce_skill_list(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in re.split(r"[,，、;；\n]", value) if item.strip()]
        return value

    @field_validator("education_requirement", "description", mode="before")
    @classmethod
    def _coerce_text(cls, value):
        if value is None:
            return ""
        if isinstance(value, list):
            return "；".join(str(item) for item in value if item is not None)
        if isinstance(value, dict):
            return "；".join(str(item) for item in value.values() if item is not None)
        return str(value)

    @field_validator("min_years_experience", mode="before")
    @classmethod
    def _coerce_years(cls, value):
        if value is None or value == "":
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        match = re.search(r"\d+(?:\.\d+)?", str(value))
        return int(float(match.group(0))) if match else 0


# ── Router ─────────────────────────────────────────────────────────────────

class RouterSchema(BaseModel):
    """Triage router output schema."""

    classification: str = Field(
        description="分类结果: new_resume | inquiry | ignore"
    )
    reasoning: str = Field(description="分类理由")


# ── Main Graph State ────────────────────────────────────────────────────────

class RecruitmentState(TypedDict):
    """Full state object passed through the LangGraph workflow."""

    # ── Input ──
    user_input: str                          # 原始输入（JD 描述 或 候选人查询）
    resume_text: Optional[str]               # 单份简历文本（可选）
    match_top_k: NotRequired[int]            # 智能匹配召回候选人数

    # ── Parsed ──
    jd_info: Optional[JDInfo]               # 解析后的岗位信息
    candidates: list[CandidateInfo]          # 检索到的候选人列表

    # ── Evaluation ──
    match_results: list[MatchResult]         # 匹配评分结果列表
    final_report: str                        # Reviewer 生成的最终报告

    # ── Routing ──
    classification: str                      # new_resume | inquiry | ignore
    next_action: str                         # planner 决定的下一步动作

    # ── HITL ──
    hr_approved: Optional[bool]             # HR 是否批准
    hr_feedback: str                         # HR 反馈内容
    candidate_decisions: dict[str, bool]     # 逐候选人审核结果 (D-09 via per-candidate)

    # ── Messages (short-term memory) ──
    messages: Annotated[list, add_messages]


# ── Input / Output schemas for API ─────────────────────────────────────────

class RecruitmentInput(BaseModel):
    """API request body."""

    user_input: str = Field(description="招聘需求或候选人查询，例如：招聘3年经验Python工程师")
    resume_text: Optional[str] = Field(default=None, description="可选：直接传入单份简历文本")
    top_k: int = Field(default=5, ge=1, le=30, description="智能匹配召回候选人数")


class RecruitmentOutput(BaseModel):
    """API response body."""

    final_report: str = Field(description="最终推荐报告")
    match_results: list[MatchResult] = Field(default_factory=list, description="候选人匹配结果列表")
    classification: str = Field(description="本次请求分类")
