import uuid

from sqlalchemy import Integer, String, Float, Text, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


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
    """
    __tablename__ = "movies"
    __table_args__ = (
        UniqueConstraint("name", "year", "time", name="uq_movie_name_year_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    time: Mapped[int] = mapped_column(Integer, nullable=False)
    imdb: Mapped[float] = mapped_column(Float, nullable=False)
    votes: Mapped[int] = mapped_column(Integer, nullable=False)
    meta_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    gross: Mapped[float | None] = mapped_column(Float, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0.00)
    certification_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("certifications.id"), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MovieModel(id={self.id}, name={self.name}, year={self.year})>"
