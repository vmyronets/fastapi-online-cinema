"""
Unit tests for FastAPI security dependencies.

Covers:
- Token extraction from Authorization header.
- JWT manager and S3 client dependency factories.
"""

import pytest
from fastapi import HTTPException

from src.security.dependencies import (
    get_token,
    get_jwt_auth_manager,
    get_s3_storage_client
)
from src.security.interfaces import (
    JWTAuthManagerInterface,
    S3StorageInterface
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


class TestDependencyFactories:
    """Tests for dependency injection factories."""

    def test_get_jwt_auth_manager_returns_interface(self):
        manager = get_jwt_auth_manager()
        assert isinstance(manager, JWTAuthManagerInterface)

    def test_get_s3_storage_client_returns_interface(self):
        client = get_s3_storage_client()
        assert isinstance(client, S3StorageInterface)
