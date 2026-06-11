"""
UserProfile ORM model.

Represents the user_profiles table storing additional user information
such as name, avatar, gender, date of birth, and bio.
One-to-one relationship with the User model.
"""

from datetime import date

from sqlalchemy import Integer, String, Text, Date, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base
from src.accounts.models.enums import GenderEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models.user import UserModel


class UserProfileModel(Base):
    """
    SQLAlchemy model for the user_profiles table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table, unique (one-to-one).
        first_name: User's first name (optional).
        last_name: User's last name (optional).
        avatar: S3 key or URL for the user's avatar image (optional).
        gender: Gender enum (MAN/WOMAN), optional.
        date_of_birth: Date of birth (optional).
        info: Short bio or additional info text (optional).

    Relationships:
        user: One-to-one back-reference to UserModel.
    """
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    gender: Mapped[str | None] = mapped_column(
        Enum(GenderEnum, name="gender_enum"), nullable=True
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    info: Mapped[str | None] = mapped_column(Text, nullable=True)

    # One-to-one back-reference to the user.
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="profile", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<UserProfileModel(id={self.id}, user_id={self.user_id})>"
