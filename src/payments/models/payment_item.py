"""
PaymentItem ORM model.

Represents the payment_items table storing individual items
paid for in a single payment. Mirrors order line items at
the time of payment for historical accuracy.
"""

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
    from src.payments.models.payment import PaymentModel


class PaymentItemModel(Base):
    """
    SQLAlchemy model for the payment_items table.

    Attributes:
        id: Primary key (int), auto-incremented.
        payment_id: Foreign key to payments table.
        order_item_id: Foreign key to order_items table.
        price_at_payment: Price of the item at payment time (DECIMAL(10,2)).

    Relationships:
        payment: Many-to-one back-reference to PaymentModel.
    """
    __tablename__ = "payment_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    payment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("payments.id", ondelete="CASCADE"),
        nullable=False
    )
    order_item_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False
    )
    price_at_payment: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False
    )

    # Many-to-one back-reference to the payment.
    payment: Mapped["PaymentModel"] = relationship(
        "PaymentModel",
        back_populates="items",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<PaymentItemModel(id={self.id}, "
            f"payment_id={self.payment_id})>"
        )
