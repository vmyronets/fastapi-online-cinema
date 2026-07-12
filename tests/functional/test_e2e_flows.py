from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.accounts.models.user import UserModel
from sqlalchemy import update
from tests.conftest import _seed_groups


class TestRegistrationLoginFlow:
    """
    End-to-end: register a user, then login, and use the token.
    Check that the user can be registered, activated, and logged in.
    """

    async def test_register_and_login(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:

        await _seed_groups(db_session)

        # Register the user and check response
        register_response = await client.post(
            "/api/v1/accounts/register/",
            json={"email": "e2e@example.com", "password": "StrongP@ss1"}
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        assert user_data["is_active"] is False

        # Manually activate (simulate) by updating DB directly
        await db_session.execute(
            update(UserModel).where(
                UserModel.email == "e2e@example.com"
            ).values(is_active=True)
        )
        await db_session.commit()

        # Log in user and check response
        login_response = await client.post(
            "/api/v1/accounts/login/",
            json={"email": "e2e@example.com", "password": "StrongP@ss1"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # Use access token to access protected endpoint
        cart_resp = await client.get(
            "/api/v1/cart/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert cart_resp.status_code == 200
