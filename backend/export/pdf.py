"""PDF export for matching reports using reportlab (DASH-02, D-06, D-08).

Registers Chinese TrueType font at import time. Generates A4-format PDF
with JD title, match date, and candidate results table.
"""

import os
from datetime import datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

# ── Font Registration ──────────────────────────────────────────────────────
# Use AR PL SungtiL GB (songti/serif-like Simplified Chinese) which ships
# on this system as a .ttf file. reportlab TTFont requires TrueType outlines
# (not OpenType/CFF). Verified by research: font exists and is TrueType.
_CJK_FONT_PATH = "/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf"
pdfmetrics.registerFont(TTFont("CJKFont", _CJK_FONT_PATH))
# ──────────────────────────────────────────────────────────────────────────


def _cjk_style(name: str = "CJKStyle", size: int = 10, bold: bool = False) -> ParagraphStyle:
    """Create ParagraphStyle with Chinese font support.

    CRITICAL: wordWrap='CJK' must be set for Chinese text wrapping
    (Pitfall 2 from research). Without this, Chinese text overflows
    table cells.
    """
    return ParagraphStyle(
        name=name,
        fontName="CJKFont",
        fontSize=size,
        leading=size * 1.5,
        wordWrap="CJK",
    )


def generate_match_report_pdf(
    jd_title: str,
    match_date: str,
    candidates: list[dict[str, Any]],
    output_path: str,
) -> str:
    """Generate a PDF matching report (D-08).

    Content:
    - JD title as document header
    - Match/generation date
    - Candidate results table with columns: name, score, matched skills,
      missing skills, approval status

    Args:
        jd_title: JD title for the report header.
        match_date: Date string for the report.
        candidates: List of MatchResult dicts with keys:
            candidate_name, match_score, matched_skills, missing_skills,
            should_proceed, recommendation.
        output_path: Absolute path where the PDF will be written.

    Returns:
        The output_path for chaining.

    Raises:
        reportlab-related exceptions on generation failure.
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=20 * mm, bottomMargin=20 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    story: list = []
    base_style = _cjk_style()

    # ── Title ──
    story.append(Paragraph(f"匹配报告: {jd_title}", _cjk_style(size=16, bold=True)))
    story.append(Spacer(1, 6 * mm))

    # ── Meta info ──
    story.append(Paragraph(f"生成日期: {match_date}", base_style))
    story.append(Spacer(1, 10 * mm))

    # ── Candidate table (D-08) ──
    header = ["候选人", "匹配度", "匹配技能", "缺失技能", "审核状态"]
    data = [header]

    for c in candidates:
        status = "通过" if c.get("should_proceed") else (
            "驳回" if c.get("should_proceed") is False else "待审"
        )
        data.append([
            c.get("candidate_name", ""),
            f"{c.get('match_score', 0)}%",
            ", ".join(c.get("matched_skills", []) or []),
            ", ".join(c.get("missing_skills", []) or []),
            status,
        ])

    col_widths = [40 * mm, 20 * mm, 50 * mm, 50 * mm, 20 * mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "CJKFont"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F81BD")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
    ]))
    story.append(table)

    doc.build(story)
    return output_path
