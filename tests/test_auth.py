"""Authentication tests — AUTH-01, AUTH-02, AUTH-03."""
import pytest


class TestLogin:
    """AUTH-01: HR can login with username and password."""

    async def test_login_success(self, test_client, test_user):
        """Login with valid credentials returns JWT + cookie."""
        pass

    async def test_login_wrong_password(self, test_client, test_user):
        """Login with wrong password returns 401."""
        pass


class TestAuth:
    """AUTH-01/AUTH-03: Authentication enforcement."""

    async def test_unauthenticated(self, test_client):
        """Unauthenticated request returns 401."""
        pass


class TestAuthZ:
    """AUTH-02: Role-based access control."""

    async def test_role_check(self, test_client, test_user):
        """Protected endpoint returns 403 for wrong role."""
        pass


class TestSession:
    """AUTH-03: Session persistence."""

    async def test_session_persistence(self, test_client, test_user):
        """/auth/me returns user from cookie session."""
        pass

    async def test_logout(self, test_client, test_user):
        """Logout clears cookie and invalidates session."""
        pass
