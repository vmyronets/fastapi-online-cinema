"""
API routes for the accounts module.

Provides endpoints for user registration, activation, login/logout,
token refresh, password management, profile CRUD, and admin user management.
"""

import secrets
from datetime import (
    datetime,
    timedelta,
    timezone
)
from typing import cast

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Request
)
from fastapi.responses import HTMLResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.security.dependencies import (
    SessionDep,
    EmailSenderDep,
    JWTManagerDep
)
from src.accounts.models import (
    UserModel,
    UserGroupModel,
    UserProfileModel,
    ActivationTokenModel,
    PasswordResetTokenModel,
    RefreshTokenModel,
    UserGroupEnum,
    GenderEnum
)
from src.accounts.schemas import (
    UserRegisterSchema,
    UserResponseSchema,
    ActivationRequestSchema,
    ResendActivationSchema,
    LoginSchema,
    TokenResponseSchema,
    RefreshTokenSchema,
    AccessTokenResponseSchema,
    ChangePasswordSchema,
    PasswordResetRequestSchema,
    PasswordResetConfirmSchema,
    ProfileCreateSchema,
    ProfileResponseSchema,
    ProfileUpdateSchema,
    AdminUserUpdateSchema,
    MessageSchema
)
from src.database.session import get_db
from src.security.dependencies import (
    get_token,
    get_s3_storage_client,
    decode_token
)
from src.security.exceptions import BaseSecurityError, S3FileUploadError
from src.security.interfaces import JWTAuthManagerInterface, S3StorageInterface
from src.security.password import (
    hash_password,
    verify_password,
    validate_password_complexity
)
from src.notifications.interfaces import EmailSenderInterface


router = APIRouter(prefix="/accounts", tags=["Accounts"])


# ----------------------------------------------
# Helper: decode token and get user_id
# ----------------------------------------------

async def _get_active_user(db: AsyncSession, user_id: int) -> UserModel:
    """
    Retrieve an active user by ID.

    Args:
        db: Async database session.
        user_id: The user's ID.

    Returns:
        UserModel: The active user instance.

    Raises:
        HTTPException: If user not found or not active.
    """
    stmt = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or not active."
        )
    return cast(UserModel, user)


async def _check_permission(
    db: AsyncSession, token_user_id: int, target_user_id: int
) -> None:
    """
    Check if the token owner has permission to act on the target user.

    Allows action if the token owner is the target user, or if the
    token owner belongs to MODERATOR or ADMIN group.

    Args:
        db: Async database session.
        token_user_id: The user ID from the JWT token.
        target_user_id: The user ID being acted upon.

    Raises:
        HTTPException: If the token owner lacks permission.
    """
    if token_user_id == target_user_id:
        return
    stmt = (
        select(UserGroupModel)
        .join(UserModel)
        .where(UserModel.id == token_user_id)
    )
    result = await db.execute(stmt)
    user_group = result.scalars().first()
    if not user_group or user_group.name == UserGroupEnum.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to perform this action."
        )


# ----------------------------------------------
# Registration
# ----------------------------------------------

