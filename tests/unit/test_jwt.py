"""
Unit tests for JWT token creation and validation.

Covers:
- Access and refresh token creation.
- Token decoding and type validation.
- Expired and invalid token handling.
"""


import pytest

from src.security.jwt_manager import JWTAuthManager
from src.security.exceptions import InvalidTokenError, TokenExpiredError


@pytest.fixture
def manager() -> JWTAuthManager:
    return JWTAuthManager()


class TestCreateTokens:
    """
    Tests for token creation. Create
    access and refresh tokens and compare them.
    """

    def test_create_access_token(self, manager):
        token = manager.create_access_token({"user_id": 1})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token(self, manager):
        token = manager.create_refresh_token({"user_id": 1})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_access_and_refresh_tokens_differ(self, manager):
        access = manager.create_access_token({"user_id": 1})
        refresh = manager.create_refresh_token({"user_id": 1})
        assert access != refresh


class TestDecodeTokens:
    """Tests for token decoding. """

    def test_decode_access_token(self, manager):
        token = manager.create_access_token({"user_id": 42})
        payload = manager.decode_access_token(token)
        assert payload["user_id"] == 42
        assert payload["type"] == "access"

    def test_decode_refresh_token(self, manager):
        token = manager.create_refresh_token({"user_id": 42})
        payload = manager.decode_refresh_token(token)
        assert payload["user_id"] == 42
        assert payload["type"] == "refresh"

    def test_decode_access_with_refresh_raises(self, manager):
        refresh = manager.create_refresh_token({"user_id": 1})
        with pytest.raises(InvalidTokenError):
            manager.decode_access_token(refresh)

    def test_decode_refresh_with_access_raises(self, manager):
        access = manager.create_access_token({"user_id": 1})
        with pytest.raises(InvalidTokenError):
            manager.decode_refresh_token(access)

    def test_invalid_token_string(self, manager):
        with pytest.raises(InvalidTokenError):
            manager.decode_access_token("not.a.valid.token")

    def test_empty_token(self, manager):
        with pytest.raises(InvalidTokenError):
            manager.decode_access_token("")


class TestExpiredToken:
    """Tests for expired token handling. """

    def test_expired_access_token(self):
        mgr = JWTAuthManager()
        mgr.access_token_expire_minutes = -1  # already expired
        token = mgr.create_access_token({"user_id": 1})
        with pytest.raises((TokenExpiredError, InvalidTokenError)):
            mgr.decode_access_token(token)
