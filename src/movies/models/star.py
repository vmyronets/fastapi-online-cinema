"""
Star ORM model.

Represents the stars table storing actors/actresses.
Many-to-many relationship with Movie through movie_stars table.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from typing import TYPE_CHECKING

from src.database.session import Base

if TYPE_CHECKING:
    from src.movies.models.movie import MovieModel


class StarModel(Base):
    """
    SQLAlchemy model for the stars table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Star's name, unique and not null.

    Relationships:
        movies: Many-to-many with MovieModel via movie_stars.
    """
    __tablename__ = "stars"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary="movie_stars",
        back_populates="stars",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<StarModel(id={self.id}, name={self.name})>"
