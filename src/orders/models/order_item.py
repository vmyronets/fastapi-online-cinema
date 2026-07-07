"""
OrderItem ORM model.

Represents the order_items table storing individual line items
within an order. Stores price_at_order for historical accuracy.
"""
from decimal import Decimal

from sqlalchemy import (
    Integer,
    Numeric,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from typing import TYPE_CHECKING

from src.database.session import Base

if TYPE_CHECKING:
    from src.orders.models.order import OrderModel
    from src.payments.models.payment_item import PaymentItemModel


class OrderItemModel(Base):
    """
    SQLAlchemy model for the order_items table.

    Attributes:
        id: Primary key (int), auto-incremented.
        order_id: Foreign key to orders table.
        movie_id: Foreign key to movies table.
        price_at_order: Price of the movie at order time (DECIMAL(10,2)).

    Relationships:
        order: Many-to-one back-reference to OrderModel.
    """
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False
    )
    price_at_order: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # Many-to-one back-reference to the order.
    order: Mapped["OrderModel"] = relationship(
        "OrderModel",
        back_populates="items",
        lazy="selectin"
    )
    # One-to-many: an order item can be part of multiple payments.
    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel",
        back_populates="order_item",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItemModel(id={self.id}, "
            f"order_id={self.order_id}, movie_id={self.movie_id})>"
        )
