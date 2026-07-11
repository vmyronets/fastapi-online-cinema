import pytest
from pydantic import ValidationError

from src.accounts.schemas import (
    UserRegisterSchema,
    LoginSchema
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
