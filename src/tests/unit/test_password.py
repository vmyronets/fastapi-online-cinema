from src.security.password import (
    hash_password,
    verify_password
)


class TestHashPassword:
    """Tests for hash_password and verify_password functions."""

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
