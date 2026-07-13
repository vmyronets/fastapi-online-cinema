from httpx import AsyncClient


class TestHealthCheck:
    """Tests for the health check endpoint for the application."""

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
