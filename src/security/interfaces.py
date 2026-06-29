"""
Abstract interfaces for security components.

Defines contracts for JWT authentication management and S3 storage,
enabling dependency injection and easy testing with mock implementations.
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


class S3StorageInterface(ABC):
    """
    Interface for S3-compatible object storage operations.

    Implementations must provide methods for uploading files
    and generating pre-signed URLs for file access.
    """

    @abstractmethod
    async def upload_file(self, file_name: str, file_data: bytes) -> None:
        """
        Upload a file to S3 storage.

        Args:
            file_name: The key/path for the file in the bucket.
            file_data: The raw file bytes to upload.

        Raises:
            S3FileUploadError: If the upload fails.
        """
        ...

    @abstractmethod
    async def get_file_url(self, file_name: str) -> str:
        """
        Generate a pre-signed URL for accessing a file.

        Args:
            file_name: The key/path of the file in the bucket.

        Returns:
            str: A pre-signed URL for the file.
        """
        ...


class EmailSenderInterface(ABC):
    """An interface for email senders."""

    @abstractmethod
    async def send_activation_email(
            self,
            email: str,
            activation_link: str
    ) -> None:
        """Asynchronously sends an account activation email."""
        ...

    @abstractmethod
    async def send_activation_complete_email(
            self,
            email: str,
            login_link: str
    ) -> None:
        """
        It sends a message confirming successful activation asynchronously.
        """
        ...

    @abstractmethod
    async def send_password_reset_email(
            self,
            email: str,
            reset_link: str
    ) -> None:
        """Asynchronously sends an email requesting a password reset."""
        ...

    @abstractmethod
    async def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        """
        It sends a message confirming the successful
        password reset asynchronously.
        """
        ...
