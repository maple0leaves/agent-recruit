import pytest


@pytest.mark.asyncio
async def test_spa_deep_link_returns_index_html(test_client):
    response = await test_client.get("/jd")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_post_only_api_preserves_405(test_client):
    response = await test_client.get("/api/recruit")

    assert response.status_code == 405


@pytest.mark.asyncio
async def test_api_health_is_namespaced(test_client):
    response = await test_client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_unknown_api_path_stays_404(test_client):
    response = await test_client.get("/api/does-not-exist")

    assert response.status_code == 404
