"""
Rating ORM model.

Represents the ratings table storing user movie ratings on a 10-point scale.
Each user can rate a movie only once.
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class RatingModel(Base):
    """
    SQLAlchemy model for the ratings table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        movie_id: Foreign key to movies table.
        score: Rating score (1-10).
        created_at: Timestamp of the rating.

    Constraints:
        Unique constraint on (user_id, movie_id) — one rating per user per movie.
    """
    __tablename__ = "ratings"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "movie_id",
            name="uq_rating_user_movie"
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
    score: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<RatingModel(user_id={self.user_id},"
            f" movie_id={self.movie_id}, score={self.score})>"
        )
