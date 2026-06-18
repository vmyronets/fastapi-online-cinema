"""
Favorite ORM model.

Represents the favorites table storing user-movie favorite relationships.
A user can add movies to their favorites list.
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class FavoriteModel(Base):
    """
    SQLAlchemy model for the favorites table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        movie_id: Foreign key to movies table.
        created_at: Timestamp when the movie was added to favorites.

    Constraints:
        Unique constraint on (user_id, movie_id) to prevent duplicates.
    """
    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="uq_favorite_user_movie"
        )
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<FavoriteModel(user_id={self.user_id},"
            f" movie_id={self.movie_id})>"
        )
