"""
User ORM model.

Represents the users table storing registered user accounts
with email, hashed password, activation status, and group membership.
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from src.database.session import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models.user_group import UserGroupModel
    from src.accounts.models.user_profile import UserProfileModel
    from src.accounts.models.activation_token import ActivationTokenModel
    from src.accounts.models.password_reset_token import PasswordResetTokenModel
    from src.accounts.models.refresh_token import RefreshTokenModel
    from src.payments.models.payment import PaymentModel


class UserModel(Base):
    """
    SQLAlchemy model for the user's table.

    Attributes:
        id: Primary key (int), auto-incremented.
        email: User's email, unique and required.
        hashed_password: Bcrypt-hashed password string.
        is_active: Whether the account is activated (default False).
        created_at: Timestamp of account creation.
        updated_at: Timestamp of last update.
        group_id: Foreign key to user_groups table.

    Relationships:
        group: Many-to-one with UserGroupModel.
        profile: One-to-one with UserProfileModel.
        activation_token: One-to-one with ActivationTokenModel.
        password_reset_token: One-to-one with PasswordResetTokenModel.
        refresh_tokens: One-to-many with RefreshTokenModel.
        payments: One-to-many with PaymentModel.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_groups.id"), ondelete="CASCADE",
        nullable=False
    )

    # Relationships
    group: Mapped["UserGroupModel"] = relationship(
        "UserGroupModel",
        back_populates="users",
        lazy="selectin"
    )
    profile: Mapped["UserProfileModel"] = relationship(
        "UserProfileModel",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    activation_token: Mapped["ActivationTokenModel"] = relationship(
        "ActivationTokenModel",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    password_reset_token: Mapped["PasswordResetTokenModel"] = relationship(
        "PasswordResetTokenModel",
        back_populates="user",
        uselist=False,
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel",
        back_populates="user",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<UserModel(id={self.id}, "
            f"email={self.email}, is_active={self.is_active})>"
        )
