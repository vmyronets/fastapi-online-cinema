import pytest

from src.security.jwt_manager import JWTAuthManager


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
