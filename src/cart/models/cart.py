from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class CartModel(Base):
    """
    SQLAlchemy model for the carts table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table, unique (one-to-one with User).
    """
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<CartModel(id={self.id}, user_id={self.user_id})>"
