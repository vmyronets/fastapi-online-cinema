"""
Director ORM model.

Represents the directors table storing movie directors.
Many-to-many relationship with Movie through movie_directors table.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import TYPE_CHECKING

from src.database.session import Base

if TYPE_CHECKING:
    from src.movies.models.movie import MovieModel


class DirectorModel(Base):
    """
    SQLAlchemy model for the directors table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Director's name, unique and not null.

    Relationships:
        movies: Many-to-many with MovieModel via movie_directors.
    """
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", secondary="movie_directors", back_populates="directors", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<DirectorModel(id={self.id}, name={self.name})>"
