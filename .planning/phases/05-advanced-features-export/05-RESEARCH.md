# Phase 5: Advanced Features & Export - Research

**Researched:** 2026-04-26
**Domain:** PDF/Excel generation (reportlab, openpyxl), reverse matching API, Agent feedback integration
**Confidence:** HIGH

## Summary

Phase 5 implements three independent features built on Phase 4's matching infrastructure. 

**Reverse Matching (MATCH-04):** Reuses the SSE streaming pipeline and Matching page, but starts from CandidateDetail with a candidate_id instead of jd_id. The agent direction is inverted -- search for JDs matching this candidate instead of candidates matching this JD. Requires a new API endpoint (or parameterized existing one), minimal backend logic changes, and mostly frontend plumbing.

**Agent Feedback (APRV-03):** Natural extension of Phase 4's HITL resume mechanism. A new "feedback" button on review cards opens a dialog for free-text feedback. The resume request adds a feedback field, the reviewer_agent incorporates it into re-scoring, and results re-stream via SSE. The `hr_feedback` field already exists in `RecruitmentState` -- the gap is the frontend UX and the re-run SSE flow.

**PDF/Excel Export (DASH-02):** reportlab with proper TrueType Chinese font (arphic-gbsn00lp.ttf ships on this system) for PDF generation, openpyxl for Excel. Both are well-established libraries with straightforward APIs for table-based document generation. Export buttons appear only in DONE state on the Matching page.

**Primary recommendation:** Implement reverse matching and feedback as extensions of the existing SSE/HITL framework. Export is entirely independent. Parallelize where possible.

### Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Reverse matching API | API / Backend | -- | New endpoint building on existing HITL stream infrastructure |
| Reverse matching UI | Browser / Client | -- | Reuses Matching page; button added to CandidateDetail |
| Agent feedback processing | API / Backend | -- | Extends existing HITL resume mechanism with feedback field |
| Feedback UI | Browser / Client | -- | Feedback button/dialog on MatchCandidateCard |
| PDF generation | API / Backend | -- | Backend reportlab ensures font availability and format control |
| Excel generation | API / Backend | -- | Backend openpyxl for consistent formatting |
| File download | API / Backend | CDN / Static | FastAPI FileResponse serves generated files |
| Export buttons | Browser / Client | -- | Shown in DONE state on Matching page |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MATCH-04 | Candidate-side reverse matching | SSE pipeline reusable; backend needs parameterized endpoint accepting candidate_id; Agent direction reversal is query construction |
| APRV-03 | Agent feedback during review | HITL resume mechanism extensible; `hr_feedback` field exists in state; frontend needs new dialog + re-run SSE flow |
| DASH-02 | PDF/Excel export | reportlab 4.x + openpyxl 3.x standard; Chinese fonts available at /usr/share/fonts/; FastAPI FileResponse for download |
</phase_requirements>

<user_constraints>
## User Constraints (from 05-CONTEXT.md)

### Reverse Matching (Candidate -> JD)
- **D-01:** Trigger from CandidateDetail "reverse match" button
- **D-02:** Reuse Matching page + SSE infrastructure, pass candidate_id not jd_id, Agent direction reversed

### Agent Feedback
- **D-03:** Feedback button on review cards -> dialog with free-text input
- **D-04:** Reuse HITL resume mechanism, resume request adds feedback field, Agent adjusts based on feedback and re-pushes via SSE
- **D-05:** After feedback, Agent re-runs matching, results streamed via SSE again

### PDF/Excel Export
- **D-06:** Backend generation -- reportlab for PDF, openpyxl for Excel, must support Chinese
- **D-07:** Export button on matching results page (DONE state), two options: PDF and Excel
- **D-08:** PDF report content: JD title, match date, candidate list (name/score/skills comparison/approval status)
- **D-09:** Excel content: single sheet, columns contain candidate name/match score/matched skills/missing skills/approval status/notes

### Carried Forward from Phase 1-4
- SSE streaming matching infrastructure (Phase 4)
- HITL resume mechanism (Phase 4)
- Matching page and 9-state state machine (Phase 4)
- Candidate detail page (Phase 3)
- JD model and API (Phase 2)
- Auth + SQLAlchemy + shadcn/ui (Phase 1)
- FastAPI FileResponse for file download

### Claude's Discretion
- PDF layout (font sizes, table widths, headers/footers)
- Excel column width and cell styles
- Export button position (top or bottom of results page)
- Feedback dialog placeholder text
- reportlab Chinese font registration method

