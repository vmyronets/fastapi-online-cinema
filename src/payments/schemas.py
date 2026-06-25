"""
Pydantic schemas for the payments module.

Defines request/response schemas for payment processing,
payment history, and Stripe webhook handling.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.payments.models import PaymentStatusEnum


class PaymentItemResponseSchema(BaseModel):
    """
    Schema for a single payment item response.

    Attributes:
        id: Payment item ID.
        order_item_id: Reference to the original order item.
        price_at_payment: Price at the time of payment.
    """
    id: int
    order_item_id: int
    price_at_payment: Decimal

    model_config = ConfigDict(from_attributes=True)


class PaymentResponseSchema(BaseModel):
    """
    Schema for payment response.

    Attributes:
        id: Payment ID.
        user_id: User who made the payment.
        order_id: Associated order ID.
        created_at: Payment creation timestamp.
        status: Payment status (successful, canceled, refunded).
        amount: Total payment amount.
        external_payment_id: External transaction ID (e.g., Stripe).
        items: List of payment items.
    """
    id: int
    user_id: int
    order_id: int
    created_at: datetime
    status: PaymentStatusEnum
    amount: Decimal
    external_payment_id: Optional[str] = None
    items: list[PaymentItemResponseSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PaymentListResponseSchema(BaseModel):
    """
    Schema for paginated payment list.

    Attributes:
        items: List of payments.
        total: Total number of payments.
        page: Current page.
        per_page: Items per page.
    """
    items: list[PaymentResponseSchema]
    total: int
    page: int
    per_page: int


class StripeCheckoutResponseSchema(BaseModel):
    """
    Schema for Stripe checkout session response.

    Attributes:
        checkout_url: URL to redirect the user to Stripe checkout.
        session_id: Stripe session ID for tracking.
    """
    checkout_url: str
    session_id: str
