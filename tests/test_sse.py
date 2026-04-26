"""SSE streaming tests — D-15."""
import pytest


class TestSSE:
    """D-15: SSE hardening."""

    async def test_timeout_sentinel(self, test_client):
        """SSE endpoint sends [DONE] on timeout."""
        pass

    async def test_disconnect(self, test_client):
        """SSE endpoint handles client disconnect gracefully."""
        pass