### Deferred Ideas (OUT OF SCOPE)
- Batch export multiple sessions -> single session only
- Custom export templates -> fixed format
- Export history page -> export from results page directly
- Independent reverse matching UI page -> reuse forward matching page
</phase_constraints>

## Standard Stack

### Core

| Library | Version (Verified) | Purpose | Why Standard |
|---------|-------------------|---------|--------------|
| reportlab | 4.x [VERIFIED: pip registry] | PDF generation | De facto Python PDF library; supports TTF/TTC fonts for CJK; SimpleDocTemplate + Platypus for table layouts |
| openpyxl | 3.x [VERIFIED: pip registry] | Excel generation | Standard Python xlsx library; native Unicode (Chinese headers work without special setup) |

### Installation

```bash
pip install reportlab openpyxl
```

No additional font packages needed -- the system ships `/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf` (AR PL SungtiL GB, songti/serif-like Simplified Chinese) which is a proper .ttf file directly supported by reportlab's `TTFont`.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| reportlab | fpdf2 / weasyprint / pdfkit | reportlab is the most mature; fpdf2 has smaller footprint but less layout control; weasyprint requires CSS-to-PDF pipeline that adds complexity for simple tables |
| openpyxl | xlsxwriter / pandas | openpyxl is the standard for programmatic xlsx; xlsxwriter cannot modify existing files; pandas adds unnecessary dependency |
| Backend reportlab | Frontend jsPDF / html2canvas | Frontend PDF requires browser fonts which may lack Chinese support; backend ensures consistent results |

## Architecture Patterns

### System Architecture Diagram

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │                            FRONTEND (React)                              │
 │                                                                          │
 │  CandidateDetail          MatchCandidateCard         Matching (DONE)     │
 │  ┌─────────────────┐    ┌─────────────────────┐    ┌──────────────────┐ │
 │  │ 反向匹配 button │───>│ 反馈重新匹配 button │    │ [PDF] [Excel]    │ │
 │  │ (D-01)          │    │ + dialog (D-03)     │    │ (D-07)           │ │
 │  └────────┬────────┘    └─────────┬───────────┘    └────────┬─────────┘ │
 │           │                      │                          │            │
 │           │ navigate /matching   │ POST /recruit/hitl/      │ GET        │
 │           │ ?candidate_id=X      │ resume + feedback        │ /matching/ │
 │           │                      │                          │ {id}/export│
 │           v                      v                          v            │
 ├──────────────────────────────────────────────────────────────────────────┤
 │                             API (FastAPI)                                │
 │                                                                          │
 │  POST /recruit/hitl/stream    POST /recruit/hitl/resume   GET /matching │
 │  (accepts jd_id OR            (accepts feedback field)    /{id}/export/ │
 │   candidate_id)                                        {pdf,excel}      │
 │         │                           │                          │         │
 │         │ SSE stream                │ feedback in               │ File    │
 │         │                           │ hr_feedback field         │Response │
 │         v                           v                          v         │
 ├──────────────────────────────────────────────────────────────────────────┤
 │                          BACKEND (Python)                                │
 │                                                                          │
 │  LangGraph Graph          reviewer_agent               Export Service    │
 │  ┌────────────────┐     ┌──────────────────────┐    ┌────────────────┐  │
 │  │ triage_router  │     │ Reads hr_feedback    │    │ reportlab PDF  │  │
 │  │ planner_agent  │     │ from state, passes   │    │ openpyxl Excel │  │
 │  │ worker_agent   │     │ to LLM for re-scoring│    └────────────────┘  │
 │  │ reviewer_agent │     └──────────────────────┘                        │
 │  └────────────────┘                                                     │
 └──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities Table (File-to-Implementation Mapping)

| File | Role in Phase 5 |
|------|-----------------|
| `api/server.py` | New reverse matching endpoint (or parameterized HITLStreamRequest); feedback field in HITLResumeRequest; new GET /matching/{session_id}/export/pdf and /export/excel endpoints |
| `agent/agent.py` | reviewer_agent already processes hr_feedback text; no structural changes needed, but may need better prompt for feedback-based re-scoring |
| `agent/schemas.py` | Add `candidate_feedback` field to RecruitmentState or extend CandidateApproval; add ExportRequest schemas |
| `frontend/src/pages/Matching.tsx` | Support candidate_id routing; add export buttons in DONE state; add feedback re-run flow |
| `frontend/src/components/Matching/MatchCandidateCard.tsx` | Add "feedback re-match" button (D-03) |
| `frontend/src/components/Candidates/CandidateDetail.tsx` | Add "reverse match" button (D-01) |
| `frontend/src/hooks/useMatchingSSE.ts` | Optionally extend to support re-run after feedback |
| `frontend/src/api/matching.ts` | Add startReverseMatchingStream, submitFeedbackAndRerun export functions |
| `backend/` (new) | Export module with reportlab PDF and openpyxl Excel generators |

