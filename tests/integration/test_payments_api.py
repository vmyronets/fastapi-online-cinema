"""
Integration tests for payments API endpoints.

Covers:
- Payment listing.
- Authentication requirements for payment endpoints.
"""


from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_user, login_test_user


class TestPaymentList:
    """Tests for payment listing endpoint."""

    async def test_list_payments_authenticated(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests listing payments for authenticated user."""
        user = await create_test_user(
            db_session,
            email="test@listpayments.com"
        )
        tokens = await login_test_user(client, user.email)
        resp = await client.get(
            "/api/v1/payments/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code == 200

    async def test_list_payments_unauthenticated(
            self,
            client: AsyncClient
    ) -> None:
        """Tests listing payments for unauthenticated user."""
        resp = await client.get("/api/v1/payments/")
        assert resp.status_code == 422


class TestPayForOrder:
    """Tests for payment creation endpoint."""

    async def test_pay_nonexistent_order(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Tests paying nonexistent order."""
        user = await create_test_user(
            db_session,
            email="test@paynonexistent.com"
        )
        tokens = await login_test_user(client, user.email)
        resp = await client.post(
            "/api/v1/payments/orders/99999/pay/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code in (400, 404)

    async def test_pay_unauthenticated(self, client: AsyncClient):
        resp = await client.post("/api/v1/payments/orders/1/pay/")
        assert resp.status_code == 422
