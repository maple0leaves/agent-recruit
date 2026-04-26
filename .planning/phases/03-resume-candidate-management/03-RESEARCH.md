# Phase 3: Resume & Candidate Management - Research

**Researched:** 2026-04-26
**Domain:** File upload, text extraction, resume parsing, candidate CRUD, pipeline state machine
**Confidence:** HIGH

## Summary

Phase 3 adds the ability for HR to upload PDF/Word resumes, have them automatically parsed by the existing Agent, and track candidates through a 5-state pipeline. The phase spans backend (file upload + text extraction + Agent integration + candidate CRUD), frontend (upload UI + list/detail pages + pipeline controls), and a new Alembic migration.

**Primary recommendation:** Build backend-first: Candidate model + migration + upload endpoint (with Agent parse integration) + CRUD/status endpoints, then frontend: upload component + table + detail page + pipeline controls. Reuse JD CRUD patterns and test structure exactly from Phase 2.

**Key technical requirement:** `python-docx` must be installed for Word (.doc/.docx) support. The existing Agent tool `analyze_resume` in `agent/tools.py` already handles LLM-based parsing via `_get_resume_parser().invoke(RESUME_PARSE_PROMPT)`. The upload endpoint saves file -> extracts text (PDF via PyMuPDF, Word via python-docx) -> calls `analyze_resume` synchronously -> creates Candidate record.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Reuse existing LangGraph Agent resume parsing logic, do not create independent parse function
- **D-02:** Accept PDF and Word (.doc/.docx) format, single file max 10MB
- **D-03:** Sync parsing -- parse immediately after upload (3-10 seconds), return Candidate object with parsed results
- **D-04:** Show parse preview with extracted fields (name/skills/education/experience), HR can manually edit
- **D-05:** Parse failure does not block flow -- return partial success + warning, HR can manually fill all fields
- **D-06:** Standard fields: name (str), email (str, optional), phone (str, optional), skills (str, comma-separated), education (str), experience (str, long text), status (enum), resume_file_path (str), status_note (str), parsed_at (datetime), created_at, updated_at
- **D-07:** Resume files stored on local disk (`data/resumes/` directory), DB stores file path only, no BLOB
- **D-08:** Pipeline status enum: new / screening / interview / hired / rejected
- **D-09:** Status change requires note (status_note) is required
- **D-10:** Table layout (shadcn Table, consistent with JD list), columns: name, skills, status, upload date
- **D-11:** Search/filter: name fuzzy search + skill keyword search + status filter
- **D-12:** Detail page single-page scroll layout -- parsed data area + match history area (placeholder) + status actions area. Clicking list row enters edit mode directly.
- **D-13:** Match history area shows "no match records yet" placeholder (Phase 4 will populate)
- **D-14:** State machine: new -> screening -> interview -> hired | rejected
- **D-15:** hired and rejected are terminal states, irreversible
- **D-16:** Each status change requires filling notes (status_note), required
- **D-17:** No delete -- candidate records (including rejected) always retained

### Carried Forward from Phase 1 & 2

- SQLite + SQLAlchemy async + Alembic (Candidate model and migration reuse this pattern)
- FastAPI Depends() auth pattern -- all candidate endpoints mount `get_current_user`
- React 19 + Vite + TypeScript + Tailwind v4 + shadcn/ui (Table/Form/Dialog/Badge)
- TanStack Query (useQuery/useMutation) + axios withCredentials
- Dark sidebar layout, `/candidates` route already reserved
- Server-side search/filter + pagination (20 items/page) -- consistent with JD list
- Existing Agent parse capability (`agent/schemas.py` has CandidateInfo schema)

### Claude's Discretion

- Resume file storage directory name (recommended `data/resumes/`)
- Parse timeout specific seconds
- Candidate-to-resume file one-to-one vs. one-to-many relationship
- Upload progress indicator UI details
- Detail page area layout order and spacing

### Deferred Ideas (OUT OF SCOPE)

- Async resume parsing (background task + polling/SSE) -- Phase 3 uses sync parsing
- Batch resume upload (multiple files at once) -- v2 scope (RES-06)
- Candidate delete -- current only retain, never delete
- Resume files stored in DB (BLOB) -- currently stored as local disk path
- Pipeline finer-grained states (phone_screen, technical_test, etc.) -- current 5 states sufficient
- Candidate avatar/photo extraction -- beyond current parse scope
- Candidate card layout -- list uses standard table
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RES-01 | HR can upload resume (PDF/Word) | FastAPI UploadFile + multipart/form-data; text extraction via PyMuPDF/pdfplumber (PDF) and python-docx (Word); file saved to `data/resumes/` |
| RES-02 | System auto-parses resume, extracts name/skills/education/experience | `analyze_resume` tool in `agent/tools.py` wraps LLM call with structured output `CandidateInfo`; invoked synchronously with extracted resume text |
| RES-03 | HR can view candidate detail (parse result, match history, current status) | Single-page scroll layout: parsed data section (editable), match history placeholder, pipeline status controls |
| RES-04 | HR can search candidate DB (by name, skill, status) | SQLAlchemy `ilike()` chained filter + status filter; same server-side search/pagination pattern as JD list |
| RES-05 | Candidate status tracking (new -> screening -> interview -> hired/rejected) | 5-state enum; dict-based transition validation (same pattern as JDStatus); terminal states irreversible; status_note required on all transitions |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Resume file save (local disk) | API / Backend | -- | File written to `data/resumes/` from server process; path stored in DB |
| Text extraction (PDF/Word) | API / Backend | -- | PyMuFPDF for PDF, python-docx for Word; needs server-side libraries |
| Resume parsing via Agent | API / Backend | -- | Calls `analyze_resume` tool directly (sync import); returns structured CandidateInfo |
| Candidate CRUD | API / Backend | -- | SQLAlchemy async queries; same pattern as JD CRUD |
| Pipeline state machine | API / Backend | -- | Dict-based transition validation; enforced in PATCH /candidates/{id}/status |
| File size validation (10MB) | API / Backend | -- | Check `len(await file.read())` before processing |
| Candidate list with search/filter | API / Backend | Browser / Client | Server-side SQL filtering + pagination; frontend renders results |
| Candidate table display | Browser / Client | -- | shadcn Table, same @tanstack/react-table pattern as JDTable |
| File upload widget | Browser / Client | -- | input[type=file] with accept=".pdf,.doc,.docx"; optional drag-drop |
| Upload progress indication | Browser / Client | -- | axios `onUploadProgress` callback |
| Candidate detail/edit page | Browser / Client | -- | Single-page scroll; inline edit via react-hook-form + Zod |
| Pipeline status controls | Browser / Client | API / Backend | Frontend triggers PATCH; server enforces valid transitions |
| Match history placeholder | Browser / Client | -- | Static "no records yet" text; Phase 4 populates |
| Resume file storage location | Database / Storage | -- | `resume_file_path` column stores relative path; actual file on disk |

