#!/usr/bin/env python3
"""
端到端招聘效果评测：对每条标注 JD 调用完整 LangGraph（run），根据最终 match_results 计算指标。

用法（在 hellojobs 目录下，需配置 .env 中 OPENAI_API_KEY 等）::

    python scripts/eval_end_to_end.py
    python scripts/eval_end_to_end.py --eval data/eval_end_to_end.jsonl --top-k 5 --limit 3

指标::
    - Recall@K: 按 match_score 排序后取 Top-K，若命中任一 relevant_files / expected_names 则为 1
    - MRR: 全量排序列表中第一个命中项的排名倒数
    - any_hit: Top-K 内是否至少命中一个标注相关人
    - num_matches: 系统返回的匹配条数
    - wall_time_ms / tool_calls / rag_retrievals: observability 快照（若可用）

标注 JSONL 每行字段::
    user_input: 招聘需求全文（会走 triage → planner → worker → reviewer）
    relevant_files: 相关简历文件名列表，如 ["zhang_wei.pdf"]
    expected_names: 可选，中文/英文名，用于 resume_source 缺失时的兜底匹配
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def normalize_matches(raw: list) -> list[dict]:
    from pydantic import BaseModel

    out: list[dict] = []
    for r in raw or []:
        if isinstance(r, dict):
            out.append(r)
        elif isinstance(r, BaseModel):
            out.append(r.model_dump())
        else:
            out.append(dict(r))
    out.sort(key=lambda x: int(x.get("match_score") or 0), reverse=True)
    return out


def is_hit(row: dict, m: dict) -> bool:
    files = row.get("relevant_files") or row.get("relevant") or []
    if isinstance(files, str):
        files = [files]
    names = row.get("expected_names") or []
    src = (m.get("resume_source") or "").replace("\\", "/").lower()
    cn = (m.get("candidate_name") or "").strip().lower()

    for f in files:
        base = Path(str(f)).name.lower()
        stem = Path(str(f)).stem.lower()
        if base and (base in src or src.endswith("/" + base) or src.endswith(base)):
            return True
        if stem and stem in src:
            return True
    for n in names:
        nlow = str(n).strip().lower()
        if not nlow:
            continue
        if nlow in cn or cn in nlow:
            return True
    return False


def recall_at_k(sorted_matches: list[dict], row: dict, k: int) -> float:
    top = sorted_matches[:k]
    return 1.0 if any(is_hit(row, m) for m in top) else 0.0


def mrr(sorted_matches: list[dict], row: dict) -> float:
    for i, m in enumerate(sorted_matches, start=1):
        if is_hit(row, m):
            return 1.0 / i
    return 0.0


def main() -> None:
    ap = argparse.ArgumentParser(description="端到端招聘效果评测（完整 run）")
    ap.add_argument("--eval", type=Path, default=ROOT / "data" / "eval_end_to_end.jsonl")
    ap.add_argument("--top-k", type=int, default=5, help="Recall@K 的 K")
    ap.add_argument("--limit", type=int, default=0, help="只跑前 N 条（0 表示全部）")
    ap.add_argument("--verbose", action="store_true", help="打印每条 match_results 摘要")
    args = ap.parse_args()

    if not args.eval.exists():
        print(f"缺少评测集: {args.eval}", file=sys.stderr)
        sys.exit(1)

    rows = load_jsonl(args.eval)
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    from main import run
    from agent.observability import get_run_metrics

    recalls: list[float] = []
    mrrs: list[float] = []
    wall_ms: list[float] = []
    n_matches: list[int] = []

    print(f"评测集: {args.eval}  |  条数={len(rows)}  |  Recall@{args.top_k}\n")

    for idx, row in enumerate(rows, start=1):
        ui = row["user_input"]
        print(f"[{idx}/{len(rows)}] 运行中…（前 80 字）{ui[:80]}…")

        t0 = time.perf_counter()
        state = run(user_input=ui, resume_text="")
        wall_ms.append((time.perf_counter() - t0) * 1000.0)

        metrics = get_run_metrics()
        matches = normalize_matches(state.get("match_results") or [])
        n_matches.append(len(matches))

        cls = state.get("classification") or ""
        if cls and cls != "inquiry":
            print(f"    ⚠ classification={cls}（本评测集假定 inquiry 检索岗）")

        r = recall_at_k(matches, row, args.top_k)
        m = mrr(matches, row)
        recalls.append(r)
        mrrs.append(m)
        print(
            f"    → Recall@{args.top_k}={r:.0f}  MRR={m:.4f}  "
            f"n={len(matches)}  wall={wall_ms[-1]:.0f}ms  "
            f"metrics={metrics}"
        )

        if args.verbose and matches:
            for j, mm in enumerate(matches[:8], start=1):
                print(
                    f"       #{j} score={mm.get('match_score')} "
                    f"name={mm.get('candidate_name')!r} src={mm.get('resume_source', '')[-40:]!r}"
                )

    import statistics

    print("\n" + "=" * 60)
    print(f"平均 Recall@{args.top_k}: {statistics.mean(recalls):.4f}")
    print(f"平均 MRR:          {statistics.mean(mrrs):.4f}")
    print(f"平均 wall_time:    {statistics.mean(wall_ms):.0f} ms")
    print(f"平均 match 条数:   {statistics.mean(n_matches):.1f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
