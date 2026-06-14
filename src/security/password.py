"""
Password hashing and validation utilities.

Uses passlib with bcrypt for secure password hashing.
Enforces password complexity rules for registration and password changes.
"""

import re

from passlib.context import CryptContext


# Bcrypt password hashing context.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password: The plain-text password to hash.

    Returns:
        str: The bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The plain-text password to verify.
        hashed_password: The stored bcrypt hash.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_complexity(password: str) -> list[str]:
    """
    Validate password complexity requirements.

    Rules:
    - Minimum 8 characters.
    - At least one uppercase letter.
    - At least one lowercase letter.
    - At least one digit.
    - At least one special character (!@#$%^&*).

    Args:
        password: The password string to validate.

    Returns:
        list[str]: A list of validation error messages. Empty if valid.
    """
    errors: list[str] = []

    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character.")

    return errors