---

## Standard Stack

### Core -- Backend Additions

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-docx | latest | Word (.docx) text extraction | Standard library for reading Word documents; extracts plain text for LLM parsing [VERIFIED: PyPI] |
| PyMuPDF (fitz) | 1.27.2.2 | PDF text extraction | Already installed; used by existing `_read_resume_file_uncached` in agent/tools.py [VERIFIED: pip show] |
| python-multipart | 0.0.26 | Form data parsing | Already installed; required by FastAPI for file upload [VERIFIED: pip show] |

**No new frontend packages needed.** Existing stack (axios, @tanstack/react-table, react-hook-form, zod, shadcn/ui components) fully covers Phase 3 requirements.

### Core -- Frontend (Existing, Confirmed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-table | 8.21.3 | Table rendering | Already installed; used by JDTable; CandidateTable follows same pattern |
| react-hook-form | 7.74.0 | Form state management | Already installed; used by JDForm; CandidateForm follows same pattern |
| zod | 4.3.6 | Schema validation | Already installed; CandidateForm Zod schema follows JDForm pattern |
| axios | 1.15.2 | HTTP client | Already installed; file upload via FormData + onUploadProgress |
| @tanstack/react-query | 5.100.5 | Server state | Already installed; useQuery/useMutation for candidate CRUD hooks |

### Already Installed shadcn/ui Components (Available for Phase 3)

All from frontend/src/components/ui/:
- table, button, input, card, badge, dialog, form, select, textarea, dropdown-menu, skeleton, label, popover, separator

No new shadcn/ui components need to be added for Phase 3.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| python-docx | textract, docx2txt | python-docx is the most maintained; textract is unmaintained; docx2txt is a simpler subset |
| Manual file size check | FastAPI max_file_size middleware | Manual check is simpler (one `if` statement); FastAPI doesn't have built-in max_file_size |
| Sync Agent invoke | Async subprocess/thread | Sync direct import is simplest (3-10s); matches D-03 sync requirement |
| python-pptx | -- | Not needed -- D-02 specifies only PDF and Word formats |

### Installation

```bash
# Backend additions (to requirements.txt)
pip install python-docx
```

**Version verification [VERIFIED: pip show / pip index]:**
- PyMuPDF 1.27.2.2 installed
- python-multipart 0.0.26 installed
- python-docx not installed -- must be added

---

## Architecture Patterns

### System Architecture Diagram

```
[Browser: Candidates SPA]
     |
     | File via input[type=file] → FormData
     | POST /candidates/upload  (multipart/form-data)
     | GET  /candidates         (list + search + filter)
     | GET  /candidates/{id}    (detail)
     | PUT  /candidates/{id}    (update parsed fields)
     | PATCH /candidates/{id}/status  (pipeline transition)
     v
[FastAPI: Candidate Routes]
     |
     |-- D-01: Direct import analyze_resume from agent.tools
     |-- D-02: 10MB file size check on UploadFile
     |-- D-03: Sync parsing (3-10s, blocking in executor)
     |-- D-05: try/except on parse → partial success model
     |
     v
[File System: data/resumes/]
     |
     |-- D-07: Save file to local disk
     |-- Path stored in Candidate.resume_file_path
     |
     v
[Agent: analyze_resume tool]
     |
     |-- D-01: analyze_resume.invoke({"resume_text": text})
     |-- Returns CandidateInfo Pydantic model
     |-- LRU cached (_analyze_resume_cached)
     |
     v
[LangGraph LLM Call]
     |
     |-- RESUME_PARSE_PROMPT + text → ChatOpenAI → CandidateInfo
     |-- Returns: name, email, skills, years_of_experience, education, summary
     |
     v
[SQLite: candidates table]
     |
     |-- D-06: Standard fields + status enum + metadata
     |-- D-08: 5 pipeline states
     |-- D-14~D-17: State machine enforcement
```

### Recommended Project Structure

