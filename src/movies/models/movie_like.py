"""
MovieLike ORM model.

Represents the movie_likes table storing user likes/dislikes on movies.
Each user can like or dislike a movie once.
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class MovieLikeModel(Base):
    """
    SQLAlchemy model for the movie_likes table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        movie_id: Foreign key to movies table.
        is_like: True for like, False for dislike.
        created_at: Timestamp of the like/dislike action.

    Constraints:
        Unique constraint on (user_id, movie_id) — one reaction per user per movie.
    """
    __tablename__ = "movie_likes"
    __table_args__ = (
        UniqueConstraint("user_id", "movie_id", name="uq_like_user_movie"),
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
    is_like: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<MovieLikeModel(user_id={self.user_id}, "
            f"movie_id={self.movie_id}, is_like={self.is_like})>"
        )
