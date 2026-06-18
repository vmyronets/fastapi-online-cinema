from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class GenreModel(Base):
    """
    SQLAlchemy model for the genres table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Genre name (e.g., "Action"), unique and not null.
    """
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<GenreModel(id={self.id}, name={self.name})>"