```
backend/
├── api/
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py              (existing)
│   │   ├── jd.py                (existing)
│   │   └── candidate.py         NEW: upload + CRUD + status endpoints
│   └── deps.py                  (existing)
├── db/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              (existing)
│   │   ├── jd.py                (existing)
│   │   └── candidate.py         NEW: Candidate ORM model + enums
│   └── engine.py                (existing)

frontend/
├── src/
│   ├── api/
│   │   ├── client.ts            (existing)
│   │   ├── jd.ts                (existing)
│   │   └── candidates.ts        NEW: API functions (upload, list, get, update, updateStatus)
│   ├── hooks/
│   │   ├── useAuth.ts           (existing)
│   │   ├── useJDs.ts            (existing)
│   │   └── useCandidates.ts     NEW: TanStack Query hooks
│   ├── types/
│   │   ├── jd.ts                (existing)
│   │   └── candidate.ts         NEW: Candidate types + enums
│   ├── components/
│   │   ├── JDs/                 (existing)
│   │   └── Candidates/          NEW:
│   │       ├── CandidateTable.tsx      (table list, like JDTable)
│   │       ├── CandidateDetail.tsx     (single-page scroll detail/edit)
│   │       ├── CandidateFilterBar.tsx  (search + status filter)
│   │       ├── CandidateUpload.tsx     (file upload widget)
│   │       ├── PipelineStatusBadge.tsx (status badge like JDStatusBadge)
│   │       └── PipelineActions.tsx     (status transition controls)
│   ├── pages/
│   │   ├── Candidates.tsx       MODIFIED: replace placeholder with full page
│   │   └── ...                  (existing)

data/
├── resumes/                     (existing, add to .gitignore)
│   ├── *.pdf                    (sample data + user uploads)
│   └── *.docx                   (user uploads)

tests/
├── conftest.py                  (existing)
├── test_auth.py                 (existing)
├── test_jd.py                   (existing)
└── test_candidate.py            NEW: candidate CRUD + upload + status tests
```

### Pattern 1: Resume Upload + Parse Pipeline

**What:** Accept multipart/form-data POST with a file, validate format and size, save to disk, extract text, call Agent to parse, handle parse failures gracefully, return Candidate record.

**When to use:** POST /candidates/upload endpoint (D-01 through D-05).

**Research findings -- Agent integration:**

The existing `analyze_resume` tool in `agent/tools.py` is a `@tool`-decorated function that:
1. Takes `resume_text: str` as input
2. Hashes the text for LRU caching (`_analyze_resume_cached`)
3. Calls `_get_resume_parser()` which is a singleton LLM (ChatOpenAI) bound to `CandidateInfo` structured output schema
4. Returns JSON string of `CandidateInfo`

```python
# agent/tools.py (existing) -- direct call pattern
from agent.tools import analyze_resume

candidate_json = analyze_resume.invoke({"resume_text": extracted_text})
# candidate_json is a JSON string of CandidateInfo
```

**Text extraction logic needed:**
```python
# For PDF (reuse existing pattern from api/server.py:_upload_resume, line 186-196)
import fitz  # PyMuPDF
doc = fitz.open(stream=io.BytesIO(raw_bytes), filetype="pdf")
text = "\n".join(page.get_text() for page in doc)

# For Word (.docx) -- new with python-docx
from docx import Document
doc = Document(io.BytesIO(raw_bytes))
text = "\n".join(paragraph.text for paragraph in doc.paragraphs)

# For .doc (legacy Word) -- limited support
# python-docx does NOT support .doc format (only .docx).
# Options:
#   1. Reject .doc with clear error message: "请上传 .docx 格式"
#   2. Try antiword/libreoffice conversion (too complex)
# Recommendation: Accept .docx only, reject .doc with helpful message
```

**Upload endpoint structure:**
```python
# backend/api/routes/candidate.py
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import io, os, uuid
from datetime import datetime, timezone

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}  # D-02: PDF and Word

@router.post("/candidates/upload")
async def upload_candidate(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    # 1. Validate file
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 PDF 和 Word (.docx) 格式")
    
    raw = await file.read()
    if len(raw) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
    if not raw:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    # 2. Save file to disk (D-07)
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join("data/resumes", safe_filename)
    os.makedirs("data/resumes", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(raw)
    
    # 3. Extract text
    text = _extract_text(raw, ext)
    
    # 4. Call Agent to parse (D-01, D-03)
    warnings = []
    parsed = CandidateInfo()  # empty fallback (D-05)
    try:
        candidate_json = analyze_resume.invoke({"resume_text": text})
        parsed = CandidateInfo.model_validate_json(candidate_json)
    except Exception as e:
        warnings.append(f"简历解析未完全成功: {str(e)}")
        # D-05: partial success, continue with empty CandidateInfo
    
    # 5. Create Candidate record
    candidate = Candidate(
        name=parsed.name or _derive_name(file.filename),
        email=parsed.email or "",
        phone="",
        skills=", ".join(parsed.skills) if parsed.skills else "",
        education=parsed.education or "",
        experience=parsed.summary or "",
        status=CandidateStatus.NEW,
        resume_file_path=file_path,
        status_note="",
        parsed_at=datetime.now(timezone.utc) if parsed.name else None,
    )
    db.add(candidate)
    await db.commit()
    await db.refresh(candidate)
    
    # 6. Return result with warnings if any
    result = _candidate_to_dict(candidate)
    if warnings:
        result["warnings"] = warnings
    return result
```

**Key insight -- `analyze_resume` is sync and slow (3-10s):** The upload endpoint will appear to "hang" for 3-10 seconds during parsing. D-03 explicitly accepts this (sync parsing). The endpoint should be `async def` with `await asyncio.to_thread()` wrapping the sync Agent call to avoid blocking the event loop. See Phase 1 research for `asyncio.to_thread()` pattern.

### Pattern 2: Candidate CRUD (Following JD Pattern)

**What:** REST endpoints for listing, getting, and updating candidates -- identical structure to JD routes in `backend/api/routes/jd.py`.

**When to use:** All CRUD endpoints (D-06, D-10, D-11).