@router.post(
    "/register/",
    response_model=UserResponseSchema,
    summary="Register a new user",
    status_code=status.HTTP_201_CREATED
)
async def register(
    data: UserRegisterSchema,
    db: SessionDep,
    background_tasks: BackgroundTasks,
    request: Request,
    email_sender: EmailSenderDep
) -> UserResponseSchema:
    """
    Register a new user account and send activation email in a background task.

    Steps:
    - Validate password complexity.
    - Check email uniqueness.
    - Create user with default USER group and inactive status.
    - Generate activation token (valid 24 hours).
    - Send activation email.

    Args:
        data (UserRegisterSchema): Registration data with email and password.
        db (AsyncSession): The asynchronous database session.
        background_tasks (BackgroundTasks): Background tasks manager.
        request (Request): The incoming request object.
        email_sender (EmailSenderInterface): Email sender interface.

    Returns:
        UserResponseSchema: The created user details.

    Raises:
        HTTPException: If password is weak, email already exists, or USER group not found.
    """
    # Validate password complexity.
    password_errors = validate_password_complexity(data.password)
    if password_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_errors
        )

    # Check email uniqueness.
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # Get default USER group.
    stmt_group = (
        select(UserGroupModel)
        .where(UserGroupModel.name == UserGroupEnum.USER)
    )
    result_group = await db.execute(stmt_group)
    group = result_group.scalars().first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Default user group not found. Please contact support."
        )

    # Create user.
    user = UserModel(
        email=data.email,
        hashed_password=hash_password(data.password),
        is_active=False,
        group_id=cast(int, group.id)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Create activation token (expires in 24 hours).
    activation_token = ActivationTokenModel(
        user_id=cast(int, user.id),
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(activation_token)
    await db.commit()

    # Create activation link for sending in email
    activation_link = (
        f"{request.base_url}/accounts/activate/"
        f"?token={activation_token.token}"
    )

    # Send activation email in background task.
    background_tasks.add_task(
        email_sender.send_activation_email,
        user.email,
        activation_link
    )

    return UserResponseSchema(
        id=user.id,
        email=user.email,
        is_active=user.is_active,
        created_at=user.created_at,
        group=group.name
    )


# ----------------------------------------------
# Activation
# ----------------------------------------------

@router.post(
    "/activate/",
    response_model=MessageSchema,
    summary="Activate user account",
)
async def activate_account(
    data: ActivationRequestSchema,
    db: SessionDep,
    background_tasks: BackgroundTasks,
    request: Request,
    email_sender: EmailSenderDep
) -> MessageSchema:
    """
    Activate a user account using the activation token.

    Steps:
    - Look up the activation token in the database.
    - Verify the token has not expired.
    - Set the user's is_active flag to True.
    - Delete the used activation token.
    - Send welcome email.

    Args:
        data (ActivationRequestSchema): Contains the activation token.
        db (AsyncSession): The asynchronous database session.
        background_tasks (BackgroundTasks): Background tasks manager.
        request (Request): The incoming request.
        email_sender (EmailSenderDep): Email sender dependency.

    Returns:
        MessageSchema: Confirmation message.

    Raises:
        HTTPException: If token is invalid or expired.
    """
    if not data.token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token is required."
        )

    stmt = (
        select(ActivationTokenModel)
        .where(ActivationTokenModel.token == data.token)
    )
    result = await db.execute(stmt)
    activation = result.scalars().first()

    if not activation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid activation token."
        )

    if (
        activation.expires_at.replace(tzinfo=timezone.utc)
        < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token has expired. Please request a new one."
        )

    # Activate the user.
    stmt_user = select(UserModel).where(UserModel.id == activation.user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()
    if user:
        user.is_active = True
        await db.delete(activation)
        await db.commit()

    login_link = f"{request.base_url}docs"
    background_tasks.add_task(
        email_sender.send_activation_complete_email,
        user.email,
        login_link
    )

    return MessageSchema(detail="Account activated successfully.")


@router.get(
    "/activate/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def activate_account_get(
    token: str,
    background_tasks: BackgroundTasks,
    request: Request,
    email_sender: EmailSenderDep,
    db: SessionDep
):
    """
    GET-endpoint for activating an account by clicking a link in the email.
    Returns a visible HTML page instead of a JSON response.

    Args:
        token (str): The activation token.
        background_tasks (BackgroundTasks): Background tasks manager.
        request (Request): The request object.
        email_sender (EmailSenderDep): Email sender dependency.
        db (SessionDep): The database session dependency.

    Returns:
        HTMLResponse: A HTML page with a success message.

    Raises:
        HTTPException: If the activation token is invalid or expired.
    """
    try:
        await activate_account(
            ActivationRequestSchema(token=token),
            db,
            background_tasks,
            request,
            email_sender,
        )
        return """
        <html><body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: green;">Your account has been successfully activated! 🚀</h2>
            <p>You can now close this page and log in.</p>
        </body></html>
        """
    except HTTPException as e:
        return f"""
        <html><body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
            <h2 style="color: red;">Activation failed! 🚨</h2>
            <p>{e.detail}</p>
        </body></html>
"""


@router.post(
    "/activate/resend/",
    response_model=MessageSchema,
    summary="Resend activation email"
)
async def resend_activation(
    data: ResendActivationSchema,
    db: SessionDep,
) -> MessageSchema:
    """
    Resend activation token for an inactive account.

    Steps:
    - Find user by email.
    - Verify user exists and is not already active.
    - Delete any existing activation token.
    - Create a new activation token (valid 24 hours).

    Args:
        data (ResendActivationSchema): Contains the user's email.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageSchema: Confirmation message.

    Raises:
        HTTPException: If user not found or already active.
    """
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email not found."
        )

    if user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is already active."
        )

    # Delete existing activation token if any.
    stmt_del = (
        select(ActivationTokenModel)
        .where(ActivationTokenModel.user_id == user.id)
    )
    result_del = await db.execute(stmt_del)
    existing = result_del.scalars().first()
    if existing:
        await db.delete(existing)

    # Create new activation token.
    new_token = ActivationTokenModel(
        user_id=cast(int, user.id),
        token=secrets.token_urlsafe(32),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(new_token)
    await db.commit()

    return MessageSchema(detail="Activation email resent successfully.")


# ----------------------------------------------
# Login / Logout
# ----------------------------------------------

@router.post(
    "/login/",
    response_model=TokenResponseSchema,
    summary="User login",
)
async def login(
    data: LoginSchema,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
) -> TokenResponseSchema:
    """
    Authenticate user and issue JWT token pair.

    Steps:
    - Find user by email.
    - Verify password.
    - Check account is active.
    - Generate access and refresh tokens.
    - Store refresh token in database.

    Args:
        data (LoginSchema): Login credentials (email, password).
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for token creation.

    Returns:
        TokenResponseSchema: Access and refresh token pair.

    Raises:
        HTTPException: If credentials are invalid or account is inactive.
    """
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not activated. Please check your email."
        )

    # Generate JWT tokens.
    access_token = jwt_manager.create_access_token({"user_id": user.id})
    refresh_token = jwt_manager.create_refresh_token({"user_id": user.id})

    # Store refresh token in database.
    refresh_token_model = RefreshTokenModel(
        user_id=cast(int, user.id),
        token=refresh_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(refresh_token_model)
    await db.commit()

    return TokenResponseSchema(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.post(
    "/logout/",
    response_model=MessageSchema,
    summary="User logout",
)
async def logout(
    data: RefreshTokenSchema,
    db: AsyncSession = Depends(get_db),
) -> MessageSchema:
    """
    Logout user by revoking their current refresh token.

    Steps:
    - Decode the access token to identify the user.
    - Delete the current refresh token for the user.

    Args:
        data: Refresh token schema.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageSchema: Confirmation message.

    Raises:
        HTTPException: If authentication fails.
    """

    # Delete current refresh token for this user.
    stmt = (
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token == data.refresh_token)
    )
    result = await db.execute(stmt)
    token_obj = result.scalars().first()
    if token_obj:
        await db.delete(token_obj)
        await db.commit()

    return MessageSchema(detail="Successfully logged out.")


# ----------------------------------------------
# Token Refresh
# ----------------------------------------------

@router.post(
    "/token/refresh/",
    response_model=AccessTokenResponseSchema,
    summary="Refresh access token",
)
async def refresh_access_token(
    data: RefreshTokenSchema,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
) -> AccessTokenResponseSchema:
    """
    Exchange a valid refresh token for a new access token.

    Steps:
    - Decode and validate the refresh token.
    - Verify the refresh token exists in the database.
    - Generate a new access token.

    Args:
        data (RefreshTokenSchema): Contains the refresh token.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for token operations.

    Returns:
        AccessTokenResponseSchema: The new access token.

    Raises:
        HTTPException: If refresh token is invalid, expired, or revoked.
    """
    try:
        payload = jwt_manager.decode_refresh_token(data.refresh_token)
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

    # Verify token exists in database (not revoked).
    stmt = (
        select(RefreshTokenModel)
        .where(RefreshTokenModel.token == data.refresh_token)
    )
    result = await db.execute(stmt)
    stored_token = result.scalars().first()
    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked."
        )

    # Generate new access token.
    user_id = payload.get("user_id")
    new_access_token = jwt_manager.create_access_token({"user_id": user_id})

    return AccessTokenResponseSchema(access_token=new_access_token)


