"""
FastAPI security dependencies.

Provides dependency injection functions for extracting JWT tokens
from request headers and instantiating security service objects.
"""

from fastapi import Header, HTTPException, status

from src.security.interfaces import JWTAuthManagerInterface
from src.security.jwt_manager import JWTAuthManager


def get_token(authorization: str = Header(..., description="Bearer token")) -> str:
    """
    Extract the JWT token from the Authorization header.

    Expects the header in the format: 'Bearer <token>'.

    Args:
        authorization: The raw Authorization header value.

    Returns:
        str: The extracted JWT token string.

    Raises:
        HTTPException: If the header format is invalid or missing.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'."
        )
    return authorization[7:]


def get_jwt_auth_manager() -> JWTAuthManagerInterface:
    """
    Provide a JWTAuthManager instance for dependency injection.

    Returns:
        JWTAuthManagerInterface: A configured JWT authentication manager.
    """
    return JWTAuthManager()