**Pattern reference from jd.py:**
- `list_candidates`: GET /candidates with `page`, `page_size`, `keyword`, `status` query params. Same `or_(field.ilike(pattern))` chained filter pattern. Sort by `created_at.desc()`.
- `get_candidate`: GET /candidates/{id} returns single candidate with all fields.
- `update_candidate`: PUT /candidates/{id} updates all writable fields (name, email, phone, skills, education, experience).

**Search logic (D-11):**
```python
if keyword:
    pattern = f"%{keyword}%"
    base_query = base_query.where(
        or_(
            Candidate.name.ilike(pattern),
            Candidate.skills.ilike(pattern),
        )
    )
if status:
    base_query = base_query.where(Candidate.status == status)
```

### Pattern 3: Pipeline State Machine (Following JD Status Pattern)

**What:** 5-state lifecycle enforced by a dict-based transition map. Terminal states (hired, rejected) are irreversible. All transitions require `status_note`.

**When to use:** PATCH /candidates/{id}/status (D-08, D-09, D-14 through D-17).

**State machine definition:**
```python
# backend/db/models/candidate.py
class CandidateStatus(str, enum.Enum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    HIRED = "hired"
    REJECTED = "rejected"

_VALID_TRANSITIONS: dict[CandidateStatus, list[CandidateStatus]] = {
    CandidateStatus.NEW: [CandidateStatus.SCREENING, CandidateStatus.REJECTED],
    CandidateStatus.SCREENING: [CandidateStatus.INTERVIEW, CandidateStatus.REJECTED],
    CandidateStatus.INTERVIEW: [CandidateStatus.HIRED, CandidateStatus.REJECTED],
    CandidateStatus.HIRED: [],       # terminal (D-15)
    CandidateStatus.REJECTED: [],    # terminal (D-15)
}
```

**Status update endpoint (following JD pattern):**
```python
@router.patch("/candidates/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: int,
    data: StatusUpdate,  # { status: str, status_note: str }
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    # 1. Fetch candidate
    # 2. Validate transition
    # 3. Validate status_note is non-empty (D-09, D-16)
    # 4. Apply new status
    # 5. Return updated candidate
```

### Pattern 4: File Upload UI in Frontend

**What:** A clean upload widget with drag-and-drop support, file type validation, and progress indicator.

**When to use:** Candidates page header area, upload trigger button that opens inline upload area or simple direct upload.

**No new npm packages needed.** Standard HTML5 `input[type=file]` with `accept=".pdf,.docx"` + axios FormData post + `onUploadProgress` for feedback.

```typescript
// axios file upload with progress (from axios docs)
const uploadResume = async (file: File, onProgress?: (pct: number) => void) => {
  const formData = new FormData();
  formData.append("file", file);
  
  const res = await apiClient.post("/candidates/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return res.data;
};
```

### Anti-Patterns to Avoid

- **Blocking event loop during parse:** `analyze_resume.invoke()` is synchronous and takes 3-10s. Must wrap in `await asyncio.to_thread()` within an `async def` handler. Do NOT use synchronous `def` handlers for upload endpoints.
- **Missing python-docx:** The upload endpoint crashes on Word files if `python-docx` is not installed. Must be explicitly added to requirements.txt.
- **Hardcoded file paths:** Use `os.path.join("data/resumes", ...)` (or `Path(...)`) not `f"data/resumes/{name}"` for cross-platform correctness. Using the config's already-defined `RESUME_DIR` variable is even better.
- **Re-extracting text from PDF for vector store:** The upload endpoint just needs to extract text once (for Agent parsing) and save the file. The vector store rebuild is a separate concern (handled by admin endpoints).
- **Duplicate resumes:** Consider whether re-uploading the same file should create a new candidate or reject. Per D-17 (no delete), duplicates are allowed but should be flagged.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF text extraction | Manual PDF parsing | PyMuPDF (fitz) | Already installed; handles CJK characters, PDF variants; used by existing code |
| Word text extraction | Manual .docx parsing | python-docx | De facto standard; handles paragraphs, tables, formatting |
| File upload decoding | Manual multipart parsing | FastAPI UploadFile | FastAPI handles streaming, buffering, encoding automatically |
| Resume parsing LLM | Custom extraction logic | Agent's analyze_resume tool | D-01 mandates reuse; already has structured output + caching |
| Pipeline state machine | Full workflow engine library | Simple dict lookup | 5 states, no branching; dict is clearer than a library (same pattern as JDStatus) |
| Status badge component | Custom badge CSS | shadcn/ui Badge | Already installed; D-10 says consistent with JD table style |
| Table sort/filter | Manual table state | @tanstack/react-table | Already installed and used by JDTable |

**Key insight:** The existing architecture has established patterns for everything Phase 3 needs. The only genuinely new technical addition is `python-docx` for Word text extraction. Every other concern -- file upload, text extraction, Agent parsing, CRUD, state machine, table, form -- is a direct application of an existing pattern.

---

## Common Pitfalls

### Pitfall 1: python-docx Not Installed

**What goes wrong:** Upload endpoint returns 500 error when user uploads a .docx file, because `import docx` fails.

**Why it happens:** `python-docx` is not in `requirements.txt` and not installed in the environment. The existing requirements only have `pypdf` and `pymupdf` for PDF.

**How to avoid:** Add `python-docx` to `requirements.txt` in the Phase 3 plan. Verify with `pip install python-docx`.

**Warning signs:** `ModuleNotFoundError: No module named 'docx'` in logs on .docx upload.

### Pitfall 2: blocking the Event Loop with Sync Agent Parse

**What goes wrong:** The upload endpoint hangs for 3-10 seconds, and during that time all other API endpoints (health, auth, JD) become unresponsive.

