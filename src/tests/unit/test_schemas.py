import pytest
from pydantic import ValidationError

from src.accounts.schemas import (
    UserRegisterSchema,
    LoginSchema,
    ActivationRequestSchema
)


class TestUserRegisterSchema:
    """
    Tests for UserRegisterSchema validation.
    Check if the schema validates valid and invalid inputs correctly.
    """

    def test_valid_registration(self):
        schema = UserRegisterSchema(
            email="user@example.com",
            password="StrongP@ss1"
        )
        assert schema.email == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(email="not-an-email", password="StrongP@ss1")

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(email="user@example.com", password="Sh1!")

    def test_password_too_long(self):
        with pytest.raises(ValidationError):
            UserRegisterSchema(email="user@example.com", password="A" * 129)


class TestLoginSchema:
    """Tests for LoginSchema validation."""

    def test_valid_login(self):
        schema = LoginSchema(email="user@example.com", password="password")
        assert schema.email == "user@example.com"

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            LoginSchema(email="bad", password="password")


class TestActivationRequestSchema:
    """Tests for ActivationRequestSchema validation."""

    def test_with_token(self):
        schema = ActivationRequestSchema(token="abc123")
        assert schema.token == "abc123"

    def test_with_email(self):
        schema = ActivationRequestSchema(email="user@example.com")
        assert schema.email == "user@example.com"

    def test_neither_provided(self):
        with pytest.raises(ValidationError):
            ActivationRequestSchema()
