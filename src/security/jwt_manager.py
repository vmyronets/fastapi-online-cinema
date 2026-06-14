"""
JWT authentication manager implementation.

Provides concrete implementation of JWTAuthManagerInterface using
python-jose for token encoding/decoding with HS256 algorithm.
Handles access and refresh token lifecycle with configurable TTLs.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import jwt, JWTError

from src.config.settings import settings
from src.security.interfaces import JWTAuthManagerInterface
from src.security.exceptions import TokenExpiredError, InvalidTokenError


class JWTAuthManager(JWTAuthManagerInterface):
    """
    JWT authentication manager using python-jose.

    Creates and validates access/refresh tokens with configurable
    expiration times. Access tokens have a shorter TTL for security,
    while refresh tokens allow obtaining new access tokens.

    Attributes:
        secret_key: Secret key for signing tokens.
        algorithm: JWT signing algorithm (default: HS256).
        access_token_expire_minutes: Access token TTL in minutes.
        refresh_token_expire_days: Refresh token TTL in days.
    """

    def __init__(self) -> None:
        """Initialize JWT manager with settings from application config."""
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, data: dict[str, Any]) -> str:
        """
        Create a JWT access token with a short TTL.

        Args:
            data: Payload data (must include 'user_id').

        Returns:
            str: Encoded JWT access token.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, data: dict[str, Any]) -> str:
        """
        Create a JWT refresh token with a longer TTL.

        Args:
            data: Payload data (must include 'user_id').

        Returns:
            str: Encoded JWT refresh token.
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)

    def decode_access_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT access token.

        Args:
            token: The JWT access token string.

        Returns:
            dict: Decoded payload containing user_id and metadata.

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is malformed or not an access token.
        """
        return self._decode_token(token, expected_type="access")

    def decode_refresh_token(self, token: str) -> dict[str, Any]:
        """
        Decode and validate a JWT refresh token.

        Args:
            token: The JWT refresh token string.

        Returns:
            dict: Decoded payload containing user_id and metadata.

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is malformed or not a refresh token.
        """
        return self._decode_token(token, expected_type="refresh")

    def _decode_token(self, token: str, expected_type: str) -> dict[str, Any]:
        """
        Internal method to decode and validate a JWT token.

        Steps:
        - Decode the token using the secret key and algorithm.
        - Verify the token type matches the expected type.
        - Check that the token has not expired.

        Args:
            token: The JWT token string.
            expected_type: Expected token type ('access' or 'refresh').

        Returns:
            dict: Decoded token payload.

        Raises:
            TokenExpiredError: If the token has expired.
            InvalidTokenError: If the token is invalid or type mismatch.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
        except JWTError:
            raise InvalidTokenError("Token is invalid or malformed.")

        # Verify token type matches expected type.
        token_type = payload.get("type")
        if token_type != expected_type:
            raise InvalidTokenError(f"Expected {expected_type} token, got {token_type}.")

        # Check expiration.
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            raise TokenExpiredError()

        return payload