**Why it happens:** If the upload handler is `def` (sync) or if `async def` calls `analyze_resume.invoke()` directly without `await asyncio.to_thread()`, the sync LLM call blocks the event loop. This is the same pitfall documented in Phase 1 (Pitfall 2).

**How to avoid:** Use `async def` for the upload handler and wrap `analyze_resume.invoke()` in `await asyncio.to_thread()`:

```python
import asyncio

async def upload_candidate(...):
    # ... save file, extract text ...
    
    def _parse():
        return analyze_resume.invoke({"resume_text": text})
    
    try:
        candidate_json = await asyncio.to_thread(_parse)
        parsed = CandidateInfo.model_validate_json(candidate_json)
    except Exception as e:
        warnings.append(f"解析失败: {str(e)}")
        # D-05: continue with empty fallback
```

**Warning signs:** Other endpoints timeout while uploading a resume; server metrics show event loop lag.

### Pitfall 3: Text Extraction Failure on Scanned PDFs

**What goes wrong:** Upload succeeds but `text` is empty string. Agent returns empty CandidateInfo. User sees "parse failed" with no actionable data.

**Why it happens:** PyMuPDF cannot extract text from scanned/image-based PDFs (they contain only images, no selectable text). The existing code already handles this (`detail = "未能从文件中提取到文字内容（可能是扫描版图片 PDF，暂不支持）"`).

**How to avoid:** Check extracted text length. If empty (or very short < 20 chars), return a clear message in `warnings` indicating the PDF might be scanned. Do NOT crash -- per D-05, user can manually fill fields.

**Warning signs:** `parsed_at` is `None` (not set when parse fails); empty skills/education; name derived from filename.

### Pitfall 4: .doc (Legacy Word) Format Confusion

**What goes wrong:** User uploads `resume.doc` and gets an error. The error message is incomprehensible.

**Why it happens:** `python-docx` only supports `.docx` (Office Open XML), not the legacy binary `.doc` format. Users commonly have `.doc` files from older Word versions.

**How to avoid:** Accept `.docx` only with a clear error message for `.doc`: "不支持 .doc 格式，请将文件另存为 .docx 格式后重新上传。" Do NOT attempt to parse .doc with python-docx (it will silently return empty or corrupt data).

### Pitfall 5: Large File Upload Without Size Check

**What goes wrong:** User uploads a 500MB file, consuming all server memory when `await file.read()` loads it into RAM.

**Why it happens:** FastAPI's `UploadFile.read()` reads the entire file into memory. Without a pre-read check, there's no way to reject before the buffer is allocated.

**How to avoid:** Check the `Content-Length` header before reading, or read in chunks and reject if exceeding limit. Simple approach: read and check length in one step:

```python
raw = await file.read()
if len(raw) > MAX_FILE_SIZE:
    raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
```

This still reads the whole file into memory, but for 10MB files this is acceptable. If stricter control is needed, use `file_size` from Content-Length header.

### Pitfall 6: TNTS -- Status Transition Without Note

**What goes wrong:** User changes candidate status but the form doesn't require a note. D-09 and D-16 mandate that `status_note` is required on every status change.

**How to avoid:** The backend PATCH endpoint must validate that `status_note` is non-empty before applying the transition. The frontend form should also enforce this via Zod `z.string().min(1)`. Both layers enforce it.

### Warning Signs Checklist

- [ ] `async def` upload handler without `await asyncio.to_thread()` for Agent call (blocks event loop)
- [ ] `python-docx` not in requirements.txt (Word upload crashes)
- [ ] No file size check before `file.read()` (memory blowup on large files)
- [ ] No `status_note` validation on status PATCH (D-09, D-16 violation)
- [ ] `.doc` accepted alongside `.docx` (will fail silently with python-docx)
- [ ] `data/resumes/` not in `.gitignore` (uploads committed to git)
- [ ] Sync `def` handler for upload (same blocking issue as Pitfall 2)
- [ ] No `try/except` around `analyze_resume.invoke()` (D-05: failure should not block)
- [ ] Hardcoded `new` status in upload handler instead of using `CandidateStatus.NEW` enum

---

## Code Examples

### Candidate Model

```python
# backend/db/models/candidate.py
"""Candidate ORM model with 5-state pipeline enum."""
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, func
from backend.db.engine import Base


class CandidateStatus(str, enum.Enum):
    NEW = "new"
    SCREENING = "screening"
    INTERVIEW = "interview"
    HIRED = "hired"
    REJECTED = "rejected"


class Candidate(Base):
    """Candidate model -- core entity for Phase 3 resume management."""

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(200), nullable=False, default="")
    phone = Column(String(50), nullable=False, default="")
    skills = Column(String(2000), nullable=False, default="")
    education = Column(String(500), nullable=False, default="")
    experience = Column(Text, nullable=False, default="")
    status = Column(Enum(CandidateStatus), nullable=False, default=CandidateStatus.NEW, index=True)
    resume_file_path = Column(String(500), nullable=False, default="")
    status_note = Column(String(1000), nullable=False, default="")
    parsed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
```

### Candidate CRUD Routes

