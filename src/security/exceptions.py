"""
Custom security exceptions.

Provides a hierarchy of exceptions for authentication
and authorization errors, including JWT token.
"""


class BaseSecurityError(Exception):
    """Base exception for all security-related errors."""
    pass


class TokenExpiredError(BaseSecurityError):
    """Raised when a JWT token has expired."""

    def __init__(self, message: str = "Token has expired."):
        super().__init__(message)


class InvalidTokenError(BaseSecurityError):
    """Raised when a JWT token is invalid or malformed."""

    def __init__(self, message: str = "Invalid token."):
        super().__init__(message)
