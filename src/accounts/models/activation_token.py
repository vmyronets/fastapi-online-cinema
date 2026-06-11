"""
ActivationToken ORM model.

Represents the activation_tokens table storing tokens sent to users
via email after registration. Tokens expire after 24 hours.
"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models.user import UserModel


class ActivationTokenModel(Base):
    """
    SQLAlchemy model for the activation_tokens table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table, unique (one-to-one).
        token: Unique activation token string.
        expires_at: Token expiration timestamp (24 hours after creation).

    Relationships:
        user: One-to-one back-reference to UserModel.
    """
    __tablename__ = "activation_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # One-to-one back-reference to the user.
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="activation_token", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<ActivationTokenModel(id={self.id}, user_id={self.user_id})>"
