"""
FastAPI security dependencies.

Provides dependency injection functions for extracting JWT tokens
from request headers and instantiating security service objects.
"""
from typing import cast, Annotated

from fastapi import Header, Depends, HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from notifications import EmailSenderInterface
from notifications.emails import get_email_sender
from security.exceptions import BaseSecurityError
from src.accounts.models import UserModel, UserGroupEnum

from src.security.interfaces import JWTAuthManagerInterface, S3StorageInterface
from src.security.jwt_manager import JWTAuthManager
from src.s3.client import S3StorageClient


# AsyncSession dependency
SessionDep = Annotated[AsyncSession, Depends(get_db)]

# EmailSenderInterface dependency
EmailSenderDep = Annotated[
    EmailSenderInterface, Depends(get_email_sender)
]


def get_token(
        authorization: str = Header(..., description="Bearer token")
) -> str:
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
            detail="Invalid authorization header format. "
                   "Expected 'Bearer <token>'."
        )
    return authorization[7:]


def get_jwt_auth_manager() -> JWTAuthManagerInterface:
    """
    Provide a JWTAuthManager instance for dependency injection.

    Returns:
        JWTAuthManagerInterface: A configured JWT authentication manager.
    """
    return JWTAuthManager()


def get_s3_storage_client() -> S3StorageInterface:
    """
    Provide an S3StorageClient instance for dependency injection.

    Returns:
        S3StorageInterface: A configured S3 storage client.
    """
    return S3StorageClient()


def decode_token(token: str, jwt_manager: JWTAuthManagerInterface) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: The raw JWT token string.
        jwt_manager: JWT manager instance for decoding.

    Returns:
        dict: The decoded token payload.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        return jwt_manager.decode_access_token(token)
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


# JWTAuthManagerInterface dependency
JWTManagerDep = Annotated[
    JWTAuthManagerInterface, Depends(get_jwt_auth_manager)
]


async def get_current_user(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token)
) -> UserModel:
    payload = decode_token(token, jwt_manager)
    user_id = cast(int, payload["user_id"])

    current_user = (
        await db.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
    ).scalars().first()

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    return cast(UserModel, current_user)


async def require_admin_or_moderator(
        current_user: UserModel = Depends(get_current_user)
) -> UserModel:
    if current_user.group.name not in {
        UserGroupEnum.ADMIN,
        UserGroupEnum.MODERATOR
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or Admin access required."
        )

    return current_user
