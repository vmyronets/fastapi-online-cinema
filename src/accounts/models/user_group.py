"""
UserGroup ORM model.

Represents the user_groups table storing role-based access groups
(USER, MODERATOR, ADMIN). Each user belongs to exactly one group.
"""

from sqlalchemy import Integer, Enum
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from src.database.session import Base
from src.accounts.models.enums import UserGroupEnum

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.accounts.models.user import UserModel


class UserGroupModel(Base):
    """
    SQLAlchemy model for the user_groups table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Group name (USER, MODERATOR, ADMIN), unique.

    Relationships:
        users: One-to-many relationship with UserModel.
    """
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        Enum(UserGroupEnum, name="user_group_enum"),
        unique=True,
        nullable=False,
    )

    # One-to-many: one group can have many users.
    users: Mapped[list["UserModel"]] = relationship(
        "UserModel",
        back_populates="group",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<UserGroupModel(id={self.id}, name={self.name})>"
