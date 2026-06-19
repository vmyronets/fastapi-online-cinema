"""
Pydantic schemas for the accounts module.

Defines request/response schemas for user registration, login,
profile management, token operations, and password management.
Uses Pydantic v2 model_config and field validators.
"""

from datetime import date, datetime
from typing import Optional

from fastapi import UploadFile, File, Form
from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


# ----------------------------------------------
# Registration & Activation
# ----------------------------------------------

class UserRegisterSchema(BaseModel):
    """
    Schema for user registration request.

    Attributes:
        email: User's email address (must be valid and unique).
        password: User's password (must meet complexity requirements).
    """
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    model_config = {
        "json_schema_extra": {
            "example": {"email": "user@example.com", "password": "StrongP@ss1"}
        }
    }


class UserResponseSchema(BaseModel):
    """
    Schema for user response after registration or retrieval.

    Attributes:
        id: The user's unique identifier.
        email: The user's email address.
        is_active: Whether the account is activated.
        created_at: Account creation timestamp.
        group: The user's group/role name.
    """
    id: int
    email: str
    is_active: bool
    created_at: datetime
    group: str

    model_config = {"from_attributes": True}


class ActivationRequestSchema(BaseModel):
    """
    Schema for account activation request.

    Attributes:
        email: Email address to send a new activation link.
        token: The activation token from the email link.
    """
    email: Optional[EmailStr] = None
    token: Optional[str] = None

    @model_validator(mode="after")
    def check_at_least_one(self) -> "ActivationRequestSchema":
        """Ensure at least one of email or token is provided."""
        if not self.email and not self.token:
            raise ValueError("Either 'email' or 'token' must be provided.")
        return self


class ResendActivationSchema(BaseModel):
    """
    Schema for resending activation email.

    Attributes:
        email: The email address to resend the activation link to.
    """
    email: EmailStr


# ----------------------------------------------
# Login & Tokens
# ----------------------------------------------

class LoginSchema(BaseModel):
    """
    Schema for user login request.

    Attributes:
        email: User's email address.
        password: User's password.
    """
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    """
    Schema for JWT token pair response.

    Attributes:
        access_token: Short-lived access token.
        refresh_token: Long-lived refresh token.
        token_type: Token type (always 'bearer').
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenSchema(BaseModel):
    """
    Schema for token refresh request.

    Attributes:
        refresh_token: The refresh token to exchange for a new access token.
    """
    refresh_token: str


class AccessTokenResponseSchema(BaseModel):
    """
    Schema for refreshed access token response.

    Attributes:
        access_token: The new short-lived access token.
        token_type: Token type (always 'bearer').
    """
    access_token: str
    token_type: str = "bearer"


# ----------------------------------------------
# Password Management
# ----------------------------------------------

class ChangePasswordSchema(BaseModel):
    """
    Schema for changing password (user knows old password).

    Attributes:
        old_password: The current password.
        new_password: The new password (must meet complexity requirements).
    """
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class PasswordResetRequestSchema(BaseModel):
    """
    Schema for requesting a password reset email.

    Attributes:
        email: The email address associated with the account.
    """
    email: EmailStr


class PasswordResetConfirmSchema(BaseModel):
    """
    Schema for confirming password reset with token.

    Attributes:
        token: The password reset token from the email.
        new_password: The new password (must meet complexity requirements).
    """
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ----------------------------------------------
# User Profile
# ----------------------------------------------

class ProfileCreateSchema:
    """
    Schema for creating a user profile via multipart form data.

    Supports file upload for avatar via form fields.

    Attributes:
        first_name: User's first name (optional).
        last_name: User's last name (optional).
        gender: Gender enum value (optional).
        date_of_birth: Date of birth (optional).
        info: Short bio text (optional).
        avatar: Uploaded avatar image file.
    """

    def __init__(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        gender: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        info: Optional[str] = None,
        avatar: Optional[UploadFile] = None,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.info = info
        self.avatar = avatar

    @classmethod
    def from_form(
        cls,
        first_name: Optional[str] = Form(None),
        last_name: Optional[str] = Form(None),
        gender: Optional[str] = Form(None),
        date_of_birth: Optional[date] = Form(None),
        info: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None),
    ) -> "ProfileCreateSchema":
        """
        Create a ProfileCreateSchema instance from multipart form data.

        Args:
            first_name: User's first name.
            last_name: User's last name.
            gender: Gender value (MAN/WOMAN).
            date_of_birth: Date of birth.
            info: Short bio text.
            avatar: Uploaded avatar file.

        Returns:
            ProfileCreateSchema: Populated schema instance.
        """
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            info=info,
            avatar=avatar,
        )


class ProfileResponseSchema(BaseModel):
    """
    Schema for user profile response.

    Attributes:
        id: Profile unique identifier.
        user_id: Associated user ID.
        first_name: User's first name.
        last_name: User's last name.
        gender: Gender value.
        date_of_birth: Date of birth.
        info: Short bio text.
        avatar: Pre-signed URL for the avatar image.
    """
    id: int
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    info: Optional[str] = None
    avatar: Optional[HttpUrl] = None

    model_config = {"from_attributes": True}


class ProfileUpdateSchema:
    """
    Schema for updating a user profile via multipart form data.

    All fields are optional — only provided fields will be updated.

    Attributes:
        first_name: Updated first name (optional).
        last_name: Updated last name (optional).
        gender: Updated gender (optional).
        date_of_birth: Updated date of birth (optional).
        info: Updated bio text (optional).
        avatar: New avatar image file (optional).
    """

    def __init__(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        gender: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        info: Optional[str] = None,
        avatar: Optional[UploadFile] = None,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.date_of_birth = date_of_birth
        self.info = info
        self.avatar = avatar

    @classmethod
    def from_form(
        cls,
        first_name: Optional[str] = Form(None),
        last_name: Optional[str] = Form(None),
        gender: Optional[str] = Form(None),
        date_of_birth: Optional[date] = Form(None),
        info: Optional[str] = Form(None),
        avatar: Optional[UploadFile] = File(None),
    ) -> "ProfileUpdateSchema":
        """
        Create a ProfileUpdateSchema instance from multipart form data.

        Args:
            first_name: Updated first name.
            last_name: Updated last name.
            gender: Updated gender value.
            date_of_birth: Updated date of birth.
            info: Updated bio text.
            avatar: New avatar file.

        Returns:
            ProfileUpdateSchema: Populated schema instance.
        """
        return cls(
            first_name=first_name,
            last_name=last_name,
            gender=gender,
            date_of_birth=date_of_birth,
            info=info,
            avatar=avatar,
        )


# ----------------------------------------------
# Admin: User Management
# ----------------------------------------------

class AdminUserUpdateSchema(BaseModel):
    """
    Schema for admin operations on user accounts.

    Attributes:
        is_active: Set user activation status.
        group_name: Change user's group/role.
    """
    is_active: Optional[bool] = None
    group_name: Optional[str] = None


class MessageSchema(BaseModel):
    """
    Generic message response schema.

    Attributes:
        detail: The response message text.
    """
    detail: str
