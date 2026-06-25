"""
Order ORM model.

Represents the orders table storing user orders.
Tracks order lifecycle through status (pending, paid, canceled).
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    Numeric,
    DateTime,
    Enum,
    func,
    ForeignKey
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)
from typing import TYPE_CHECKING

from src.database.session import Base
from src.orders.models.enums import OrderStatusEnum

if TYPE_CHECKING:
    from src.orders.models.order_item import OrderItemModel
    from src.payments.models.payment import PaymentModel
    from src.payments.models.payment_item import PaymentItemModel


class OrderModel(Base):
    """
    SQLAlchemy model for the orders table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        created_at: Timestamp of order creation.
        status: Order status (pending, paid, canceled).
        total_amount: Total cost of all items (DECIMAL(10,2)).

    Relationships:
        items: One-to-many with OrderItemModel.
        payments: One-to-many with PaymentModel.
        payment_items: Many-to-one with PaymentItemModel.
    """
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(OrderStatusEnum, name="order_status_enum"),
        default=OrderStatusEnum.PENDING,
        nullable=False
    )
    total_amount: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True
    )

    # One-to-many: an order can contain multiple items.
    items: Mapped[list["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    # One-to-many: an order can contain multiple payments.
    payments: Mapped[list["PaymentModel"]] = relationship(
        "PaymentModel",
        back_populates="order",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    # many-to-one: an order can contain multiple payment items.
    payment_items: Mapped[list["PaymentItemModel"]] = relationship(
        "PaymentItemModel",
        back_populates="order_item",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<OrderModel(id={self.id}, "
            f"user_id={self.user_id}, status={self.status})>"
        )
