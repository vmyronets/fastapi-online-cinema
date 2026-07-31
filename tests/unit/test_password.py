"""
Unit tests for password hashing and validation utilities.

Covers:
- Password hashing and verification.
- Password complexity validation rules.
"""


from src.security.password import (
    hash_password,
    verify_password,
    validate_password_complexity
)


class TestHashPassword:
    """
    Tests for hash_password and verify_password functions.
    Checks that hash_password returns a string and that verify_password
    correctly verifies correct and incorrect passwords.
    """

    def test_hash_returns_string(self):
        hashed = hash_password("TestPass1!")
        assert isinstance(hashed, str)
        assert hashed != "TestPass1!"

    def test_verify_correct_password(self):
        hashed = hash_password("TestPass1!")
        assert verify_password("TestPass1!", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("TestPass1!")
        assert verify_password("WrongPass1!", hashed) is False

    def test_different_hashes_for_same_password(self):
        h1 = hash_password("TestPass1!")
        h2 = hash_password("TestPass1!")
        assert h1 != h2  # bcrypt uses random salt


class TestValidatePasswordComplexity:
    """
    Tests for validate_password_complexity function.
    Checks that validate_password_complexity returns a list of errors
    and that it correctly validates passwords based on complexity rules.
    """

    def test_valid_password(self):
        errors = validate_password_complexity("StrongP@ss1")
        assert errors == []

    def test_too_short(self):
        errors = validate_password_complexity("Aa1!")
        assert any("at least 8 characters" in e for e in errors)

    def test_no_uppercase(self):
        errors = validate_password_complexity("lowercase1!")
        assert any("uppercase" in e for e in errors)

    def test_no_lowercase(self):
        errors = validate_password_complexity("UPPERCASE1!")
        assert any("lowercase" in e for e in errors)

    def test_no_digit(self):
        errors = validate_password_complexity("NoDigits!!")
        assert any("digit" in e for e in errors)

    def test_no_special_char(self):
        errors = validate_password_complexity("NoSpecial1A")
        assert any("special character" in e for e in errors)

    def test_all_rules_violated(self):
        errors = validate_password_complexity("abc")
        assert len(errors) >= 3
