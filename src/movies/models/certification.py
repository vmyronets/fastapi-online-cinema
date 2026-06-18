from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.session import Base


class CertificationModel(Base):
    """
    SQLAlchemy model for the certifications table.

    Attributes:
        id: Primary key (int), auto-incremented.
        name: Certification name (e.g., "PG-13"), unique and not null.
    """
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<CertificationModel(id={self.id}, name={self.name})>"
