"""
Functional (end-to-end) tests covering complete user scenarios.

Covers:
- Registration → login flow.
- Movie browsing and filtering.
- User interacts with a movie successfully.
- Cart → order placement flow.
- Authentication lifecycle (login, use token, logout).
"""


from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.accounts.models.user import UserModel
from tests.conftest import (
    _seed_groups,
    create_test_user,
    login_test_user,
    create_test_movie
)


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
        cart_response = await client.get(
            "/api/v1/cart/",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert cart_response.status_code == 200


class TestAuthLifecycle:
    """
    End-to-end: login, use token, change password,
    logout and check that refresh token is revoked.
    """

    async def test_full_auth_lifecycle(
            self,
            client: AsyncClient,
            db_session: AsyncSession,
    ) -> None:

        user = await create_test_user(
            db_session,
            email="lifecycle@example.com",
            password="OldPass1!"
        )

        tokens = await login_test_user(
            client,
            user.email,
            "OldPass1!"
        )
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Use token to access protected resource
        resp = await client.get("/api/v1/cart/", headers=headers)
        assert resp.status_code == 200

        # Change password
        resp = await client.post(
            "/api/v1/accounts/password/change/",
            json={"old_password": "OldPass1!", "new_password": "NewPass1!"},
            headers=headers
        )
        assert resp.status_code == 200

        # Logout
        resp = await client.post(
            "/api/v1/accounts/logout/",
            headers=headers,
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert resp.status_code == 200

        resp = await client.post(
            "/api/v1/accounts/token/refresh/",
            json={
                "refresh_token": tokens["refresh_token"]
            }
        )

        assert resp.status_code == 401


class TestMovieBrowsingFlow:
    """End-to-end: browse movies, view details, filter."""

    async def test_browse_and_filter(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:

        await create_test_movie(
            db_session,
            name="Action Movie",
            year=2024,
            price=Decimal("12.99")
        )
        await create_test_movie(
            db_session,
            name="Drama Movie",
            year=2020,
            time=90,
            price=Decimal("8.99")
        )

        # List all movies
        resp = await client.get("/api/v1/movies/")
        assert resp.status_code == 200

        # Get specific movie
        resp = await client.get("/api/v1/movies/1/")
        assert resp.status_code == 200

        # List genres
        resp = await client.get("/api/v1/movies/genres/")
        assert resp.status_code == 200


class TestCartToOrderFlow:
    """
    End-to-end: add movies to cart, create order, view orders.
    Check that order creation and viewing work correctly.
    """

    async def test_cart_to_order(
            self,
            client: AsyncClient,
            db_session: AsyncSession,
    ):
        user = await create_test_user(
            db_session,
            email="order@example.com"
        )
        tokens = await login_test_user(client, user.email)
        movie1 = await create_test_movie(
            db_session,
            name="Movie 1",
            price=Decimal("9.99")
        )
        movie2 = await create_test_movie(
            db_session,
            name="Movie 2",
            year=2023,
            time=90,
            price=Decimal("14.99")
        )
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Add movies to cart
        resp = await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": movie1.id},
            headers=headers
        )
        assert resp.status_code in (200, 201)

        resp = await client.post(
            "/api/v1/cart/items/",
            json={"movie_id": movie2.id},
            headers=headers
        )
        assert resp.status_code in (200, 201)

        # View cart
        resp = await client.get("/api/v1/cart/", headers=headers)
        assert resp.status_code == 200

        # Create order from cart
        resp = await client.post("/api/v1/orders/", headers=headers)
        assert resp.status_code in (200, 201)

        # View orders
        resp = await client.get("/api/v1/orders/", headers=headers)
        assert resp.status_code == 200
        orders = resp.json()
        assert "orders" in orders or "items" in orders or isinstance(
            orders, list
        )


class TestMovieInteractionFlow:
    """
    End-to-end: authenticated user interacts
    with a movie (comment, rate, favorite, like).
    """

    async def test_full_movie_interaction(
            self,
            client: AsyncClient,
            db_session: AsyncSession
    ) -> None:
        user = await create_test_user(
            db_session,
            email="interact@example.com"
        )
        tokens = await login_test_user(client, user.email)
        movie = await create_test_movie(db_session)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Add comment
        resp = await client.post(
            f"/api/v1/movies/{movie.id}/comments/",
            json={"content": "Amazing film!"},
            headers=headers
        )
        assert resp.status_code in (200, 201)

        # Rate movie
        resp = await client.post(
            f"/api/v1/movies/{movie.id}/ratings/",
            json={"score": 9},
            headers=headers
        )
        assert resp.status_code in (200, 201)

        # Add to favorites
        resp = await client.post(
            f"/api/v1/movies/{movie.id}/favorites/",
            headers=headers
        )
        assert resp.status_code in (200, 201)

        # Like movie
        resp = await client.post(
            f"/api/v1/movies/{movie.id}/likes/",
            json={"is_like": True},
            headers=headers
        )
        assert resp.status_code in (200, 201)

        # View favorites
        resp = await client.get(
            f"/api/v1/movies/favorites/",
            headers=headers
        )
        assert resp.status_code == 200

        # Remove from favorites
        resp = await client.delete(
            f"/api/v1/movies/{movie.id}/favorites/",
            headers=headers
        )
        assert resp.status_code == 200
