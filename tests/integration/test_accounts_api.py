from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import (
    create_test_user,
    _seed_groups,
    login_test_user
)


class TestHealthCheck:
    """Tests for the health check endpoint for the application."""

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestRegister:
    """Tests for user registration endpoint."""

    async def test_register_success(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """
        Check if user registration is successful.
        """
        await _seed_groups(db_session)
        resp = await client.post(
            "/api/v1/accounts/register/",
            json={"email": "new@example.com", "password": "StrongP@ss1"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new@example.com"
        assert data["is_active"] is False

    async def test_register_duplicate_email(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """
        Check if user registration fails with duplicate email.
        """
        await create_test_user(db_session, email="dup@example.com")
        resp = await client.post(
            "/api/v1/accounts/register/",
            json={"email": "dup@example.com", "password": "StrongP@ss1"}
        )
        assert resp.status_code in (400, 409)

    async def test_register_weak_password(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """
        Check if user registration fails with weak password.
        """
        await _seed_groups(db_session)
        resp = await client.post(
            "/api/v1/accounts/register/",
            json={"email": "weak@example.com", "password": "weakpass1"}
        )
        assert resp.status_code in (400, 422)

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        """
        Check if user registration fails with invalid email.
        """
        resp = await client.post(
            "/api/v1/accounts/register/",
            json={"email": "not-email", "password": "StrongP@ss1"}
        )
        assert resp.status_code == 422


class TestLogin:
    """Tests for login endpoint and JWT token issuance."""

    async def test_login_success(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """
        Check if user login succeeds with valid credentials.
        """
        await create_test_user(
            db_session,
            email="login@example.com",
            password="StrongP@ss1"
        )
        resp = await client.post(
            "/api/v1/accounts/login/",
            json={"email": "login@example.com", "password": "StrongP@ss1"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """
        Check if user login fails with invalid password.
        """
        await create_test_user(db_session, email="login2@example.com")
        resp = await client.post(
            "/api/v1/accounts/login/",
            json={"email": "login2@example.com", "password": "WrongPass1!"}
        )
        assert resp.status_code in (400, 401)

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        """Check if user login fails with nonexistent user."""
        resp = await client.post(
            "/api/v1/accounts/login/",
            json={"email": "ghost@example.com", "password": "StrongP@ss1"}
        )
        assert resp.status_code in (400, 401, 404)

    async def test_login_inactive_user(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Check if user login fails with inactive user."""
        await create_test_user(
            db_session,
            email="inactive@example.com",
            is_active=False
        )
        resp = await client.post(
            "/api/v1/accounts/login/",
            json={"email": "inactive@example.com", "password": "TestPass1!"}
        )
        assert resp.status_code in (400, 403)


class TestLogout:
    """Tests for logout endpoint."""

    async def test_logout_success(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Test logout endpoint with valid token."""
        user = await create_test_user(db_session, email="logout@example.com")
        tokens = await login_test_user(client, user.email)
        resp = await client.post(
            "/api/v1/accounts/logout/",
            headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 200

    async def test_logout_no_token(self, client: AsyncClient) -> None:
        """Check if user logout fails without token."""
        resp = await client.post("/api/v1/accounts/logout/")
        assert resp.status_code == 422


class TestTokenRefresh:
    """Tests for token refresh endpoint."""

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        """Check if token refresh fails with invalid token."""
        resp = await client.post(
            "/api/v1/accounts/token/refresh/",
            json={"refresh_token": "invalid-token"}
        )
        assert resp.status_code in (400, 401)


class TestChangePassword:
    """Tests for password change endpoint."""

    async def test_change_password_success(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Check if password change succeeds with valid credentials."""
        user = await create_test_user(
            db_session,
            email="chpw@example.com",
            password="OldPass1!"
        )
        tokens = await login_test_user(client, user.email, "OldPass1!")
        resp = await client.post(
            "/api/v1/accounts/password/change/",
            json={"old_password": "OldPass1!", "new_password": "NewPass1!"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code == 200

    async def test_change_password_wrong_old(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        """Check if password change fails with invalid old password."""
        user = await create_test_user(db_session, email="chpw2@example.com")
        tokens = await login_test_user(client, user.email)
        resp = await client.post(
            "/api/v1/accounts/password/change/",
            json={"old_password": "WrongOld1!", "new_password": "NewPass1!"},
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert resp.status_code in (400, 401)
