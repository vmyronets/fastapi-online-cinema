"""
Abstract interfaces for security components.

Defines contracts for JWT authentication management, enabling
dependency injection and easy testing with mock implementations.
"""

from abc import ABC, abstractmethod
from typing import Any


class JWTAuthManagerInterface(ABC):
    """
    Interface for JWT authentication management.

    Implementations must provide methods for creating and decoding
    both access and refresh tokens.
    """

    @abstractmethod
    def create_access_token(self, data: dict[str, Any]) -> str:
        """
        Create a new JWT access token.

        Args:
            data: Payload data to encode in the token (e.g., user_id).

        Returns:
            str: The encoded JWT access token string.
        """
        ...

    @abstractmethod
    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """
        Create a new JWT refresh token.

        Args:
            data: Payload data to encode in the token (e.g., user_id).

        Returns:
            str: The encoded JWT refresh token string.
        """
        ...

    @abstractmethod
    def decode_access_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT access token.

        Args:
            token: The JWT access token string.

        Returns:
            dict: The decoded token payload.

        Raises:
            BaseSecurityError: If the token is invalid or expired.
        """
        ...

    @abstractmethod
    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT refresh token.

        Args:
            token: The JWT refresh token string.

        Returns:
            dict: The decoded token payload.

        Raises:
            BaseSecurityError: If the token is invalid or expired.
        """
        ...