```python
# backend/api/routes/candidate.py
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import get_current_user, get_db
from backend.db.models.candidate import Candidate, CandidateStatus
from agent.tools import analyze_resume

router = APIRouter(prefix="/candidates", tags=["candidates"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


# ── Pydantic Schemas ──────────────────────────────────────────────────────────

class CandidateResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: str
    skills: str
    education: str
    experience: str
    status: str
    resume_file_path: str
    status_note: str
    parsed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CandidateListResponse(BaseModel):
    items: list[CandidateResponse]
    total: int
    page: int
    page_size: int


class CandidateUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: str | None = None
    education: str | None = None
    experience: str | None = None


class StatusUpdate(BaseModel):
    status: str
    status_note: str

    @field_validator("status")
    @classmethod
    def validate_status_value(cls, v: str) -> str:
        valid_values = {s.value for s in CandidateStatus}
        if v not in valid_values:
            raise ValueError(f"无效的状态值: {v}")
        return v

    @field_validator("status_note")
    @classmethod
    def note_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("状态变更是备注必填")
        return v.strip()


# ── State Machine (D-14, D-15) ────────────────────────────────────────────────

_VALID_TRANSITIONS: dict[CandidateStatus, list[CandidateStatus]] = {
    CandidateStatus.NEW: [CandidateStatus.SCREENING, CandidateStatus.REJECTED],
    CandidateStatus.SCREENING: [CandidateStatus.INTERVIEW, CandidateStatus.REJECTED],
    CandidateStatus.INTERVIEW: [CandidateStatus.HIRED, CandidateStatus.REJECTED],
    CandidateStatus.HIRED: [],
    CandidateStatus.REJECTED: [],
}


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get("")
async def list_candidates(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Filter by pipeline status"),
    keyword: str | None = Query(None, description="Search in name, skills"),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List candidates with pagination and search/filter (RES-04, D-11)."""
    base_query = select(Candidate)

    if status:
        base_query = base_query.where(Candidate.status == status)
    if keyword:
        pattern = f"%{keyword}%"
        base_query = base_query.where(
            or_(Candidate.name.ilike(pattern), Candidate.skills.ilike(pattern))
        )

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    data_query = (
        base_query.order_by(Candidate.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await db.execute(data_query)).scalars().all()

    return CandidateListResponse(
        items=[CandidateResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/upload", status_code=201)
async def upload_candidate(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Upload resume, parse via Agent, create candidate record (RES-01, RES-02)."""
    # ... see Pattern 1 for full implementation ...
    pass


@router.get("/{candidate_id}")
async def get_candidate(
    candidate_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Get single candidate detail (RES-03)."""
    result = await db.execute(select(Candidate).where(Candidate.id == candidate_id))
    candidate = result.scalar_one_or_none()
    if not candidate:
        raise HTTPException(status_code=404, detail="候选人不存在")
    return CandidateResponse.model_validate(candidate)


@router.put("/{candidate_id}")
async def update_candidate(
    candidate_id: int,
    data: CandidateUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update candidate parsed fields (RES-03, D-04)."""
    # Fetch, update fields that are not None, commit, return
    pass


@router.patch("/{candidate_id}/status")
async def update_candidate_status(
    candidate_id: int,
    data: StatusUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update pipeline status with transition validation (RES-05, D-14~D-17)."""
    # Fetch, validate transition, apply, commit, return
    pass
```

### Candidate TanStack Query Hooks

```typescript
// frontend/src/hooks/useCandidates.ts
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchCandidates, uploadCandidate, updateCandidate, updateCandidateStatus } from "../api/candidates";
import type { CandidateListResponse, Candidate, CandidateUpdate } from "../types/candidate";

export interface CandidateFilters {
  page: number;
  pageSize: number;
  status?: string;
  keyword?: string;
}

export function useCandidates(filters: CandidateFilters) {
  return useQuery<CandidateListResponse>({
    queryKey: ["candidates", "list", filters],
    queryFn: () => fetchCandidates({
      page: filters.page,
      page_size: filters.pageSize,
      ...(filters.status && { status: filters.status }),
      ...(filters.keyword && { keyword: filters.keyword }),
    }),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useUploadCandidate() {
  const queryClient = useQueryClient();
  return useMutation<Candidate, Error, { file: File; onProgress?: (pct: number) => void }>({
    mutationFn: ({ file, onProgress }) => uploadCandidate(file, onProgress),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
    },
  });
}

export function useUpdateCandidate() {
  const queryClient = useQueryClient();
  return useMutation<Candidate, Error, { id: number; data: CandidateUpdate }>({
    mutationFn: ({ id, data }) => updateCandidate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
    },
  });
}

export function useUpdateCandidateStatus() {
  const queryClient = useQueryClient();
  return useMutation<Candidate, Error, { id: number; status: string; status_note: string }>({
    mutationFn: ({ id, status, status_note }) => updateCandidateStatus(id, status, status_note),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["candidates", "list"] });
    },
  });
}
```

### Pipeline Status Badge

```typescript
// frontend/src/components/Candidates/PipelineStatusBadge.tsx
import { Badge } from "@/components/ui/badge";

const STATUS_CONFIG: Record<string, { label: string; variant: "default" | "secondary" | "outline" | "destructive" }> = {
  new: { label: "新入库", variant: "outline" },
  screening: { label: "筛选中", variant: "secondary" },
  interview: { label: "面试", variant: "default" },
  hired: { label: "已录用", variant: "default" },
  rejected: { label: "不合适", variant: "destructive" },
};

export default function PipelineStatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || { label: status, variant: "outline" };
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
```

### Inline Candidate Detail Form (Click to Edit)

