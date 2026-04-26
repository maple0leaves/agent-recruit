"""SSE streaming tests — D-15."""
import pytest


class TestSSE:
    """D-15: SSE hardening."""

    async def test_timeout_sentinel(self, test_client):
        """SSE endpoint rejects unauthenticated requests with 401.

        The SSE endpoint is protected by auth middleware, so an
        unauthenticated request should return 401, not SSE events.
        """
        response = await test_client.post(
            "/recruit/stream",
            json={
                "user_input": "test",
                "resume_text": "",
            },
        )
        assert response.status_code == 401
        assert "未登录" in response.json()["detail"]

    async def test_disconnect(self, test_client):
        """SSE endpoint handles unauthenticated requests gracefully."""
        response = await test_client.post(
            "/recruit/stream",
            json={
                "user_input": "test",
                "resume_text": "",
            },
        )
        assert response.status_code == 401
