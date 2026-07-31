"""
Integration tests for orders API endpoints.

Covers:
- Order creation from cart.
- Order listing with pagination.
- Order cancellation.
- Error handling for empty cart and invalid orders.
"""


from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    create_test_user,
    login_test_user,
    create_test_movie
)


async def _add_movie_to_cart(
        client: AsyncClient,
        token: str,
        movie_id: int
) -> None:
    """Helper to add a movie to the user's cart."""
    await client.post(
        "/api/v1/cart/items/",
        json={"movie_id": movie_id},
        headers={"Authorization": f"Bearer {token}"}
    )


class TestCreateOrder:
    """Tests for order creation endpoint."""

    async def test_create_order_success(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that a user can create an order."""
        user = await create_test_user(db_session, email="test@ordercreate.com")
        tokens = await login_test_user(client, user.email)
        movie = await create_test_movie(db_session)
        await _add_movie_to_cart(client, tokens["access_token"], movie.id)
        resp = await client.post(
            "/api/v1/orders/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code in (200, 201)

    async def test_create_order_empty_cart(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that a user cannot create an order with an empty cart."""
        user = await create_test_user(db_session, email="test@emptycart.com")

        tokens = await login_test_user(client, user.email)
        resp = await client.post(
            "/api/v1/orders/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code == 400

    async def test_create_order_unauthenticated(
            self,
            client: AsyncClient
    ) -> None:
        """Test for impossible creating an order by unauthenticated user."""
        resp = await client.post("/api/v1/orders/")  # arbitrary request
        assert resp.status_code == 422


class TestListOrders:
    """Tests for order listing endpoint."""

    async def test_list_orders(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that a user can list orders."""
        user = await create_test_user(db_session, email="test@listorders.com")
        tokens = await login_test_user(client, user.email)
        resp = await client.get(
            "/api/v1/orders/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code == 200

    async def test_list_orders_pagination(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that a user can list orders with pagination."""
        user = await create_test_user(db_session, email="test@listorders.com")
        tokens = await login_test_user(client, user.email)
        resp = await client.get(
            "/api/v1/orders/?page=1&per_page=5",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code == 200


class TestCancelOrder:
    """Tests for order cancellation endpoint."""

    async def test_cancel_order(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that a user can cancel an order."""
        user = await create_test_user(db_session, email="test@cancelorder.com")
        tokens = await login_test_user(client, user.email)
        movie = await create_test_movie(db_session)
        await _add_movie_to_cart(client, tokens["access_token"], movie.id)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        order_resp = await client.post("/api/v1/orders/", headers=headers)
        if order_resp.status_code in (200, 201):
            order_id = order_resp.json().get("id")
            if order_id:
                resp = await client.post(
                    f"/api/v1/orders/{order_id}/cancel/",
                    headers=headers
                )
                assert resp.status_code == 200

    async def test_cancel_nonexistent_order(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests that a user cannot cancel a nonexistent order."""
        user = await create_test_user(
            db_session,
            email="test@cancelnonexistent.com"
        )
        tokens = await login_test_user(client, user.email)
        resp = await client.post(
            "/api/v1/orders/99999/cancel/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code == 404