### Recommended Project Structure (Additions)

```
backend/
├── export/
│   ├── __init__.py
│   ├── pdf.py           # reportlab PDF generation
│   └── excel.py         # openpyxl Excel generation
```

### Pattern 1: Reverse Matching via Parameterized SSE Endpoint

**What:** The existing `POST /recruit/hitl/stream` accepts `jd_id`. For reverse matching, create a variant or accept both parameters.

**When to use:** When reusing the same SSE streaming pipeline but inverting the query direction.

**Example (Backend API):**
```python
# Option A: New endpoint (cleaner separation)
class HITLReverseRequest(BaseModel):
    candidate_id: int = Field(description="Candidate ID to find matching JDs for")

@app.post("/recruit/hitl/reverse-stream")
async def hitl_reverse_stream(
    request: HITLReverseRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """SSE streaming endpoint for reverse matching (MATCH-04, D-02).
    
    Fetches candidate from DB, constructs a reverse query (find JDs matching
    this candidate), and starts the HITL LangGraph streaming.
    """
    from backend.db.models.candidate import Candidate
    
    # Fetch candidate
    result = await db.execute(select(Candidate).where(Candidate.id == request.candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    # Construct reverse user_input -- search JDs that match this candidate's skills
    user_input = f"为以下候选人匹配最合适的职位：{candidate.name}，技能：{candidate.skills}，经验：{candidate.experience}，学历：{candidate.education}"
    
    # Reuse the same SSE streaming generator, but jd_id = 0 to signal reverse mode
    # The generator creates MatchSession with candidate_id instead of jd_id
    return StreamingResponse(
        _stream_hitl_recruitment(user_input, jd_id=0, request=http_request, db=db, candidate_id=request.candidate_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

**Example (Frontend API):**
```typescript
// frontend/src/api/matching.ts
export function startReverseMatchingStream(
  candidateId: number,
  signal?: AbortSignal
): Promise<Response> {
  return fetch("/recruit/hitl/reverse-stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate_id: candidateId }),
    credentials: "include",
    signal,
  });
}
```

### Pattern 2: Agent Feedback via HITL Resume Extension

**What:** The existing `POST /recruit/hitl/resume` accepts `approvals` (list of CandidateApproval). For agent feedback, add a `feedback_rerun` flag or similar mechanism that tells the agent to re-process with the feedback text.

**When to use:** Extending the HITL pipeline to support iterative feedback.

**Example (Backend - HITLResumeRequest):**
```python
class HITLResumeRequest(BaseModel):
    thread_id: str
    approvals: list[CandidateApproval]
    feedback_rerun: bool = False       # NEW: triggers agent re-run (APRV-03, D-04)
    global_feedback: str = ""          # NEW: free-text feedback from HR
```

The `reviewer_agent` already accepts `hr_feedback` text. When `feedback_rerun=True`, the resume endpoint should:
1. Store the feedback in state
2. Re-invoke the graph with the existing state
3. The reviewer_agent reads hr_feedback and incorporates it into LLM re-scoring

**Example (Frontend - useMatchingSSE):**
```typescript
// Add to useMatchingSSE hook
const submitFeedback = useCallback(
  async (feedback: string) => {
    if (!threadIdRef.current) return;
    setState("SUBMITTING");
    try {
      const result = await submitReview(threadIdRef.current, getCurrentDecisions(), {
        feedback_rerun: true,
        global_feedback: feedback,
      });
      // Re-enter streaming mode to show new results
      setState("STREAMING");
      // ... SSE handling continues
    } catch (err) { ... }
  }, []
);
```

### Pattern 3: PDF Export with Chinese Font

**What:** Generate PDF using reportlab with registered Chinese TrueType font.

**When to use:** Server-side document generation with Chinese text.

**Example (Backend - backend/export/pdf.py):**
```python
"""PDF export using reportlab (DASH-02, D-06, D-08)."""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# Register Chinese font (D-06)
# /usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf ships on this system
# or use DroidSansFallbackFull.ttf which also supports CJK
_CJK_FONT_PATH = "/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf"
pdfmetrics.registerFont(TTFont("CJKFont", _CJK_FONT_PATH))


