"""State and schema definitions for the recruitment agent system."""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
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


class RecruitmentOutput(BaseModel):
    """API response body."""

    final_report: str = Field(description="最终推荐报告")
    match_results: list[MatchResult] = Field(default_factory=list, description="候选人匹配结果列表")
    classification: str = Field(description="本次请求分类")
