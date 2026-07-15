from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_test_user, create_test_movie


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


class TestCartAddItem:
    """Tests for adding items to cart."""

    async def test_add_item(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests adding item to cart."""
        user = await create_test_user(db_session, email="test@cart.com")
        tokens = await login_test_user(client, user.email)
        movie = await create_test_movie(db_session)
        resp = await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": movie.id},
            headers={"Authorization": f"Bearer {tokens["access_token"]}"}
        )
        assert resp.status_code in (200, 201)

    async def test_add_duplicate_item(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests adding duplicate item to cart fails."""
        user = await create_test_user(db_session, email="test@cart.com")
        tokens = await login_test_user(client, user.email)
        movie = await create_test_movie(db_session)
        headers = {"Authorization": f"Bearer {tokens["access_token"]}"}
        await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": movie.id},
            headers=headers
        )
        resp = await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": movie.id},
            headers=headers
        )
        assert resp.status_code in (400, 409)

    async def test_add_nonexistent_movie(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that adding non-existent movie to cart fails."""
        user = await create_test_user(db_session, email="test@cart.com")
        tokens = await login_test_user(client, user.email)
        resp = await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": 99999},
            headers={"Authorization": f"Bearer {tokens["access_token"]}"}
        )
        assert resp.status_code in (400, 404)


class TestCartRemoveItem:
    """Tests for removing items from cart."""

    async def test_remove_item(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests removing item from cart."""
        user = await create_test_user(
            db_session,
            email="test@removefromcart.com"
        )
        tokens = await login_test_user(client, user.email)
        movie = await create_test_movie(db_session)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": movie.id},
            headers=headers
        )
        resp = await client.delete(
            f"/api/v1/cart/items/{movie.id}/",
            headers=headers
        )
        assert resp.status_code == 200

    async def test_remove_nonexistent_item(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Test removing nonexistent item from cart fails."""
        user = await create_test_user(
            db_session,
            email="test@removefromcart.com"
        )
        tokens = await login_test_user(client, user.email)
        resp = await client.delete(
            "/api/v1/cart/items/99999/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code in (400, 404)
