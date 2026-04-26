"""Integration tests for JD CRUD, filtering, pagination, templates."""
import pytest
from backend.auth.jwt import create_access_token


def _auth_header(test_user) -> dict[str, str]:
    """Create Authorization header with a valid JWT for the test user."""
    token = create_access_token(str(test_user.id), test_user.role.value)
    return {"Authorization": f"Bearer {token}"}


SAMPLE_JD = {
    "title": "Python工程师",
    "department": "技术部",
    "skills": "Python, FastAPI, SQL",
    "experience_years": 3,
    "education": "本科",
    "salary_min": 20000,
    "salary_max": 40000,
    "description": "负责后端API开发与数据库优化",
}


class TestCreateJD:
    """JD-01: HR can create a new JD."""

    async def test_create_jd_success(self, test_client, test_user):
        """Create JD with valid data returns 201 and full JDResponse."""
        headers = _auth_header(test_user)
        response = await test_client.post("/jd", json=SAMPLE_JD, headers=headers)
        assert response.status_code == 201
        result = response.json()
        assert result["title"] == SAMPLE_JD["title"]
        assert result["department"] == SAMPLE_JD["department"]
        assert result["skills"] == SAMPLE_JD["skills"]
        assert result["experience_years"] == SAMPLE_JD["experience_years"]
        assert result["education"] == SAMPLE_JD["education"]
        assert result["salary_min"] == SAMPLE_JD["salary_min"]
        assert result["salary_max"] == SAMPLE_JD["salary_max"]
        assert result["description"] == SAMPLE_JD["description"]
        assert result["status"] == "draft"
        assert "id" in result
        assert "created_at" in result
        assert "updated_at" in result

    async def test_create_jd_validation(self, test_client, test_user):
        """Create JD with missing required fields returns 422."""
        headers = _auth_header(test_user)
        response = await test_client.post(
            "/jd", json={"title": "", "department": "技术部"}, headers=headers
        )
        assert response.status_code == 422

    async def test_create_jd_unauthorized(self, test_client):
        """Create JD without auth header returns 401."""
        response = await test_client.post("/jd", json=SAMPLE_JD)
        assert response.status_code == 401