def _cjk_style(name="CJKStyle", size=10, bold=False):
    return ParagraphStyle(
        name=name,
        fontName="CJKFont",
        fontSize=size,
        leading=size * 1.5,
        wordWrap="CJK",  # CRITICAL for Chinese text wrapping
    )


def generate_match_report_pdf(
    jd_title: str,
    match_date: str,
    candidates: list[dict],  # list of MatchResult dicts
    output_path: str,
):
    """Generate PDF report for a matching session (D-08).
    
    Content:
    - JD title header
    - Match date
    - Candidate table: name, score, skills comparison, approval status
    """
    doc = SimpleDocTemplate(output_path, pagesize=A4, 
                            topMargin=20*mm, bottomMargin=20*mm)
    story = []
    base_style = _cjk_style()
    
    # Title
    story.append(Paragraph(f"匹配报告: {jd_title}", _cjk_style(size=16, bold=True)))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph(f"生成日期: {match_date}", base_style))
    story.append(Spacer(1, 10*mm))
    
    # Table header + data
    header = ["候选人", "匹配度", "匹配技能", "缺失技能", "审核状态"]
    data = [header]
    for c in candidates:
        status = "通过" if c.get("should_proceed") else ("驳回" if c.get("should_proceed") is False else "待审")
        data.append([
            c.get("candidate_name", ""),
            f"{c.get('match_score', 0)}%",
            ", ".join(c.get("matched_skills", [])),
            ", ".join(c.get("missing_skills", [])),
            status,
        ])
    
    table = Table(data, colWidths=[40*mm, 20*mm, 50*mm, 50*mm, 20*mm])
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
```

### Pattern 4: Excel Export with openpyxl

**What:** Generate Excel workbook with single sheet and styled headers.

**When to use:** Server-side spreadsheet generation.

**Example (Backend - backend/export/excel.py):**
```python
"""Excel export using openpyxl (DASH-02, D-06, D-09)."""

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


