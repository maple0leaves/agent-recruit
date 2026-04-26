"""Integration tests for candidate upload, CRUD, list/search/filter, status machine."""
import io
import json
import uuid
from unittest.mock import patch

import fitz  # PyMuPDF for test PDF generation
import pytest
from backend.auth.jwt import create_access_token


def _auth_header(test_user) -> dict[str, str]:
    """Create Authorization header with a valid JWT for the test user."""
    token = create_access_token(str(test_user.id), test_user.role.value)
    return {"Authorization": f"Bearer {token}"}


MOCK_CANDIDATE_JSON = json.dumps({
    "name": "张三",
    "email": "zhangsan@test.com",
    "skills": ["Python", "FastAPI", "SQL"],
    "years_of_experience": 3,
    "education": "本科",
    "summary": "3年Python开发经验，熟悉FastAPI和SQL数据库",
})


def _make_test_pdf(text: str = "Test resume content") -> bytes:
    """Generate a minimal valid PDF with the given text content."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def _make_test_docx(text: str = "Test resume content") -> bytes:
    """Generate a minimal valid .docx with the given text content."""
    from docx import Document
    doc = Document()
    doc.add_paragraph(text)
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def _mock_analyze_resume(**overrides):
    """Create a mock for analyze_resume that returns MOCK_CANDIDATE_JSON with optional overrides."""
    data = json.loads(MOCK_CANDIDATE_JSON)
    data.update(overrides)
    return json.dumps(data)


# ── Class TestUpload (RES-01, RES-02) ────────────────────────────────────────


class TestUpload:
    """Resume upload and auto-parsing (RES-01, RES-02, D-01~D-05)."""

    @patch("backend.api.routes.candidate.analyze_resume")
    async def test_upload_pdf_success(self, mock_analyze, test_client, test_user):
        """Upload valid PDF returns 201 with parsed candidate data."""
        mock_analyze.invoke.return_value = MOCK_CANDIDATE_JSON
        headers = _auth_header(test_user)
        pdf_bytes = _make_test_pdf("张三 3年Python经验")
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "张三"
        assert result["email"] == "zhangsan@test.com"
        assert result["skills"] == "Python, FastAPI, SQL"
        assert result["education"] == "本科"
        assert result["experience"] == "3年Python开发经验，熟悉FastAPI和SQL数据库"
        assert result["status"] == "new"
        assert result["parsed_at"] is not None
        assert "data/resumes/" in result["resume_file_path"]
        assert "id" in result

    @patch("backend.api.routes.candidate.analyze_resume")
    async def test_upload_docx_success(self, mock_analyze, test_client, test_user):
        """Upload valid .docx returns 201 with parsed candidate data."""
        mock_analyze.invoke.return_value = MOCK_CANDIDATE_JSON
        headers = _auth_header(test_user)
        docx_bytes = _make_test_docx("张三 3年Python经验")
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            headers=headers,
        )
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "张三"
        assert result["email"] == "zhangsan@test.com"
        assert result["status"] == "new"
        assert result["parsed_at"] is not None

    async def test_file_too_large(self, test_client, test_user):
        """Upload file > 10MB returns 400."""
        headers = _auth_header(test_user)
        # Create 11MB of garbage bytes
        large_bytes = b"x" * (11 * 1024 * 1024)
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("large.pdf", large_bytes, "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "10" in detail or "10MB" in detail

    async def test_invalid_format(self, test_client, test_user):
        """Upload non-PDF/DOCX file returns 400."""
        headers = _auth_header(test_user)
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("resume.exe", b"fake exe", "application/octet-stream")},
            headers=headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "格式" in detail or "format" in detail.lower()

    async def test_upload_requires_auth(self, test_client):
        """Upload without auth header returns 401."""
        pdf_bytes = _make_test_pdf("Test content")
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        )
        assert response.status_code == 401

    @patch("backend.api.routes.candidate.analyze_resume")
    async def test_parse_failure(self, mock_analyze, test_client, test_user):
        """Parse failure returns 201 with warnings and empty fallback fields (D-05)."""
        mock_analyze.invoke.side_effect = Exception("API Error")
        headers = _auth_header(test_user)
        pdf_bytes = _make_test_pdf("Test content")
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == ""
        assert result["email"] == ""
        assert result["skills"] == ""
        # Should include warnings field with error message
        assert "warnings" in result
        assert "API Error" in str(result["warnings"])

    @patch("backend.api.routes.candidate.analyze_resume")
    async def test_doc_rejected(self, mock_analyze, test_client, test_user):
        """Legacy .doc format should be rejected with helpful message."""
        headers = _auth_header(test_user)
        response = await test_client.post(
            "/candidates/upload",
            files={"file": ("resume.doc", b"fake doc", "application/msword")},
            headers=headers,
        )
        assert response.status_code == 400
        detail = response.json()["detail"]
        assert "docx" in detail.lower() or "格式" in detail


# ── Class TestList (RES-04) ────────────────────────────────────────────────────


class TestList:
    """Pagination, search, and filter for candidate list (RES-04, D-11)."""

    async def _upload_candidate(self, client, headers, mock_return_json):
        """Helper: upload a candidate with a mocked analyze_resume return."""
        with patch("backend.api.routes.candidate.analyze_resume") as mock_analyze:
            mock_analyze.invoke.return_value = mock_return_json
            pdf_bytes = _make_test_pdf("Test")
            resp = await client.post(
                "/candidates/upload",
                files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
                headers=headers,
            )
            return resp

    async def test_list_pagination(self, test_client, test_user):
        """GET /candidates returns paginated results."""
        headers = _auth_header(test_user)
        # Upload 25 candidates
        for i in range(25):
            mock_data = _mock_analyze_resume(name=f"候选人{i:02d}")
            resp = await self._upload_candidate(test_client, headers, mock_data)
            assert resp.status_code == 201

        # Page 1: first 20
        resp1 = await test_client.get("/candidates?page=1&page_size=20", headers=headers)
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1["items"]) == 20
        assert data1["total"] == 25
        assert data1["page"] == 1
        assert data1["page_size"] == 20

        # Page 2: remaining 5
        resp2 = await test_client.get("/candidates?page=2&page_size=20", headers=headers)
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) == 5
        assert data2["total"] == 25
        assert data2["page"] == 2

    async def test_search_by_name(self, test_client, test_user):
        """GET /candidates?keyword=张三 returns matching candidate."""
        headers = _auth_header(test_user)
        # Upload a specific candidate
        mock_zhang = _mock_analyze_resume(name="张三")
        resp = await self._upload_candidate(test_client, headers, mock_zhang)
        assert resp.status_code == 201

        mock_li = _mock_analyze_resume(name="李四")
        resp = await self._upload_candidate(test_client, headers, mock_li)
        assert resp.status_code == 201

        # Search by name
        resp = await test_client.get("/candidates?keyword=张三", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "张三"

    async def test_search_by_skill(self, test_client, test_user):
        """GET /candidates?keyword=Python returns candidates with Python in skills."""
        headers = _auth_header(test_user)
        mock_python = _mock_analyze_resume(name="Python Dev", skills=["Python", "Django"])
        resp = await self._upload_candidate(test_client, headers, mock_python)
        assert resp.status_code == 201

        mock_java = _mock_analyze_resume(name="Java Dev", skills=["Java", "Spring"])
        resp = await self._upload_candidate(test_client, headers, mock_java)
        assert resp.status_code == 201

        resp = await test_client.get("/candidates?keyword=Python", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert "Python" in data["items"][0]["skills"]

    async def test_filter_status(self, test_client, test_user):
        """GET /candidates?status=new returns only new candidates."""
        headers = _auth_header(test_user)
        mock_data = _mock_analyze_resume(name="Test Candidate")
        resp = await self._upload_candidate(test_client, headers, mock_data)
        assert resp.status_code == 201

        resp = await test_client.get("/candidates?status=new", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["status"] == "new"

        resp = await test_client.get("/candidates?status=screening", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0

    async def test_list_no_filters(self, test_client, test_user):
        """GET /candidates without params returns all candidates."""
        headers = _auth_header(test_user)
        mock_data1 = _mock_analyze_resume(name="候选人甲")
        mock_data2 = _mock_analyze_resume(name="候选人乙")
        await self._upload_candidate(test_client, headers, mock_data1)
        await self._upload_candidate(test_client, headers, mock_data2)

        resp = await test_client.get("/candidates", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2

    async def test_list_requires_auth(self, test_client):
        """GET /candidates without auth returns 401."""
        resp = await test_client.get("/candidates")
        assert resp.status_code == 401


# ── Class TestCRUD (RES-03) ────────────────────────────────────────────────────


class TestCRUD:
    """Candidate GET, PUT operations (RES-03, D-04, D-06)."""

    async def _create_candidate(self, client, headers, mock_return_json=None):
        """Helper: upload a candidate and return the response."""
        if mock_return_json is None:
            mock_return_json = MOCK_CANDIDATE_JSON
        with patch("backend.api.routes.candidate.analyze_resume") as mock_analyze:
            mock_analyze.invoke.return_value = mock_return_json
            pdf_bytes = _make_test_pdf("Test")
            resp = await client.post(
                "/candidates/upload",
                files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
                headers=headers,
            )
            assert resp.status_code == 201
            return resp.json()

    async def test_get_candidate(self, test_client, test_user):
        """GET /candidates/{id} returns full candidate with all fields."""
        headers = _auth_header(test_user)
        created = await self._create_candidate(test_client, headers)

        resp = await test_client.get(f"/candidates/{created['id']}", headers=headers)
        assert resp.status_code == 200
        result = resp.json()
        assert result["name"] == "张三"
        assert result["email"] == "zhangsan@test.com"
        assert result["skills"] == "Python, FastAPI, SQL"
        assert result["education"] == "本科"
        assert result["experience"] == "3年Python开发经验，熟悉FastAPI和SQL数据库"
        assert result["status"] == "new"
        assert result["parsed_at"] is not None

    async def test_get_candidate_not_found(self, test_client, test_user):
        """GET /candidates/9999 returns 404."""
        headers = _auth_header(test_user)
        resp = await test_client.get("/candidates/9999", headers=headers)
        assert resp.status_code == 404
        assert "不存在" in resp.json()["detail"]

    async def test_update_candidate(self, test_client, test_user):
        """PUT /candidates/{id} updates writable fields only."""
        headers = _auth_header(test_user)
        created = await self._create_candidate(test_client, headers)

        update_data = {
            "name": "张三(更新)",
            "email": "updated@test.com",
            "phone": "13800138000",
            "skills": "Python, FastAPI, Docker",
            "education": "硕士",
            "experience": "5年Python全栈开发经验",
        }
        resp = await test_client.put(
            f"/candidates/{created['id']}", json=update_data, headers=headers,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["name"] == "张三(更新)"
        assert result["email"] == "updated@test.com"
        assert result["phone"] == "13800138000"
        assert result["skills"] == "Python, FastAPI, Docker"
        assert result["education"] == "硕士"
        assert result["experience"] == "5年Python全栈开发经验"
        # Status and parsed_at should remain unchanged
        assert result["status"] == "new"
        assert result["parsed_at"] is not None

    async def test_update_requires_auth(self, test_client):
        """PUT /candidates/1 without auth returns 401."""
        resp = await test_client.put(
            "/candidates/1", json={"name": "Test"},
        )
        assert resp.status_code == 401

    async def test_partial_update(self, test_client, test_user):
        """PUT with only some fields updates only those fields."""
        headers = _auth_header(test_user)
        created = await self._create_candidate(test_client, headers)
        original_name = created["name"]
        original_email = created["email"]

        resp = await test_client.put(
            f"/candidates/{created['id']}",
            json={"phone": "13900139000"},
            headers=headers,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["phone"] == "13900139000"
        # Other fields unchanged
        assert result["name"] == original_name
        assert result["email"] == original_email

    async def test_update_not_found(self, test_client, test_user):
        """PUT /candidates/9999 returns 404."""
        headers = _auth_header(test_user)
        resp = await test_client.put(
            "/candidates/9999", json={"name": "Test"}, headers=headers,
        )
        assert resp.status_code == 404


# ── Class TestStatus (RES-05, D-14~D-17) ───────────────────────────────────────


class TestStatus:
    """Pipeline status state machine (RES-05, D-14~D-17)."""

    async def _create_candidate(self, client, headers):
        """Create a new candidate via upload with mock."""
        with patch("backend.api.routes.candidate.analyze_resume") as mock_analyze:
            mock_analyze.invoke.return_value = MOCK_CANDIDATE_JSON
            pdf_bytes = _make_test_pdf("Test")
            resp = await client.post(
                "/candidates/upload",
                files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
                headers=headers,
            )
            assert resp.status_code == 201
            return resp.json()

    async def test_valid_transition_new_to_screening(self, test_client, test_user):
        """new -> screening with note returns 200."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)
        assert candidate["status"] == "new"

        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "screening", "status_note": "开始筛选"},
            headers=headers,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["status"] == "screening"
        assert result["status_note"] == "开始筛选"

    async def test_valid_transition_new_to_rejected(self, test_client, test_user):
        """new -> rejected directly is allowed (D-14)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "rejected", "status_note": "不符合要求"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"

    async def test_valid_transition_to_interview(self, test_client, test_user):
        """new -> screening -> interview (D-14)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        # new -> screening
        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "screening", "status_note": "开始筛选"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "screening"

        # screening -> interview
        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "interview", "status_note": "进入面试"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "interview"

    async def test_valid_transition_to_hired(self, test_client, test_user):
        """new -> screening -> interview -> hired (D-14)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        for status, note in [
            ("screening", "开始筛选"),
            ("interview", "进入面试"),
            ("hired", "通过面试"),
        ]:
            resp = await test_client.patch(
                f"/candidates/{candidate['id']}/status",
                json={"status": status, "status_note": note},
                headers=headers,
            )
            assert resp.status_code == 200
            assert resp.json()["status"] == status

    async def test_terminal_hired_irreversible(self, test_client, test_user):
        """Once hired, no further status transitions allowed (D-15)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        # Advance to hired
        for status, note in [
            ("screening", "开始筛选"),
            ("interview", "进入面试"),
            ("hired", "通过面试"),
        ]:
            resp = await test_client.patch(
                f"/candidates/{candidate['id']}/status",
                json={"status": status, "status_note": note},
                headers=headers,
            )
            assert resp.status_code == 200

        # Try further transition
        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "screening", "status_note": "重新筛选"},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_terminal_rejected_irreversible(self, test_client, test_user):
        """Once rejected, no further status transitions allowed (D-15)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "rejected", "status_note": "不合适"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Try further transition
        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "screening", "status_note": "重新考虑"},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_status_change_requires_note(self, test_client, test_user):
        """PATCH without status_note returns 422 (D-09, D-16)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "screening", "status_note": ""},
            headers=headers,
        )
        assert resp.status_code == 422

    async def test_invalid_transition(self, test_client, test_user):
        """new -> interview (skip screening) returns 400 (D-14)."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "interview", "status_note": "跳过筛选"},
            headers=headers,
        )
        assert resp.status_code == 400

    async def test_invalid_status_value(self, test_client, test_user):
        """PATCH with invalid status value returns 422."""
        headers = _auth_header(test_user)
        candidate = await self._create_candidate(test_client, headers)

        resp = await test_client.patch(
            f"/candidates/{candidate['id']}/status",
            json={"status": "invalid_status", "status_note": "test"},
            headers=headers,
        )
        assert resp.status_code == 422


# ── Class TestLifecycle (D-17) ─────────────────────────────────────────────────


class TestLifecycle:
    """Candidate lifecycle constraints (D-17)."""

    async def test_no_delete(self, test_client, test_user):
        """DELETE /candidates/{id} returns 405 (D-17: no delete)."""
        headers = _auth_header(test_user)
        resp = await test_client.delete("/candidates/1", headers=headers)
        assert resp.status_code == 405
