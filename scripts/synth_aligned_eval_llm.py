#!/usr/bin/env python3
"""
用 LLM 根据简历正文生成「对齐」的招聘 JD，写出 eval JSONL（替代随机弱标注）。

输入：某目录下的一批 PDF（如 data/eval_pools/IT_eval_run）。
输出：
  - 检索评测：{"query": "<英文 JD>", "relevant": ["<basename>"]}
  - 端到端评测：{"user_input": "...", "relevant_files": [...], "expected_names": []}

依赖：.env 中 OPENAI_API_KEY；与主项目相同的 LLM 配置。

用法::

    conda activate hellojobs
    cd /root/project/hellojobs
    export RESUME_DIR=/root/project/hellojobs/data/eval_pools/IT_eval_run

    python scripts/synth_aligned_eval_llm.py \\
        --resumes-dir data/eval_pools/IT_eval_run \\
        --lines 10 \\
        --out-retrieval data/eval_it_aligned_retrieval.jsonl \\
        --out-e2e data/eval_it_aligned_e2e.jsonl

说明：JD 由模型根据简历摘要归纳，仍非「人工 gold」的严格标准，但显著强于随机配对。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _read_pdf_excerpt(path: Path, max_chars: int) -> str:
    import fitz

    doc = fitz.open(str(path))
    chunks: list[str] = []
    total = 0
    for page in doc:
        chunks.append(page.get_text())
        total = len("\n".join(chunks))
        if total >= max_chars:
            break
    doc.close()
    text = "\n".join(chunks)[:max_chars]
    return " ".join(text.split())


def main() -> None:
    ap = argparse.ArgumentParser(description="LLM 生成与简历对齐的 eval JSONL")
    ap.add_argument(
        "--resumes-dir",
        type=Path,
        required=True,
        help="含 PDF 的目录（相对项目根或绝对路径）",
    )
    ap.add_argument("--lines", type=int, default=10, help="生成多少条（≤ 目录内 PDF 数）")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--excerpt-chars", type=int, default=1200, help="每份简历喂给 LLM 的最大字符")
    ap.add_argument(
        "--out-retrieval",
        type=Path,
        required=True,
        help="输出：eval_rag_metrics 用 JSONL",
    )
    ap.add_argument(
        "--out-e2e",
        type=Path,
        default=None,
        help="可选：eval_end_to_end 用 JSONL",
    )
    args = ap.parse_args()

    rdir = args.resumes_dir
    if not rdir.is_absolute():
        rdir = (ROOT / rdir).resolve()
    pdfs = sorted(rdir.glob("*.pdf"))
    if not pdfs:
        print(f"目录下无 PDF: {rdir}", file=sys.stderr)
        sys.exit(1)

    rng = random.Random(args.seed)
    n = min(args.lines, len(pdfs))
    picked = rng.sample(pdfs, n)

    blocks: list[str] = []
    names: list[str] = []
    for i, p in enumerate(picked, start=1):
        ex = _read_pdf_excerpt(p, args.excerpt_chars)
        names.append(p.name)
        blocks.append(f"### RESUME_INDEX {i}  FILE_NAME: {p.name}\n{ex}\n")

    user_prompt = (
        "You are creating labeled data for resume retrieval evaluation.\n"
        "For EACH resume block below (numbered RESUME_INDEX 1..N), write ONE English job posting "
        "(4–7 sentences) that a real employer could reasonably use to recruit a candidate matching "
        "that resume's skills, roles, and seniority.\n"
        "Rules:\n"
        "- Do NOT include the resume filename or index numbers inside job_posting_en.\n"
        "- Do NOT invent specific person names; use generic role titles.\n"
        "- Do NOT copy long verbatim phrases from the resume; paraphrase into hiring language.\n"
        "- Each job posting must be specific enough that the source resume is a strong match.\n"
        "Return structured output with one entry per index, in order 1..N.\n\n"
        + "\n".join(blocks)
    )

    from pydantic import BaseModel, Field

    class OneJD(BaseModel):
        resume_index: int = Field(ge=1, description="Must match RESUME_INDEX 1..N")
        job_posting_en: str = Field(
            min_length=80,
            description="English job posting aligned to that resume",
        )

    class BatchJD(BaseModel):
        items: list[OneJD] = Field(min_length=n, max_length=n)

    from agent.agent import _build_llm

    llm = _build_llm(temperature=0.2)
    structured = llm.with_structured_output(BatchJD)
    try:
        out: BatchJD = structured.invoke(
            [
                {
                    "role": "system",
                    "content": "You output only valid structured data matching the schema.",
                },
                {"role": "user", "content": user_prompt},
            ]
        )
    except Exception as e:
        print(f"LLM 调用失败: {e}", file=sys.stderr)
        sys.exit(1)

    items_sorted = sorted(out.items, key=lambda x: x.resume_index)
    if len(items_sorted) != n or {x.resume_index for x in items_sorted} != set(range(1, n + 1)):
        print("LLM 返回的索引不完整或与输入不一致", file=sys.stderr)
        sys.exit(1)

    rows_r: list[dict] = []
    rows_e: list[dict] = []
    for item in items_sorted:
        fn = names[item.resume_index - 1]
        if fn != picked[item.resume_index - 1].name:
            print("内部顺序与文件名映射不一致", file=sys.stderr)
            sys.exit(1)
        jd = item.job_posting_en.strip()
        rows_r.append({"query": jd, "relevant": [fn]})
        rows_e.append(
            {
                "user_input": (
                    f"{jd} Please search our resume library, score candidates against this role, "
                    "and give interview recommendations. (Synthetic eval; resume pool is English PDFs.)"
                ),
                "relevant_files": [fn],
                "expected_names": [],
            }
        )

    out_r = args.out_retrieval
    if not out_r.is_absolute():
        out_r = (ROOT / out_r).resolve()
    out_r.parent.mkdir(parents=True, exist_ok=True)
    out_r.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows_r) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] 检索评测集: {out_r}  ({n} 条)", file=sys.stderr)

    if args.out_e2e:
        out_e = args.out_e2e
        if not out_e.is_absolute():
            out_e = (ROOT / out_e).resolve()
        out_e.parent.mkdir(parents=True, exist_ok=True)
        out_e.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows_e) + "\n",
            encoding="utf-8",
        )
        print(f"[ok] 端到端评测集: {out_e}  ({n} 条)", file=sys.stderr)


if __name__ == "__main__":
    main()
