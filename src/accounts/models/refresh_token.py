"""
RefreshToken ORM model.

Represents the refresh_tokens table storing JWT refresh tokens.
Used to get new access tokens without re-entering credentials.
Deleted on logout to prevent further use.
"""

from datetime import datetime

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models.user import UserModel


class RefreshTokenModel(Base):
    """
    SQLAlchemy model for the refresh_tokens table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users' table.
        token: Unique refresh token string.
        expires_at: Token expiration timestamp.

    Relationships:
        user: Many-to-one back-reference to UserModel.
    """
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Many-to-one back-reference to the user.
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="refresh_tokens", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<RefreshTokenModel(id={self.id}, user_id={self.user_id})>"