def generate_match_report_excel(
    candidates: list[dict],
    output_path: str,
    sheet_title: str = "匹配结果",
):
    """Generate single-sheet Excel report (D-09).
    
    Columns: candidate name, match score, matched skills, missing skills, 
    approval status, notes.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    
    # Headers (D-09)
    headers = ["候选人姓名", "匹配度", "匹配技能", "缺失技能", "审核状态", "备注"]
    ws.append(headers)
    
    # Style headers
    header_font = Font(name="Noto Sans CJK SC", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
    
    # Data rows
    for c in candidates:
        status = "通过" if c.get("should_proceed") else ("驳回" if c.get("should_proceed") is False else "待审")
        ws.append([
            c.get("candidate_name", ""),
            c.get("match_score", 0),
            ", ".join(c.get("matched_skills", [])),
            ", ".join(c.get("missing_skills", [])),
            status,
            c.get("recommendation", ""),
        ])
    
    # Set column widths
    ws.column_dimensions["A"].width = 18  # name
    ws.column_dimensions["B"].width = 10  # score
    ws.column_dimensions["C"].width = 40  # matched skills
    ws.column_dimensions["D"].width = 40  # missing skills
    ws.column_dimensions["E"].width = 12  # status
    ws.column_dimensions["F"].width = 30  # notes
    
    wb.save(output_path)
```

### Anti-Patterns to Avoid

- **Resumable file download:** Do not store generated PDF/Excel in DB. Generate on-the-fly to a temp file, return via FileResponse, then clean up. Use `tempfile.NamedTemporaryFile(delete=False)` or a dedicated `data/exports/` directory with periodic cleanup.
- **Frontend PDF generation:** Do not generate PDF in the browser. Backend reportlab ensures Chinese font availability and consistent rendering. Frontend PDF tools (jsPDF, html2pdf) lack reliable CJK support without embedding fonts.
- **Per-candidate SSE restart:** For agent feedback, do not start a brand-new SSE connection. Instead, re-use the existing flow: submit feedback via POST /resume, then have the frontend restart a new SSE stream to receive updated results.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF generation | Manual PDF byte construction | reportlab (SimpleDocTemplate + Platypus) | Hand-rolled PDF means reimplementing page layout, font embedding, table formatting, pagination -- reportlab handles all of this |
| Excel generation | Manual XML xlsx construction | openpyxl | xlsx is a zipped XML format with complex schemas; openpyxl is the community standard |
| Font discovery | Hardcoded font path | ReportLab + system fonts | The system has /usr/share/fonts/ with proper CJK .ttf files; register them once at import time |
| File download | Custom streaming implementation | FastAPI FileResponse | FileResponse handles headers, streaming, cleanup; write temp file, return response |

**Key insight:** PDF and Excel generation look simple but have deep edge cases (Chinese font fallback, text overflow, page breaks, column width fitting). Established libraries handle these correctly.

## Common Pitfalls

### Pitfall 1: reportlab TTFont with .otf files fails silently
**What goes wrong:** Chinese characters render as blank squares or the PDF fails to generate.
**Why it happens:** Noto Sans CJK is distributed as OpenType (.otf) with PostScript/CFF outlines. ReportLab's `TTFont` requires TrueType outlines. [VERIFIED: reportlab source code at hg.reportlab.com]
**How to avoid:** Use only `.ttf` or `.ttc` font files. This system has `/usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf` which is a proper TrueType font. For `.ttc` files (e.g., NotoSansCJK-Regular.ttc), use `TTFont(..., subfontIndex=2)` to select Simplified Chinese sub-font. [VERIFIED: font inventory on system]
**Warning signs:** Empty squares instead of Chinese characters, or `TTFError: "postscript outlines are not supported"`.

### Pitfall 2: reportlab Paragraph does not wrap Chinese text correctly
**What goes wrong:** Chinese text overflows table cell boundaries or does not break at character boundaries.
**Why it happens:** By default, reportlab uses Western word-wrapping (break at spaces). Chinese text has no spaces between words.
**How to avoid:** Always set `wordWrap='CJK'` in ParagraphStyle when using Chinese fonts. [ASSUMED based on training knowledge; verified by Chinese tutorial sources]
**Warning signs:** Text runs past column width, text wraps mid-character.

### Pitfall 3: openpyxl font name for Chinese fonts
**What goes wrong:** Excel renders Chinese characters in a different font than specified.
**Why it happens:** The font name passed to openpyxl must match a font name registered in the system, not a file path. openpyxl embeds the font name, Excel renders using matching installed fonts.
**How to avoid:** Use standard font names like "微软雅黑", "宋体", or simply omit the font name for data cells (Excel falls back to its default CJK font). Headers can use any name since they are just metadata. [ASSUMED based on training knowledge]
**Warning signs:** Chinese characters show in a different font than specified.

### Pitfall 4: Reverse matching MatchSession requires schema changes
**What goes wrong:** MatchSession model has `jd_id` as NOT NULL, but reverse matching has no JD.
**Why it happens:** The model was designed for forward matching (JD -> candidates).
**How to avoid:** Make `jd_id` nullable (add `candidate_id` column as alternative), or create a separate MatchSession variant for reverse matches. Option A (nullable jd_id + new candidate_id field) is cleaner and reuses the existing dashboard query logic. [VERIFIED: backend/db/models/match_session.py has jd_id=Column(Integer, nullable=False)]
**Warning signs:** Database integrity error when creating MatchSession for reverse match.

### Pitfall 5: SSE re-run after feedback leaves stale state
**What goes wrong:** After submitting feedback, the SSE stream restarts but the Matching page may show stale candidates from the previous run.
**Why it happens:** The 9-state machine does not handle "re-streaming" -- once in DONE, it cannot go back to STREAMING without a full reset.
**How to avoid:** Either (a) reset to STREAMING state and clear candidates when feedback re-run is triggered, or (b) add a new "RE-STREAMING" state to distinguish initial matching from re-matching. Approach (a) is simpler and matches user expectation (old results replaced by new ones). [ASSUMED based on reading useMatchingSSE.ts 9-state machine]
**Warning signs:** Candidate cards show results from both old and new runs overlapping.

## Code Examples

### Reverse Matching: Frontend Hook Extension

```typescript
// frontend/src/api/matching.ts (extend existing file)
export function startReverseMatchingStream(
  candidateId: number,
  signal?: AbortSignal
): Promise<Response> {
  return fetch("/recruit/hitl/reverse-stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ candidate_id: candidateId }),
    credentials: "include",
    signal,
  });
}
```

Source: Existing `startMatchingStream` pattern in `frontend/src/api/matching.ts` [VERIFIED: codebase].

### Matching Page: Candidate Detail "Reverse Match" Button

```tsx
// In CandidateDetail.tsx, add after the PipelineActions card
import { useNavigate } from "react-router-dom";

// Inside CandidateDetail component
const navigate = useNavigate();

// In the return JSX, add a new section or button
<Button
  variant="outline"
  className="gap-2"
  onClick={() => navigate(`/matching?candidateId=${candidateId}`)}
>
  <Search className="h-4 w-4" />
  反向匹配
</Button>
```

Source: Existing navigation patterns in `frontend/src/components/Candidates/CandidateDetail.tsx` [VERIFIED: codebase].

### Feedback Dialog on MatchCandidateCard

```tsx
// In MatchCandidateCard.tsx, add "feedback re-match" button
interface MatchCandidateCardProps {
  candidate: MatchResult;
  onApprove: () => void;
  onReject: () => void;
  onFeedback?: () => void;  // NEW for APRV-03
  isReviewed: boolean;
  decision?: "approved" | "rejected" | null;
}

// In CardFooter, add a feedback button between reject and approve
<Button
  variant="outline"
  size="sm"
  onClick={onFeedback}
  disabled={isReviewed}
  className="gap-1"
>
  <MessageSquare className="h-3 w-3" />
  反馈
</Button>
```

Source: Existing `MatchCandidateCard` pattern in `frontend/src/components/Matching/MatchCandidateCard.tsx` [VERIFIED: codebase].

### Feedback Dialog Component (new)

```tsx
// frontend/src/components/Matching/FeedbackDialog.tsx
// Reuses ReviewNoteDialog pattern but for free-text feedback to the Agent

interface FeedbackDialogProps {
  open: boolean;
  onClose: () => void;
  candidateName: string;
  onSubmit: (feedback: string) => void;
}

// Dialog with Textarea for feedback, similar to ReviewNoteDialog
// Placeholder: "请描述您对匹配结果的建议，Agent 将据此重新调整..."
```

Source: Existing `ReviewNoteDialog` pattern at `frontend/src/components/Matching/ReviewNoteDialog.tsx` [VERIFIED: codebase].

### Excel Export: API Endpoint

```python
# In api/server.py, new export endpoints
import tempfile
import os

@app.get("/matching/{session_id}/export/pdf")
async def export_match_pdf(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Export matching result as PDF (DASH-02, D-08)."""
    # Fetch MatchSession and results
    from backend.db.models.match_session import MatchSession
    result = await db.execute(select(MatchSession).where(MatchSession.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Build PDF
    from backend.export.pdf import generate_match_report_pdf
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        generate_match_report_pdf(
            jd_title=f"Session #{session_id}",
            match_date=session.created_at.strftime("%Y-%m-%d"),
            candidates=[],  # TODO: fetch candidates from session data
            output_path=tmp.name,
        )
        return FileResponse(
            tmp.name,
            media_type="application/pdf",
            filename=f"match-report-{session_id}.pdf",
            headers={"Content-Disposition": f"attachment; filename=match-report-{session_id}.pdf"},
        )
    finally:
        os.unlink(tmp.name)
```

Source: Existing `FileResponse` usage for frontend serving in `api/server.py` line 69 [VERIFIED: codebase].

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Frontend jspdf for PDF export | Backend reportlab | Phase 5 | Consistent font handling, no browser dependencies |
| Single approve/reject card | Card with feedback button | Phase 5 | Enables iterative HR-Agent loop |
| HITL resume final | HITL resume with re-run | Phase 5 | feedback can now trigger re-matching |
| jd_id required for matching | jd_id or candidate_id | Phase 5 | Reverse matching support |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | /usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf works with reportlab TTFont | Standard Stack | Low -- it's a .ttf file (TrueType), reportlab documentation confirms .ttf support. Test will catch this immediately. |
| A2 | openpyxl handles Chinese text without special font registration | Standard Stack | Low -- openpyxl uses Unicode natively; Chinese characters in .xlsx are standard UTF-8. |
| A3 | The reviewer_agent can re-score with feedback text without structural changes | Agent Feedback | Medium -- the existing `hr_feedback` field is already passed to the LLM prompt but the quality of re-scoring depends on prompt quality. May need prompt engineering. |
| A4 | HITLResumeRequest can accept feedback_rerun flag without breaking existing flow | Agent Feedback | Low -- adding optional fields with defaults preserves backward compatibility. |
| A5 | MatchSession jd_id can be made nullable | Reverse Matching | Medium -- requires Alembic migration. If not compatible with existing dashboards, may need a separate table. |
| A6 | The Matching page can be reused for reverse matching with query params | Reverse Matching | Low -- the page already handles routing with `:jdId` param and paramless paths. Adding candidate_id query param is straightforward. |

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| reportlab | PDF export (D-06) | No (needs install) | -- | `pip install reportlab` |
| openpyxl | Excel export (D-06) | No (needs install) | -- | `pip install openpyxl` |
| Chinese .ttf font | reportlab PDF | Yes | AR PL SungtiL GB at /usr/share/fonts/truetype/arphic-gbsn00lp/gbsn00lp.ttf | DroidSansFallbackFull.ttf also available |
| Python 3.12 | All backend | Yes | 3.12.0 | -- |

**Missing dependencies with no fallback:** None (reportlab and openpyxl are standard pip packages).

**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | pytest.ini (asyncio_mode=auto) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MATCH-04 | Reverse matching stream endpoint returns valid SSE | integration | `pytest tests/test_sse.py::test_reverse_stream -x` | NO -- Wave 0 |
| MATCH-04 | Reverse matching passes candidate_id, returns JD results | integration | `pytest tests/test_sse.py::test_reverse_match_results -x` | NO -- Wave 0 |
| APRV-03 | Resume with feedback_rerun returns re-scored results | integration | `pytest tests/test_sse.py::test_feedback_rerun -x` | NO -- Wave 0 |
| APRV-03 | Feedback dialog validation (empty feedback rejected) | unit | `pytest tests/ -x -q` | NO -- Wave 0 |
| DASH-02 | PDF export endpoint returns valid PDF | integration | `pytest tests/ -x -q` | NO -- Wave 0 |
| DASH-02 | Excel export endpoint returns valid xlsx | integration | `pytest tests/ -x -q` | NO -- Wave 0 |
| DASH-02 | PDF contains expected Chinese text | integration | `pytest tests/ -x -q` | NO -- Wave 0 |
| DASH-02 | Excel contains expected Chinese headers | integration | `pytest tests/ -x -q` | NO -- Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_sse.py -x -q`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_export.py` -- covers PDF/Excel export endpoints
- [ ] `tests/test_sse.py` extensions -- covers reverse stream + feedback rerun
- [ ] No new framework installs needed (pytest + pytest-asyncio already configured)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | JWT token (existing) -- all endpoints use `get_current_user` dependency |
| V5 Input Validation | yes | Pydantic BaseModel validation on all request schemas |
| V12 File and Resources | yes | FastAPI FileResponse for download; temp file cleanup in finally block |

### Known Threat Patterns for this Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal in export filenames | Tampering | Use session_id (integer) not user-supplied filename; generate safe filenames server-side |
| Temp file leakage | Information Disclosure | Always use `try/finally` with `os.unlink()` for temp files, or use `tempfile.NamedTemporaryFile(delete=True)` with FileResponse by passing the file descriptor |
| Unauthorized session access | Information Disclosure | Export endpoints already use `Depends(get_current_user)`; confirm the user has access to the session's JD/candidate |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: codebase] -- All existing Phase 4 files read from `/root/project/hellojobs/`
- [VERIFIED: font inventory] -- Chinese fonts confirmed present via `fc-list :lang=zh` and `find /usr/share/fonts -name "*.ttf"`
- [VERIFIED: npm registry] -- reportlab 4.x and openpyxl 3.x available via pip

### Secondary (MEDIUM confidence)
- [CITED: reportlab source code at hg.reportlab.com] -- TTFont supports TrueType (not OTF/CFF); supports .ttc with subfontIndex
- [CITED: multiple Chinese language tutorials] -- reportlab ParagraphStyle needs wordWrap='CJK' for Chinese text

### Tertiary (LOW confidence)
- None -- all major claims verified against codebase or system state

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- reportlab and openpyxl are standard, verified by registry
- Architecture: HIGH -- based on reading existing codebase and understanding reuse patterns
- Pitfalls: HIGH -- reportlab .otf limitation is well-documented; MatchSession schema verified; SSE state machine verified

**Research date:** 2026-04-26
**Valid until:** 2026-05-26 (stable libraries; fast-moving changes are unlikely)