# ----------------------------------------------
# Password Management
# ----------------------------------------------

@router.post(
    "/password/change/",
    response_model=MessageSchema,
    summary="Change password",
)
async def change_password(
    data: ChangePasswordSchema,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
) -> MessageSchema:
    """
    Change password for authenticated user.

    Steps:
    - Decode access token to identify user.
    - Verify old password matches.
    - Validate new password complexity.
    - Update password hash in database.

    Args:
        data (ChangePasswordSchema): Old and new passwords.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageSchema: Confirmation message.

    Raises:
        HTTPException: If old password is wrong or new password is weak.
    """
    payload = decode_token(token, jwt_manager)
    user = await _get_active_user(db, cast(int, payload.get("user_id")))

    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect."
        )

    password_errors = validate_password_complexity(data.new_password)
    if password_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_errors
        )

    # Delete all refresh tokens for this user.
    stmt = (
        select(RefreshTokenModel)
        .where(RefreshTokenModel.user_id == user.id)
    )
    result = await db.execute(stmt)
    refresh_tokens = result.scalars().all()
    for token in refresh_tokens:
        await db.delete(token)

    user.hashed_password = hash_password(data.new_password)
    await db.commit()

    return MessageSchema(detail="Password changed successfully.")


@router.post(
    "/password/reset/",
    response_model=MessageSchema,
    summary="Request password reset",
)
async def request_password_reset(
    data: PasswordResetRequestSchema,
    db: SessionDep,
    background_tasks: BackgroundTasks,
    request: Request,
    email_sender: EmailSenderDep,
) -> MessageSchema:
    """
    Request a password reset and background
    sending an email with link to reset password.

    Steps:
    - Find user by email.
    - Verify user exists and is active.
    - Delete any existing reset token.
    - Create a new password reset token.
    - Send password reset email.

    Args:
        data (PasswordResetRequestSchema): Contains the user's email.
        db (AsyncSession): The asynchronous database session.
        background_tasks (BackgroundTasks): Background tasks manager.
        request (Request): The incoming request object.
        email_sender (EmailSenderDep): Email sender dependency.

    Returns:
        MessageSchema: Confirmation message (always returns success for security).

    Raises:
        HTTPException: None (always returns success to prevent email enumeration).
    """
    stmt = select(UserModel).where(UserModel.email == data.email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if user and user.is_active:
        # Delete existing reset token if any.
        stmt_del = select(PasswordResetTokenModel).where(
            PasswordResetTokenModel.user_id == user.id
        )
        result_del = await db.execute(stmt_del)
        existing = result_del.scalars().first()
        if existing:
            await db.delete(existing)

        # Create new reset token.
        reset_token = PasswordResetTokenModel(
            user_id=cast(int, user.id),
            token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        db.add(reset_token)
        await db.commit()

        reset_link = (
            f"{request.base_url}accounts/password/"
            f"reset/confirm/?token={reset_token.token}"
        )
        background_tasks.add_task(
            email_sender.send_password_reset_email,
            user.email,
            reset_link
        )

    # Always return success to prevent email enumeration.
    return MessageSchema(
        detail="If the email is registered, a reset link has been sent."
    )


@router.post(
    "/password/reset/confirm/",
    response_model=MessageSchema,
    summary="Confirm password reset",
)
async def confirm_password_reset(
    data: PasswordResetConfirmSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    email_sender: EmailSenderDep,
    db: SessionDep
) -> MessageSchema:
    """
    Reset password using a valid reset token.

    Steps:
    - Look up the reset token.
    - Verify it has not expired.
    - Validate new password complexity.
    - Update the user's password hash.
    - Delete the used reset token.
    - Send confirmation email.

    Args:
        data (PasswordResetConfirmSchema): Reset token and new password.
        background_tasks (BackgroundTasks): Background tasks.
        request (Request): The request object.
        email_sender (EmailSenderDep): Email sender dependency.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageSchema: Confirmation message.

    Raises:
        HTTPException: If token is invalid/expired or password is weak.
    """
    stmt = select(PasswordResetTokenModel).where(
        PasswordResetTokenModel.token == data.token
    )
    result = await db.execute(stmt)
    reset = result.scalars().first()

    if not reset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token."
        )

    if (
        reset.expires_at.replace(tzinfo=timezone.utc)
        < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired."
        )

    password_errors = validate_password_complexity(data.new_password)
    if password_errors:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=password_errors
        )

    # Update password.
    stmt_user = select(UserModel).where(UserModel.id == reset.user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()
    if user:
        user.hashed_password = hash_password(data.new_password)

        refresh_tokens = (
            await db.execute(
                select(RefreshTokenModel)
                .where(RefreshTokenModel.user_id == user.id)
            )
        ).scalars().all()
        for token in refresh_tokens:
            await db.delete(token)

        await db.delete(reset)
        await db.commit()

        login_link = f"{request.base_url}docs"
        background_tasks.add_task(
            email_sender.send_password_reset_complete_email,
            user.email,
            login_link
        )

    return MessageSchema(detail="Password reset successfully.")


@router.get(
    "/password/reset/confirm/",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def password_reset_form_get(token: str):
    """
    The GET endpoint that the user is redirected to from the email.
    It returns an HTML form that uses JavaScript to send a POST request
    to our main JSON endpoint.
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Setting a New Password</title>
        <style>
            body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f4f4f9; }}
            .card {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 300px; text-align: center; }}
            input {{ width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }}
            button {{ width: 100%; padding: 10px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }}
            button:hover {{ background: #0056b3; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h3>Enter a new password</h3>
            <input type="password" id="new_password" placeholder="New password (at least 8 characters)">
            <button onclick="submitPassword()">Save</button>
            <p id="message" style="color: red; font-size: 14px;"></p>
        </div>
        <script>
            async function submitPassword() {{
                const password = document.getElementById('new_password').value;
                const msgEl = document.getElementById('message');
                msgEl.style.color = '#333';
                msgEl.innerText = 'Processing...';

                const response = await fetch('/accounts/password/reset/confirm/', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ token: "{token}", new_password: password }})
                }});

                const data = await response.json();
                if (response.ok) {{
                    msgEl.style.color = 'green';
                    msgEl.innerText = 'Your password has been successfully changed! You can close this window.';
                }} else {{
                    msgEl.style.color = 'red';
                    msgEl.innerText = typeof data.detail === 'string' ? data.detail : data.detail[0];
                }}
            }}
        </script>
    </body>
    </html>
    """


# ----------------------------------------------
# User Profile
# ----------------------------------------------

@router.post(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    summary="Create user profile",
    status_code=status.HTTP_201_CREATED,
)
async def create_profile(
    user_id: int,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    profile_data: ProfileCreateSchema = Depends(ProfileCreateSchema.from_form),
) -> ProfileResponseSchema:
    """
    Creates a user profile.

    Steps:
    - Validate user authentication token.
    - Check if the user already has a profile.
    - Upload avatar to S3 storage.
    - Store profile details in the database.

    Args:
        user_id (int): The ID of the user for whom the profile is being created.
        token (str): The authentication token.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding tokens.
        db (AsyncSession): The asynchronous database session.
        s3_client (S3StorageInterface): The asynchronous S3 storage client.
        profile_data (ProfileCreateSchema): The profile data from the form.

    Returns:
        ProfileResponseSchema: The created user profile details.

    Raises:
        HTTPException: If authentication fails, if the user is not found or inactive,
                       or if the profile already exists, or if S3 upload fails.
    """
    payload = decode_token(token, jwt_manager)
    token_user_id = cast(int, payload.get("user_id"))
    await _check_permission(db, token_user_id, user_id)

    user = await _get_active_user(db, user_id)

    # Check if profile already exists.
    stmt_profile = (
        select(UserProfileModel)
        .where(UserProfileModel.user_id == user.id)
    )
    result_profile = await db.execute(stmt_profile)
    if result_profile.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has a profile.",
        )

    # Upload avatar to S3 if provided.
    avatar_key = None
    if profile_data.avatar:
        avatar_bytes = await profile_data.avatar.read()
        avatar_key = f"avatars/{user.id}_{profile_data.avatar.filename}"
        try:
            await s3_client.upload_file(
                file_name=avatar_key,
                file_data=avatar_bytes
            )
        except S3FileUploadError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload avatar. Please try again later.",
            )

    # Create profile.
    new_profile = UserProfileModel(
        user_id=cast(int, user.id),
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        gender=cast(
            GenderEnum,
            profile_data.gender
        ) if profile_data.gender else None,
        date_of_birth=profile_data.date_of_birth,
        info=profile_data.info,
        avatar=avatar_key,
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)

    # Generate avatar URL if avatar was uploaded.
    avatar_url = None
    if new_profile.avatar:
        avatar_url = await s3_client.get_file_url(new_profile.avatar)

    return ProfileResponseSchema(
        id=new_profile.id,
        user_id=new_profile.user_id,
        first_name=new_profile.first_name,
        last_name=new_profile.last_name,
        gender=new_profile.gender,
        date_of_birth=new_profile.date_of_birth,
        info=new_profile.info,
        avatar=avatar_url,
    )


