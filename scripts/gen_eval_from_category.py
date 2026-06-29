#!/usr/bin/env python3
"""
从 testdataset/data/<Category>/ 抽取 N 份 PDF，生成评测用 JSONL（模板，建议人工抽查）。

典型流程::

    # 1) 生成检索评测集 + 把样本软链到独立目录（便于 RESUME_DIR 只索引这一池）
    python scripts/gen_eval_from_category.py \\
        --category INFORMATION-TECHNOLOGY \\
        --n 120 --lines 50 \\
        --materialize data/eval_pools/INFORMATION-TECHNOLOGY \\
        --out data/eval_it_retrieval.jsonl \\
        --e2e-out data/eval_it_e2e.jsonl

    # 2) 让向量库只建在这一池上（.env 或临时环境变量）
    export RESUME_DIR=/绝对路径/hellojobs/data/eval_pools/INFORMATION-TECHNOLOGY
    # 删旧索引或依赖 VECTOR_INDEX_AUTO_REBUILD 在目录变化后重建

    # 3) 跑检索离线指标
    python scripts/eval_rag_metrics.py --eval data/eval_it_retrieval.jsonl --top-k 5

    # 4) 可选：端到端（耗 LLM）
    python scripts/eval_end_to_end.py --eval data/eval_it_e2e.jsonl

说明:
    - 每行随机指定 1 份池内 PDF 为 ``relevant`` / ``relevant_files``，JD 为按 Category 选的英文模板之一；
      属于「弱标注」：Recall 不一定高，用于压测与流程验证，写论文需人工改 query/标签。
    - ``--materialize`` 使用**符号链接**指向原 PDF，不占双倍磁盘。
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "testdataset" / "data"


# 按文件夹名给英文 JD 模板（多句轮换，避免 50 行 query 完全相同）
JD_TEMPLATES: dict[str, list[str]] = {
    "INFORMATION-TECHNOLOGY": [
        "Hiring a software engineer with backend or full-stack experience. "
        "Strong fundamentals in data structures, APIs, databases, and shipping production code.",
        "Looking for an IT professional: web development, scripting, troubleshooting, "
        "and collaboration in agile teams. Cloud or DevOps exposure is a plus.",
        "Recruiting a developer for building and maintaining business applications, "
        "debugging issues, and improving reliability of internal software systems.",
    ],
    "ENGINEERING": [
        "Hiring an engineer with design, analysis, and project delivery experience. "
        "Hands-on technical work, documentation, and cross-functional coordination.",
        "Seeking an engineering professional for technical problem solving, "
        "systems thinking, and implementation of engineering solutions.",
    ],
    "BUSINESS-DEVELOPMENT": [
        "Hiring for business development: market outreach, partnerships, "
        "pipeline growth, and client relationship management.",
    ],
    "FINANCE": [
        "Recruiting a finance professional: analysis, reporting, budgeting, "
        "and compliance awareness in a corporate environment.",
    ],
    "ACCOUNTANT": [
        "Hiring an accountant: bookkeeping, reconciliations, tax or audit support, "
        "and attention to detail with financial statements.",
    ],
    "BANKING": [
        "Looking for a banking sector professional with customer-facing or "
        "operations experience and knowledge of financial products.",
    ],
    "SALES": [
        "Recruiting sales talent: prospecting, closing deals, CRM hygiene, "
        "and consistent quota achievement in a competitive market.",
    ],
    "HR": [
        "Hiring an HR specialist: recruiting coordination, employee relations, "
        "policies, onboarding, and HR administration.",
    ],
    "HEALTHCARE": [
        "Seeking a healthcare professional with clinical or administrative experience, "
        "patient-focused mindset, and regulatory awareness.",
    ],
    "CONSULTANT": [
        "Hiring a consultant profile: structured problem solving, client delivery, "
        "slides and analysis, and stakeholder communication.",
    ],
    "ADVOCATE": [
        "Recruiting legal / advocate profile: research, drafting, case preparation, "
        "and advocacy or advisory experience.",
    ],
    "CHEF": [
        "Hiring culinary professional: kitchen operations, menu execution, "
        "food safety, and high-volume service experience.",
    ],
    "FITNESS": [
        "Looking for a fitness professional: coaching, program design, "
        "and client motivation in a gym or studio setting.",
    ],
    "AVIATION": [
        "Recruiting aviation-related experience: operations, safety culture, "
        "and technical or customer service roles in the industry.",
    ],
    "CONSTRUCTION": [
        "Hiring construction sector experience: site coordination, safety, "
        "scheduling, and trade collaboration.",
    ],
    "PUBLIC-RELATIONS": [
        "Seeking PR / communications talent: media outreach, messaging, "
        "campaigns, and brand reputation work.",
    ],
    "TEACHER": [
        "Hiring an educator: curriculum delivery, student engagement, "
        "and classroom or training facilitation experience.",
    ],
    "ARTS": [
        "Looking for arts / creative profile: portfolio-driven work, "
        "production or performance experience, and collaboration.",
    ],
    "APPAREL": [
        "Recruiting apparel / fashion industry experience: merchandising, "
        "retail operations, or supply chain exposure.",
    ],
    "AGRICULTURE": [
        "Hiring agriculture-related experience: field operations, supply, "
        "or agribusiness process knowledge.",
    ],
    "AUTOMOBILE": [
        "Seeking automobile industry experience: technical, sales, or service roles "
        "in automotive organizations.",
    ],
    "BPO": [
        "Hiring BPO / operations profile: process adherence, ticketing, "
        "quality metrics, and customer communication.",
    ],
    "DIGITAL-MEDIA": [
        "Recruiting digital media talent: content, campaigns, analytics, "
        "and online channel growth.",
    ],
}

DEFAULT_JD = (
    "We are hiring an experienced professional in this field. "
    "Strong communication, ownership of deliverables, and relevant industry experience."
)


def _jd_for_category(category: str, variant_index: int) -> str:
    templates = JD_TEMPLATES.get(category, [DEFAULT_JD])
    return templates[variant_index % len(templates)]


def _collect_pdfs(category_dir: Path) -> list[Path]:
    if not category_dir.is_dir():
        raise FileNotFoundError(f"目录不存在: {category_dir}")
    pdfs = sorted(category_dir.glob("*.pdf"))
    if not pdfs:
        raise FileNotFoundError(f"目录下无 PDF: {category_dir}")
    return pdfs


def _materialize_symlinks(files: list[Path], dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for src in files:
        dst = dest / src.name
        try:
            if dst.is_symlink() or dst.exists():
                dst.unlink()
        except OSError:
            pass
        dst.symlink_to(src.resolve())


def main() -> None:
    ap = argparse.ArgumentParser(description="从 testdataset Category 抽样并生成 eval JSONL")
    ap.add_argument(
        "--dataset-root",
        type=Path,
        default=DEFAULT_DATASET,
        help="含各类别子目录的根路径（默认 testdataset/data）",
    )
    ap.add_argument(
        "--category",
        type=str,
        required=True,
        help="子目录名，如 INFORMATION-TECHNOLOGY",
    )
    ap.add_argument(
        "--n",
        type=int,
        default=100,
        help="从该类随机抽样的 PDF 数量（构成候选池）",
    )
    ap.add_argument(
        "--lines",
        type=int,
        default=40,
        help="生成的 JSONL 行数（每行 1 个 gold relevant）",
    )
    ap.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子，便于复现",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="检索评测 JSONL 输出路径（默认 data/eval_<category>_retrieval.jsonl）",
    )
    ap.add_argument(
        "--e2e-out",
        type=Path,
        default=None,
        help="若指定则额外写端到端评测 JSONL（字段兼容 eval_end_to_end.py）",
    )
    ap.add_argument(
        "--materialize",
        type=Path,
        default=None,
        help="将抽样得到的 N 个 PDF 符号链接到此目录，便于单独设置 RESUME_DIR",
    )
    args = ap.parse_args()

    cat = args.category.strip().upper()
    cat_dir = args.dataset_root / cat
    all_pdfs = _collect_pdfs(cat_dir)

    rng = random.Random(args.seed)
    n = min(args.n, len(all_pdfs))
    pool = rng.sample(all_pdfs, n)

    if args.materialize:
        mat = args.materialize
        if not mat.is_absolute():
            mat = (ROOT / mat).resolve()
        _materialize_symlinks(pool, mat)
        print(f"[ok] 已软链 {n} 个 PDF → {mat}", file=sys.stderr)

    lines = max(1, args.lines)
    out_retrieval = args.out or (ROOT / "data" / f"eval_{cat.lower().replace('-', '_')}_retrieval.jsonl")
    out_retrieval.parent.mkdir(parents=True, exist_ok=True)

    rows_retrieval: list[dict] = []
    rows_e2e: list[dict] = []

    for i in range(lines):
        gold = pool[i % len(pool)]
        base = gold.name
        jd = _jd_for_category(cat, i)
        rows_retrieval.append({"query": jd, "relevant": [base]})
        rows_e2e.append(
            {
                "user_input": (
                    f"[Eval template EN] {jd} "
                    f"Please search the resume library and rank candidates; "
                    f"gold file for this row (weak label): {base}"
                ),
                "relevant_files": [base],
                "expected_names": [],
            }
        )

    out_retrieval.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows_retrieval) + "\n",
        encoding="utf-8",
    )
    print(f"[ok] 检索评测集: {out_retrieval}  ({lines} 行)", file=sys.stderr)

    e2e_path = args.e2e_out
    if e2e_path:
        if not e2e_path.is_absolute():
            e2e_path = (ROOT / e2e_path).resolve()
        e2e_path.parent.mkdir(parents=True, exist_ok=True)
        e2e_path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows_e2e) + "\n",
            encoding="utf-8",
        )
        print(f"[ok] 端到端评测集: {e2e_path}  ({lines} 行)", file=sys.stderr)

    print("\n后续建议:", file=sys.stderr)
    print(
        f"  1) 将 RESUME_DIR 指到含上述 PDF 的目录"
        f"（若用了 --materialize 则: {args.materialize.resolve() if args.materialize else cat_dir}）",
        file=sys.stderr,
    )
    print("  2) 重建或依赖自动重建向量索引后运行:", file=sys.stderr)
    print(f"     python scripts/eval_rag_metrics.py --eval {out_retrieval}", file=sys.stderr)
    if e2e_path:
        print(f"     python scripts/eval_end_to_end.py --eval {e2e_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
