"""
Certification ORM model.

Represents the certifications table storing movie ratings/certifications
(e.g., PG-13, R). One-to-many relationship with Movie.
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


class CertificationModel(Base):
    """
    SQLAlchemy model for the certifications table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Certification name (e.g., "PG-13"), unique and not null.

    Relationships:
        movies: One-to-many with MovieModel.
    """
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    movies: Mapped[list["MovieModel"]] = relationship(
        "MovieModel", back_populates="certification", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<CertificationModel(id={self.id}, name={self.name})>"
