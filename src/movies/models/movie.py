"""
Movie ORM model.

Represents the movies table storing main movie data including
title, year, duration, ratings, pricing, and relationships
with genres, directors, stars, and certification.
"""

import uuid

from sqlalchemy import (
    Integer,
    String,
    Float,
    Text,
    Numeric,
    ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from typing import TYPE_CHECKING

from src.database.session import Base

if TYPE_CHECKING:
    from src.movies.models.certification import CertificationModel
    from src.movies.models.genre import GenreModel
    from src.movies.models.director import DirectorModel
    from src.movies.models.star import StarModel


class MovieModel(Base):
    """
    SQLAlchemy model for the movies table.

    Attributes:
        id: Primary key (int), auto-incremented.
        uuid: Unique UUID for global identification.
        name: Movie title, not null.
        year: Release year, not null.
        time: Duration in minutes, not null.
        imdb: IMDb rating, not null.
        votes: Number of IMDb votes, not null.
        meta_score: Metascore (optional).
        gross: Gross revenue (optional).
        description: Movie synopsis, not null.
        price: Movie price (DECIMAL(10,2)).
        certification_id: Foreign key to certifications table.

    Relationships:
        certification: Many-to-one with CertificationModel.
        genres: Many-to-many with GenreModel via movie_genres.
        directors: Many-to-many with DirectorModel via movie_directors.
        stars: Many-to-many with StarModel via movie_stars.
    """
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "year",
            "time",
            name="uq_movie_name_year_time"
        )
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=0.00
    )
    certification_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("certifications.id"),
        nullable=False
    )

    # Relationships
    certification: Mapped["CertificationModel"] = relationship(
        "CertificationModel",
        back_populates="movies",
        lazy="selectin"
    )
    genres: Mapped[list["GenreModel"]] = relationship(
        "GenreModel",
        secondary="movie_genres",
        back_populates="movies",
        lazy="selectin"
    )
    directors: Mapped[list["DirectorModel"]] = relationship(
        "DirectorModel",
        secondary="movie_directors",
        back_populates="movies",
        lazy="selectin"
    )
    stars: Mapped[list["StarModel"]] = relationship(
        "StarModel",
        secondary="movie_stars",
        back_populates="movies",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<MovieModel(id={self.id}, "
            f"name={self.name}, year={self.year})>"
        )
