import pytest
from fastapi import HTTPException

from src.security.dependencies import (
    get_token
)


class TestGetToken:
    """Tests for get_token dependency."""

    def test_valid_bearer_token(self):
        token = get_token("Bearer my-jwt-token")
        assert token == "my-jwt-token"

    def test_missing_bearer_prefix(self):
        with pytest.raises(HTTPException) as exc_info:
            get_token("Token my-jwt-token")
        assert exc_info.value.status_code == 401

    def test_empty_header(self):
        with pytest.raises(HTTPException):
            get_token("")

    def test_bearer_only(self):
        token = get_token("Bearer ")
        assert token == ""