```typescript
// frontend/src/components/Candidates/CandidateDetail.tsx (conceptual)
// Single-page scroll layout showing:
// 1. Parsed data section with inline editing (react-hook-form)
// 2. Match history section with "暂无匹配记录" placeholder (D-13)
// 3. Pipeline status section with status transition controls (D-14~D-17)
//
// Clicking any parsed field enters edit mode (D-12)
// Status changes open a dialog requiring status_note (D-09, D-16)
//
// Pattern follows JDForm but without Dialog wrapper (inline, not modal):
// - useForm with zodResolver
// - Field segments: personal info, skills, education, experience
// - Save button triggers PUT /candidates/{id}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `api/server.py` /upload-resume returns raw text only | `/candidates/upload` returns full Candidate object | Phase 3 | Better UX -- single round trip instead of upload-then-create |
| Sample resumes manually placed in `data/resumes/` | User-uploaded resumes stored via API | Phase 3 | Need to add `data/resumes/` to .gitignore to avoid committing real resumes |
| Agent `analyze_resume` only used in full workflow | Directly invoked from upload endpoint | Phase 3 | Import pattern from agent.tools; sync call in async endpoint via asyncio.to_thread |

**Deprecated/outdated:**
- `/upload-resume` endpoint in `api/server.py` (returns text only) -- Phase 3 will create a new endpoint; the old one can remain for backward compatibility or be deprecated.

---

## Runtime State Inventory

> Not applicable -- Phase 3 is greenfield. No rename or refactor of existing state is involved. The `data/resumes/` directory already exists with sample files but is not affected by renaming operations.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PyMuPDF (fitz) | PDF text extraction | Yes | 1.27.2.2 | -- |
| python-multipart | Form data parsing | Yes | 0.0.26 | -- |
| python-docx | Word (.docx) text extraction | **No** | -- | Reject .docx with error message; PDF-only support |
| pypdf | Alternative PDF parsing | Yes | 6.10.2 | -- |
| Node.js | Frontend | Yes | 22.22.1 | -- |
| npm | Frontend packages | Yes | 10.9.4 | -- |

**Missing dependencies with no fallback:**
- python-docx: Must be installed for Word (.docx) support. No viable alternative -- this is the standard library for Word text extraction.

**Missing dependencies with fallback:**
- None -- all other dependencies are available.

---

## Validation Architecture

> `workflow.nyquist_validation` is enabled (`true` in `.planning/config.json`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio (existing in requirements.txt) |
| Config file | tests/conftest.py (existing) |
| Quick run command | `python -m pytest tests/test_candidate.py -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| RES-01 | Upload valid PDF returns 201 with CandidateResponse | integration | `pytest tests/test_candidate.py::TestUpload::test_upload_pdf_success -x` | Needs Wave 0 |
| RES-01 | Upload valid Word (.docx) returns 201 with CandidateResponse | integration | `pytest tests/test_candidate.py::TestUpload::test_upload_docx_success -x` | Needs Wave 0 |
| RES-01 | Upload file >10MB returns 400 | integration | `pytest tests/test_candidate.py::TestUpload::test_file_too_large -x` | Needs Wave 0 |
| RES-01 | Upload invalid format (.exe) returns 400 | integration | `pytest tests/test_candidate.py::TestUpload::test_invalid_format -x` | Needs Wave 0 |
| RES-01 | Upload without auth returns 401 | integration | `pytest tests/test_candidate.py::TestUpload::test_requires_auth -x` | Needs Wave 0 |
| RES-02 | Parse success populates name/skills/education/experience | integration | `pytest tests/test_candidate.py::TestUpload::test_parse_success -x` | Needs Wave 0 |
| RES-02 | Parse failure returns 201 with warnings + empty fields | integration | `pytest tests/test_candidate.py::TestUpload::test_parse_failure -x` | Needs Wave 0 |
| RES-03 | GET /candidates/{id} returns full candidate | integration | `pytest tests/test_candidate.py::TestCRUD::test_get_candidate -x` | Needs Wave 0 |
| RES-03 | PUT /candidates/{id} updates parsed fields | integration | `pytest tests/test_candidate.py::TestCRUD::test_update_candidate -x` | Needs Wave 0 |
| RES-04 | GET /candidates?keyword= filters correctly | integration | `pytest tests/test_candidate.py::TestList::test_search_by_name -x` | Needs Wave 0 |
| RES-04 | GET /candidates?status= filters correctly | integration | `pytest tests/test_candidate.py::TestList::test_filter_status -x` | Needs Wave 0 |
| RES-04 | GET /candidates paginates correctly | integration | `pytest tests/test_candidate.py::TestList::test_pagination -x` | Needs Wave 0 |
| RES-05 | PATCH status new->screening succeeds with note | integration | `pytest tests/test_candidate.py::TestStatus::test_valid_transition -x` | Needs Wave 0 |
| RES-05 | PATCH status to terminal state is irreversible | integration | `pytest tests/test_candidate.py::TestStatus::test_terminal_irreversible -x` | Needs Wave 0 |
| RES-05 | PATCH status without note returns 422 | integration | `pytest tests/test_candidate.py::TestStatus::test_requires_note -x` | Needs Wave 0 |
| RES-05 | PATCH invalid transition returns 400 | integration | `pytest tests/test_candidate.py::TestStatus::test_invalid_transition -x` | Needs Wave 0 |
| D-17 | DELETE /candidates/{id} returns 405 (not implemented) | integration | `pytest tests/test_candidate.py::TestLifecycle::test_no_delete -x` | Needs Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_candidate.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_candidate.py` -- candidate upload, CRUD, status tests (pattern follows test_jd.py)
- [ ] Test PDF fixture: A small valid PDF file for upload tests (can use a minimal generated PDF)
- [ ] Test .docx fixture: A minimal Word document for upload tests

---

## Security Domain

> `security_enforcement` is enabled by default (absent from config.json).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | All candidate endpoints use `Depends(get_current_user)` -- same as JD |
| V3 Session Management | yes | Same cookie-based pattern from Phase 1 |
| V4 Access Control | yes | JWT role field; optionally `Depends(require_role("recruiter"))` |
| V5 Input Validation | yes | Pydantic models for all request bodies; file type/size validation; status_note non-empty |
| V6 Cryptography | no | No encryption needed -- file storage path only; resume content not encrypted on disk |
| V12 File Uploads | yes | FastAPI UploadFile; 10MB limit; format whitelist (.pdf, .docx); content-type check |

### Known Threat Patterns for FastAPI + File Upload

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Large file upload DoS | Denial of Service | 10MB limit check before processing; Content-Length header check |
| Malicious file upload | Tampering | Format whitelist (.pdf, .docx); PyMuPDF and python-docx are safe parsers |
| Path traversal in filename | Tampering | Use UUID for saved filename (NOT user-provided filename): `f"{uuid4().hex}{ext}"` |
| Sensitive resume data leaked via git | Information Disclosure | Add `data/resumes/*` to `.gitignore` |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `analyze_resume.invoke({"resume_text": text})` is the correct sync invocation pattern | Code Examples / Pattern 1 | LOW: Verified by reading `agent/tools.py` line 123 -- `analyze_resume` is a `@tool` with signature `(resume_text: str) -> str` |
| A2 | `python-docx` is the correct library for Word (.docx) text extraction | Standard Stack | LOW: python-docx is the de facto standard; actively maintained on PyPI |
| A3 | `data/resumes/` should be added to `.gitignore` | File Structure / Security Domain | LOW: Currently tracked in git (36 sample files). Adding to .gitignore won't remove them from tracking; need `git rm --cached` if we want them untracked. Uploaded real resumes should never be committed. |
| A4 | .doc (legacy Word) is unsupported and should be rejected with clear message | Common Pitfalls | MEDIUM: Some users may have .doc files. Clear instructions to convert to .docx is acceptable. Adding antiword/libreoffice conversion is out of scope. |
| A5 | One-to-one relationship between candidate and resume file | Architecture | MEDIUM: D-06 has `resume_file_path` as single field. User discretion says this is Claude's discretion area -- one-to-one is simplest and matches the single-upload flow. |

---

## Open Questions (RESOLVED)

1. **python-docx version to install**
   - What we know: Not installed. Latest stable is 1.x.
   - What's unclear: Exact version to pin.
   - Recommendation: Run `pip install python-docx` or add to requirements.txt unpinned (`python-docx>=1.0.0`).

2. **Sample resume files in git**
   - What we know: `data/resumes/` has 36 committed sample resumes for testing.
   - What's unclear: Whether to keep them tracked (as test data) or fully gitignore them.
   - Recommendation: Add `data/resumes/*` to `.gitignore` for new uploads. Existing committed files remain tracked. User can decide later whether to remove them from history.

3. **Loading state duration for 3-10s parse**
   - What we know: RESUME_PARSE_PROMPT calls an LLM which takes 3-10 seconds.
   - What's unclear: Acceptable loading UX. A simple spinner for 10 seconds might feel slow.
   - Recommendation: Show a non-blocking progress bar or "正在智能解析简历..." message with a subtle spinner. Include the Parse Timeout in Claude's Discretion -- recommend 30 seconds as timeout.

4. **Test fixture for file upload**
   - What we know: Tests need actual PDF and .docx files to test upload endpoints.
   - What's unclear: Where to store test fixtures.
   - Recommendation: Create `tests/fixtures/` with a minimal 1-page PDF and a minimal .docx (can be generated programmatically in conftest or committed as fixtures).

---

## Sources

### Primary (HIGH confidence)

| Source | What Was Verified |
|--------|-------------------|
| [VERIFIED: codebase] | `agent/tools.py:120-124` - `analyze_resume` tool signature and implementation |
| [VERIFIED: codebase] | `agent/tools.py:20-27` - `_get_resume_parser` singleton with `with_structured_output(CandidateInfo)` |
| [VERIFIED: codebase] | `agent/schemas.py:11-20` - `CandidateInfo` Pydantic model (name, email, skills, years_of_experience, education, summary) |
| [VERIFIED: codebase] | `api/server.py:173-209` - Existing `/upload-resume` endpoint pattern (PDF text extraction, error handling) |
| [VERIFIED: codebase] | `backend/db/models/jd.py` - JD model pattern (Enum, Column, DeclarativeBase) |
| [VERIFIED: codebase] | `backend/api/routes/jd.py` - JD CRUD pattern (list, create, get, update, status) |
| [VERIFIED: codebase] | `tests/test_jd.py` - Test pattern (classes per test group, _auth_header helper, httpx AsyncClient) |
| [VERIFIED: codebase] | `tests/conftest.py` - Test fixtures (db_path, test_engine, test_session, test_client, test_user) |
| [VERIFIED: codebase] | `config.py:28` - `RESUME_DIR` already defined as `data/resumes/` |
| [VERIFIED: codebase] | `data/resumes/` - Directory exists with 36 sample resumes (tracked in git) |
| [VERIFIED: pip show] | PyMuPDF 1.27.2.2 installed; python-multipart 0.0.26 installed |
| [VERIFIED: pip show] | python-docx NOT installed |

### Secondary (MEDIUM confidence)

| Source | What Was Verified |
|--------|-------------------|
| [CITED: python-docx docs] | Document() API for reading .docx files; `paragraphs` attribute for text extraction |
| [CITED: FastAPI docs] | `UploadFile`, `File(...)`, multipart/form-data handling; async file read |
| [CITED: axios docs] | `onUploadProgress` for upload progress; FormData for multipart file upload |

### Tertiary (LOW confidence)

None -- all findings based on codebase audit or verified package checks.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all existing packages verified via codebase audit; only python-docx is new and must be added
- Architecture: HIGH -- all patterns are direct reuse of Phase 1/2 established patterns; state machine follows JDStatus exactly
- Pitfalls: HIGH -- all based on existing codebase issues and D-01 through D-17 constraints

**Research date:** 2026-04-26
**Valid until:** 2026-05-26 (30 days)
