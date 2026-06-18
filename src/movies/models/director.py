from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class DirectorModel(Base):
    """
    SQLAlchemy model for the directors table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Director's name, unique and not null.
    """
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<DirectorModel(id={self.id}, name={self.name})>"
