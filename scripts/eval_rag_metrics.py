#!/usr/bin/env python3
"""
离线评测 FAISS +（可选）Rerank 检索效果。

用法（在 hellojobs 项目根目录）::
    python scripts/eval_rag_metrics.py
    python scripts/eval_rag_metrics.py --top-k 5 --eval data/eval_retrieval.jsonl

输入文件为 JSONL，每行::
    {"query": "...", "relevant": ["zhang_wei.pdf", "li_ming.pdf"]}

指标说明::
    - Recall@K: 每条 query 的 top-K 结果中是否命中任一 relevant 文件（0/1），再对 query 取平均
    - MRR: 第一个命中 relevant 的排名倒数（无命中为 0），再平均
    - latency_ms: 单次 retriever.invoke 墙钟时间

注意: 需已配置 Embedding API（.env），且建议先 ``POST /admin/rebuild-index`` 或自行构建向量索引。
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

# 项目根 = hellojobs/
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


def doc_sources(docs: list) -> list[str]:
    out: list[str] = []
    for d in docs:
        src = (d.metadata or {}).get("source", "")
        if src:
            out.append(Path(src).name)
        else:
            out.append("")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="RAG 检索离线指标（Recall@K / MRR / 延迟）")
    ap.add_argument(
        "--eval",
        type=Path,
        default=ROOT / "data" / "eval_retrieval.jsonl",
        help="JSONL 评测集路径",
    )
    ap.add_argument("--top-k", type=int, default=5, help="检索返回条数 K")
    args = ap.parse_args()

    if not args.eval.exists():
        print(f"缺少评测集: {args.eval}", file=sys.stderr)
        sys.exit(1)

    rows = load_jsonl(args.eval)
    if not rows:
        print("评测集为空", file=sys.stderr)
        sys.exit(1)

    from rag.retriever import get_retriever

    retriever = get_retriever(top_k=args.top_k)
    recalls: list[float] = []
    mrrs: list[float] = []
    latencies: list[float] = []

    for row in rows:
        q = row["query"]
        want = {Path(x).name for x in row.get("relevant", [])}
        if not want:
            continue

        t0 = time.perf_counter()
        docs = retriever.invoke(q)
        latencies.append((time.perf_counter() - t0) * 1000.0)

        names = doc_sources(docs)
        hit_at = None
        for i, n in enumerate(names, start=1):
            if n in want:
                hit_at = i
                break

        recalls.append(1.0 if hit_at is not None else 0.0)
        mrrs.append(1.0 / hit_at if hit_at else 0.0)

    print(f"评测文件: {args.eval}")
    print(f"条数: {len(recalls)}  |  top_k={args.top_k}")
    print(f"Recall@{args.top_k}: {statistics.mean(recalls):.4f}")
    print(f"MRR:          {statistics.mean(mrrs):.4f}")
    print(f"latency P50:  {statistics.median(latencies):.1f} ms")
    if len(latencies) >= 2:
        print(f"latency mean: {statistics.mean(latencies):.1f} ms")


if __name__ == "__main__":
    main()
