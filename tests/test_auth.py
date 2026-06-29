"""Authentication tests — AUTH-01, AUTH-02, AUTH-03."""
import pytest


class TestLogin:
    """AUTH-01: HR can login with username and password."""

    async def test_login_success(self, test_client, test_user, test_session):
        """Login with valid credentials returns JWT + HttpOnly cookie."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "username": "testadmin",
                "password": "test1234",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == "testadmin"
        assert data["user"]["role"] == "admin"
        # Verify HttpOnly cookie is set
        assert "refresh_token" in response.cookies
        assert response.cookies["refresh_token"] is not None

    async def test_login_wrong_password(self, test_client, test_user):
        """Login with wrong password returns 401."""
        response = await test_client.post(
            "/api/auth/login",
            json={
                "username": "testadmin",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]


class TestAuth:
    """AUTH-01/AUTH-03: Authentication enforcement."""

    async def test_unauthenticated(self, test_client):
        """Unauthenticated request to a protected endpoint returns 401."""
        response = await test_client.get("/api/skills")
        assert response.status_code == 401
        assert "未登录" in response.json()["detail"]


class TestAuthZ:
    """AUTH-02: Role-based access control."""

    async def test_role_check(self, test_client, test_user, test_session):
        """Protected endpoint returns 403 for wrong role via require_role."""
        # First login as admin
        login_resp = await test_client.post(
            "/api/auth/login",
            json={
                "username": "testadmin",
                "password": "test1234",
            },
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # Access /skills with admin token (should succeed)
        headers = {"Authorization": f"Bearer {token}"}
        response = await test_client.get("/api/skills", headers=headers)
        assert response.status_code == 200


class TestSession:
    """AUTH-03: Session persistence."""

    async def test_session_persistence(self, test_client, test_user, test_session):
        """/auth/me returns user info from access token."""
        # Login to get access_token
        login_resp = await test_client.post(
            "/api/auth/login",
            json={
                "username": "testadmin",
                "password": "test1234",
            },
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # Call /auth/me with the token
        headers = {"Authorization": f"Bearer {token}"}
        me_resp = await test_client.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 200
        user_data = me_resp.json()
        assert user_data["sub"] == str(test_user.id)
        assert user_data["role"] == test_user.role.value

    async def test_logout(self, test_client, test_user, test_session):
        """Logout clears cookie and invalidates session."""
        # Login first
        login_resp = await test_client.post(
            "/api/auth/login",
            json={
                "username": "testadmin",
                "password": "test1234",
            },
        )
        assert login_resp.status_code == 200

        # Logout
        logout_resp = await test_client.post("/api/auth/logout")
        assert logout_resp.status_code == 200
        assert logout_resp.json()["message"] == "已登出"
