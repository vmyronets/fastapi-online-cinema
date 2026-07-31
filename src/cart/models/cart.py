"""
Cart ORM model.

Represents the carts table. Each user has exactly one cart (one-to-one).
Acts as a container for CartItem records.
"""

from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from src.database.session import Base

if TYPE_CHECKING:
    from src.cart.models.cart_item import CartItemModel


class CartModel(Base):
    """
    SQLAlchemy model for the carts table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table, unique (one-to-one with User).

    Relationships:
        items: One-to-many with CartItemModel.
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

    # One-to-many: a cart can contain multiple items.
    items: Mapped[list["CartItemModel"]] = relationship(
        "CartItemModel",
        back_populates="cart",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CartModel(id={self.id}, user_id={self.user_id})>"