class TestUpdateCloseJD:
    """JD-02: HR can edit and close existing JDs."""

    async def _create_jd(self, client, headers, **overrides) -> dict:
        data = {**SAMPLE_JD, **overrides}
        resp = await client.post("/jd", json=data, headers=headers)
        assert resp.status_code == 201
        return resp.json()

    async def test_update_jd(self, test_client, test_user):
        """PUT /jd/{id} updates all fields."""
        headers = _auth_header(test_user)
        created = await self._create_jd(test_client, headers)
        jd_id = created["id"]

        updated_data = {
            "title": "高级Java工程师",
            "department": "研发部",
            "skills": "Java, Spring, MySQL",
            "experience_years": 5,
            "education": "硕士",
            "salary_min": 30000,
            "salary_max": 50000,
            "description": "负责核心系统架构设计与开发",
        }
        resp = await test_client.put(
            f"/jd/{jd_id}", json=updated_data, headers=headers
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["title"] == "高级Java工程师"
        assert result["department"] == "研发部"
        assert result["skills"] == "Java, Spring, MySQL"
        assert result["experience_years"] == 5
        assert result["education"] == "硕士"
        assert result["salary_min"] == 30000
        assert result["salary_max"] == 50000
        assert result["description"] == "负责核心系统架构设计与开发"

    async def test_close_jd(self, test_client, test_user):
        """PATCH /jd/{id}/status transitions draft->active->closed."""
        headers = _auth_header(test_user)
        created = await self._create_jd(test_client, headers)
        jd_id = created["id"]
        assert created["status"] == "draft"

        # Activate
        resp = await test_client.patch(
            f"/jd/{jd_id}/status",
            json={"status": "active"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "active"

        # Close
        resp = await test_client.patch(
            f"/jd/{jd_id}/status",
            json={"status": "closed"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"

    async def test_reactivate_jd(self, test_client, test_user):
        """Closed JD can be reactivated to active (D-12)."""
        headers = _auth_header(test_user)
        created = await self._create_jd(test_client, headers)
        jd_id = created["id"]

        # draft -> active -> closed -> active
        for status in ["active", "closed", "active"]:
            resp = await test_client.patch(
                f"/jd/{jd_id}/status",
                json={"status": status},
                headers=headers,
            )
            assert resp.status_code == 200
        assert resp.json()["status"] == "active"

    async def test_invalid_status_transition(self, test_client, test_user):
        """draft -> closed is invalid (D-12: must go draft->active first)."""
        headers = _auth_header(test_user)
        created = await self._create_jd(test_client, headers)
        jd_id = created["id"]

        resp = await test_client.patch(
            f"/jd/{jd_id}/status",
            json={"status": "closed"},
            headers=headers,
        )
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "draft" in detail or "closed" in detail


class TestListJD:
    """JD-03: HR can filter and search JD list with server-side pagination."""

    async def _create_jd(self, client, headers, **overrides) -> dict:
        data = {**SAMPLE_JD, **overrides}
        resp = await client.post("/jd", json=data, headers=headers)
        assert resp.status_code == 201
        return resp.json()

    async def test_list_jds_pagination(self, test_client, test_user):
        """GET /jd returns paginated results with total count."""
        headers = _auth_header(test_user)
        for i in range(25):
            await self._create_jd(
                test_client, headers,
                title=f"职位{i}", department=f"部门{i % 5}",
            )

        # Page 1: first 20
        resp1 = await test_client.get(
            "/jd?page=1&page_size=20", headers=headers
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert len(data1["items"]) == 20
        assert data1["total"] == 25
        assert data1["page"] == 1
        assert data1["page_size"] == 20

        # Page 2: remaining 5
        resp2 = await test_client.get(
            "/jd?page=2&page_size=20", headers=headers
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert len(data2["items"]) == 5
        assert data2["total"] == 25
        assert data2["page"] == 2

    async def test_list_jds_filter_status(self, test_client, test_user):
        """GET /jd?status=active returns only active JDs."""
        headers = _auth_header(test_user)

        # Create 2 draft JDs
        jd1 = await self._create_jd(test_client, headers, title="Draft JD")
        # Activate one
        await test_client.patch(
            f"/jd/{jd1['id']}/status",
            json={"status": "active"},
            headers=headers,
        )
        await self._create_jd(test_client, headers, title="Another Draft")

        resp = await test_client.get(
            "/jd?status=active", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["status"] == "active" for item in data["items"])
        assert data["total"] == 1

    async def test_list_jds_search_keyword(self, test_client, test_user):
        """GET /jd?keyword=Python filters by title/department/skills (D-08)."""
        headers = _auth_header(test_user)
        await self._create_jd(test_client, headers, title="Python工程师")
        await self._create_jd(test_client, headers, title="Java工程师")

        resp = await test_client.get(
            "/jd?keyword=Python", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Python工程师"

    async def test_list_jds_date_filter(self, test_client, test_user):
        """GET /jd with date_from/date_to includes JDs from today."""
        headers = _auth_header(test_user)
        await self._create_jd(test_client, headers, title="Today's JD")

        import datetime
        today = datetime.date.today().isoformat()
        resp = await test_client.get(
            f"/jd?date_from={today}&date_to={today}", headers=headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_list_jds_no_filters(self, test_client, test_user):
        """GET /jd without filters returns all JDs paginated."""
        headers = _auth_header(test_user)
        await self._create_jd(test_client, headers, title="JD One")
        await self._create_jd(test_client, headers, title="JD Two")

        resp = await test_client.get("/jd", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2


class TestTemplates:
    """JD-04: System provides 3-5 JD templates."""

    async def test_list_templates(self, test_client, test_user):
        """GET /jd/templates returns at least 3 template items."""
        headers = _auth_header(test_user)
        resp = await test_client.get("/jd/templates", headers=headers)
        assert resp.status_code == 200
        templates = resp.json()
        assert isinstance(templates, list)
        assert len(templates) >= 3
        for t in templates:
            assert "name" in t
            assert "skills" in t
            assert "experience_years" in t
            assert "education" in t
            assert "salary_min" in t
            assert "salary_max" in t
            assert "description" in t


class TestAuth:
    """All JD endpoints require authentication."""

    async def test_jd_requires_auth(self, test_client):
        """All JD endpoints return 401 without auth header."""
        # POST /jd
        assert (await test_client.post("/jd", json=SAMPLE_JD)).status_code == 401
        # PUT /jd/1
        assert (await test_client.put("/jd/1", json=SAMPLE_JD)).status_code == 401
        # PATCH /jd/1/status
        assert (await test_client.patch("/jd/1/status", json={"status": "active"})).status_code == 401
        # GET /jd
        assert (await test_client.get("/jd")).status_code == 401
        # GET /jd/1
        assert (await test_client.get("/jd/1")).status_code == 401
        # GET /jd/templates
        assert (await test_client.get("/jd/templates")).status_code == 401
