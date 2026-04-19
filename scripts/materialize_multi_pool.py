#!/usr/bin/env python3
"""
从多个 Category 各抽若干 PDF，符号链接到同一目录，形成更大检索候选池。

用法::

    python scripts/materialize_multi_pool.py \\
        --out data/eval_pools/mix_520 \\
        --spec INFORMATION-TECHNOLOGY:120,ENGINEERING:100,FINANCE:100,SALES:100,BUSINESS-DEVELOPMENT:100 \\
        --seed 42

--spec 格式: Category:数量 用逗号分隔；数量超过该目录 PDF 数时自动截断。
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = ROOT / "testdataset" / "data"


def main() -> None:
    ap = argparse.ArgumentParser(description="多 Category 简历池软链")
    ap.add_argument("--dataset-root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--out", type=Path, required=True, help="输出目录（将创建）")
    ap.add_argument(
        "--spec",
        type=str,
        required=True,
        help="如 INFORMATION-TECHNOLOGY:120,ENGINEERING:100,...",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    out = args.out
    if not out.is_absolute():
        out = (ROOT / out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    total = 0
    for part in args.spec.split(","):
        part = part.strip()
        if not part:
            continue
        cat, _, nstr = part.partition(":")
        cat = cat.strip()
        nwant = int(nstr.strip()) if nstr.strip() else 0
        cat_dir = args.dataset_root / cat.upper()
        if not cat_dir.is_dir():
            print(f"[skip] 无目录: {cat_dir}", file=sys.stderr)
            continue
        pdfs = list(cat_dir.glob("*.pdf"))
        if not pdfs:
            print(f"[skip] 无 PDF: {cat_dir}", file=sys.stderr)
            continue
        n = min(nwant, len(pdfs))
        picked = rng.sample(pdfs, n)
        for src in picked:
            dst = out / src.name
            try:
                if dst.is_symlink() or dst.exists():
                    dst.unlink()
            except OSError:
                pass
            dst.symlink_to(src.resolve())
            total += 1
        print(f"[ok] {cat}: {n}/{len(pdfs)} → {out.name}", file=sys.stderr)

    print(f"[ok] 合计软链 {total} 个 PDF → {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
