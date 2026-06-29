"""LangGraph workflow definition and entry point for the recruitment system."""

import os
import sys
from uuid import uuid4

sys.path.insert(0, os.path.dirname(__file__))

import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END

from config import init_langsmith, LANGSMITH_TRACING, LANGSMITH_PROJECT
from agent.schemas import RecruitmentState
from agent.observability import reset_run_metrics, get_run_metrics
from agent.agent import (
    triage_router,
    planner_agent,
    worker_agent,
    reviewer_agent,
    single_resume_agent,
    should_continue_planning,
)

_langsmith_active = init_langsmith()


# ── Build the LangGraph workflow ─────────────────────────────────────────────

def build_graph(use_hitl: bool = False):
    """Build and compile the recruitment workflow graph.

    Args:
        use_hitl: If True, add a human review interrupt before reviewer_agent

    Returns:
        Compiled LangGraph runnable
    """
    builder = StateGraph(RecruitmentState)

    # Nodes
    builder.add_node("triage_router", triage_router)
    builder.add_node("planner_agent", planner_agent)
    builder.add_node("worker_agent", worker_agent)
    builder.add_node("reviewer_agent", reviewer_agent)
    builder.add_node("single_resume_agent", single_resume_agent)

    # Edges
    builder.add_edge(START, "triage_router")

    # Planner → Worker (if tool calls) or Reviewer (if done)
    builder.add_conditional_edges(
        "planner_agent",
        should_continue_planning,
        {
            "worker_agent": "worker_agent",
            "reviewer_agent": "reviewer_agent",
        },
    )

    # Worker loops back to planner after executing tools
    builder.add_edge("worker_agent", "planner_agent")

    # End nodes
    builder.add_edge("reviewer_agent", END)
    builder.add_edge("single_resume_agent", END)

    # HITL: interrupt before reviewer so HR can review
    interrupt_before = ["reviewer_agent"] if use_hitl else []

    # Use SqliteSaver for persistent checkpoints
    sqlite_conn = sqlite3.connect("data/dev.db", check_same_thread=False)
    checkpointer = SqliteSaver(sqlite_conn)
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=interrupt_before,
    )


# ── Default compiled graph instances ─────────────────────────────────────────

recruitment_graph = build_graph(use_hitl=False)
recruitment_graph_hitl = build_graph(use_hitl=True)


# ── CLI entry point ───────────────────────────────────────────────────────────

def run(
    user_input: str,
    resume_text: str = "",
    top_k: int = 5,
    use_hitl: bool = False,
    thread_id: str | None = None,
) -> dict:
    """Run the recruitment workflow and return the final state.

    Args:
        user_input: Recruitment requirement description
        resume_text: Optional raw resume text (for new_resume flow)
        top_k: Number of candidates to recall for matching
        use_hitl: Whether to enable Human-in-the-Loop mode
        thread_id: Optional thread identifier. Defaults to a fresh id per run.

    Returns:
        Final state dictionary
    """
    graph = recruitment_graph_hitl if use_hitl else recruitment_graph
    config = {"configurable": {"thread_id": thread_id or f"run-{uuid4().hex}"}}

    if _langsmith_active:
        from langchain_core.tracers import LangChainTracer

        tracer = LangChainTracer(project_name=LANGSMITH_PROJECT)
        config["callbacks"] = [tracer]

    reset_run_metrics()

    initial_state: RecruitmentState = {
        "user_input": user_input,
        "resume_text": resume_text or None,
        "match_top_k": max(1, min(30, int(top_k or 5))),
        "jd_info": None,
        "candidates": [],
        "match_results": [],
        "final_report": "",
        "classification": "",
        "next_action": "",
        "hr_approved": None,
        "hr_feedback": "",
        "messages": [],
    }

    result = graph.invoke(initial_state, config=config)
    return result


if __name__ == "__main__":
    if _langsmith_active:
        print(f"[observability] LangSmith tracing ON → project: {LANGSMITH_PROJECT}")
    else:
        print("[observability] LangSmith tracing OFF")

    user_input = input("请输入招聘需求（例如：招聘一个3年经验的Python工程师）：\n> ").strip()
    result = run(user_input)

    metrics = get_run_metrics()
    print("\n" + "=" * 60)
    print("📊 最终报告：")
    print("=" * 60)
    print(result.get("final_report", "（无报告）"))
    print("\n" + "-" * 60)
    print(f"📈 运行指标: {metrics}")
