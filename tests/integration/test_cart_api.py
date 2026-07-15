from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_test_user


class TestCartView:
    """Tests for viewing cart."""

    async def test_view_cart_unauthenticated(
            self,
            client: AsyncClient
    ) -> None:
        """Tests viewing cart for unauthenticated user."""
        resp = await client.get("/api/v1/cart/")
        assert resp.status_code == 422

    async def test_view_cart_authenticated(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests viewing cart for authenticated user."""
        user = await create_test_user(db_session, email="test@cart.com")
        tokens = await login_test_user(client, user.email)
        resp = await client.get(
            "/api/v1/cart/",
            headers={"Authorization": f"Bearer {tokens["access_token"]}"}
        )
        assert resp.status_code == 200