@router.get(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    summary="Get user profile",
)
async def get_profile(
    user_id: int,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
) -> ProfileResponseSchema:
    """
    Retrieve a user's profile.

    Steps:
    - Validate authentication token.
    - Fetch the user's profile from the database.
    - Generate a pre-signed URL for the avatar.

    Args:
        user_id (int): The ID of the user whose profile to retrieve.
        token (str): The authentication token.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        db (AsyncSession): The asynchronous database session.
        s3_client (S3StorageInterface): S3 client for avatar URL generation.

    Returns:
        ProfileResponseSchema: The user's profile details.

    Raises:
        HTTPException: If authentication fails or profile not found.
    """
    decode_token(token, jwt_manager)

    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )

    avatar_url = None
    if profile.avatar:
        avatar_url = await s3_client.get_file_url(profile.avatar)

    return ProfileResponseSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=avatar_url
    )


@router.patch(
    "/users/{user_id}/profile/",
    response_model=ProfileResponseSchema,
    summary="Update user profile",
)
async def update_profile(
    user_id: int,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db),
    s3_client: S3StorageInterface = Depends(get_s3_storage_client),
    profile_data: ProfileUpdateSchema = Depends(ProfileUpdateSchema.from_form),
) -> ProfileResponseSchema:
    """
    Update a user's profile.

    Steps:
    - Validate authentication and permissions.
    - Fetch existing profile.
    - Update only provided fields.
    - Upload new avatar to S3 if provided.

    Args:
        user_id (int): The ID of the user whose profile to update.
        token (str): The authentication token.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        db (AsyncSession): The asynchronous database session.
        s3_client (S3StorageInterface): S3 client for avatar operations.
        profile_data (ProfileUpdateSchema): Updated profile data from form.

    Returns:
        ProfileResponseSchema: The updated profile details.

    Raises:
        HTTPException: If authentication fails, profile not found, or S3 upload fails.
    """
    payload = decode_token(token, jwt_manager)
    token_user_id = cast(int, payload.get("user_id"))
    await _check_permission(db, token_user_id, user_id)

    stmt = select(UserProfileModel).where(UserProfileModel.user_id == user_id)
    result = await db.execute(stmt)
    profile = result.scalars().first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found.",
        )

    # Update only provided fields.
    if profile_data.first_name is not None:
        profile.first_name = profile_data.first_name
    if profile_data.last_name is not None:
        profile.last_name = profile_data.last_name
    if profile_data.gender is not None:
        profile.gender = profile_data.gender
    if profile_data.date_of_birth is not None:
        profile.date_of_birth = profile_data.date_of_birth
    if profile_data.info is not None:
        profile.info = profile_data.info

    # Upload new avatar if provided.
    if profile_data.avatar:
        avatar_bytes = await profile_data.avatar.read()
        avatar_key = f"avatars/{user_id}_{profile_data.avatar.filename}"
        try:
            await s3_client.upload_file(
                file_name=avatar_key,
                file_data=avatar_bytes
            )
        except S3FileUploadError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload avatar. Please try again later.",
            )
        profile.avatar = avatar_key

    await db.commit()
    await db.refresh(profile)

    avatar_url = None
    if profile.avatar:
        avatar_url = await s3_client.get_file_url(profile.avatar)

    return ProfileResponseSchema(
        id=profile.id,
        user_id=profile.user_id,
        first_name=profile.first_name,
        last_name=profile.last_name,
        gender=profile.gender,
        date_of_birth=profile.date_of_birth,
        info=profile.info,
        avatar=avatar_url
    )


