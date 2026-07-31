"""
Genre ORM model.

Represents the genres table storing movie genres (e.g., Action, Drama).
Many-to-many relationship with Movie through movie_genres table.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from src.database.session import Base

if TYPE_CHECKING:
    from src.movies.models.movie import MovieModel


class GenreModel(Base):
    """
    SQLAlchemy model for the genres table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Genre name (e.g., "Action"), unique and not null.

    Relationships:
        movies: Many-to-many with MovieModel via movie_genres.
    """
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False
    )

    # Many-to-many with movies through the association table.
    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel",
        secondary="movie_genres",
        back_populates="genres",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<GenreModel(id={self.id}, name={self.name})>"
