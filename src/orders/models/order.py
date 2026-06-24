from datetime import datetime

from sqlalchemy import (
    Integer,
    Numeric,
    DateTime,
    Enum,
    func,
    ForeignKey
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base
from src.orders.models.enums import OrderStatusEnum


class OrderModel(Base):
    """
    SQLAlchemy model for the orders table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        created_at: Timestamp of order creation.
        status: Order status (pending, paid, canceled).
        total_amount: Total cost of all items (DECIMAL(10,2)).
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

    def __repr__(self) -> str:
        return (
            f"<OrderModel(id={self.id}, "
            f"user_id={self.user_id}, status={self.status})>"
        )