# ----------------------------------------------
# Admin: User Management
# ----------------------------------------------

@router.patch(
    "/admin/users/{user_id}/",
    response_model=MessageSchema,
    summary="Admin: update user (activate, change group)",
)
async def admin_update_user(
    user_id: int,
    data: AdminUserUpdateSchema,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db)
) -> MessageSchema:
    """
    Admin endpoint to update user activation status or group.

    Steps:
    - Verify the requester is an ADMIN.
    - Find the target user.
    - Update is_active and/or group as requested.

    Args:
        user_id (int): The ID of the user to update.
        data (AdminUserUpdateSchema): Fields to update.
        token (str): The authentication token.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        db (AsyncSession): The asynchronous database session.

    Returns:
        MessageSchema: Confirmation message.

    Raises:
        HTTPException: If requester is not admin, user not found, or group invalid.
    """
    payload = decode_token(token, jwt_manager)
    admin_user_id = payload.get("user_id")

    # Verify requester is ADMIN.
    stmt_admin = (
        select(UserGroupModel)
        .join(UserModel)
        .where(UserModel.id == admin_user_id)
    )
    result_admin = await db.execute(stmt_admin)
    admin_group = result_admin.scalars().first()
    if not admin_group or admin_group.name != UserGroupEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can perform this action."
        )

    # Find target user.
    stmt_user = select(UserModel).where(UserModel.id == user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    # Update activation status.
    if data.is_active is not None:
        user.is_active = data.is_active

    # Update group.
    if data.group_name is not None:
        stmt_group = (
            select(UserGroupModel)
            .where(UserGroupModel.name == data.group_name)
        )
        result_group = await db.execute(stmt_group)
        new_group = result_group.scalars().first()
        if not new_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Group '{data.group_name}' not found."
            )
        user.group_id = new_group.id

    await db.commit()

    return MessageSchema(detail="User updated successfully.")
