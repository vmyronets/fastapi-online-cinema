"""
Payment ORM model.

Represents the payments table storing payment transactions
made by users for orders. Tracks payment lifecycle through
status (successful, canceled, refunded).
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    String,
    Numeric,
    DateTime,
    Enum,
    ForeignKey,
    func
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from src.database.session import Base
from src.payments.models.enums import PaymentStatusEnum


class PaymentModel(Base):
    """
    SQLAlchemy model for the payments table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        order_id: Foreign key to orders table.
        created_at: Timestamp of payment creation.
        status: Payment status (successful, canceled, refunded).
        amount: Total payment amount (DECIMAL(10,2)).
        external_payment_id: External transaction ID from payment provider (e.g., Stripe).
    """
    __tablename__ = "payments"

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
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        Enum(PaymentStatusEnum, name="payment_status_enum"),
        default=PaymentStatusEnum.SUCCESSFUL,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )
    external_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentModel(id={self.id}, "
            f"user_id={self.user_id}, status={self.status})>"
        )
