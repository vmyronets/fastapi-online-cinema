"""
PasswordResetToken ORM model.

Represents the password_reset_tokens table storing tokens for
password recovery. Sent to user's email upon request.
"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models.user import UserModel


class PasswordResetTokenModel(Base):
    """
    SQLAlchemy model for the password_reset_tokens table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table, unique (one-to-one).
        token: Unique password reset token string.
        expires_at: Token expiration timestamp.

    Relationships:
        user: One-to-one back-reference to UserModel.
    """
    __tablename__ = "password_reset_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # One-to-one back-reference to the user.
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="password_reset_token", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<PasswordResetTokenModel(id={self.id}, user_id={self.user_id})>"
