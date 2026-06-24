"""
Pydantic schemas for the orders module.

Defines request/response schemas for order creation,
listing, and order item details.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class OrderItemResponseSchema(BaseModel):
    """
    Schema for a single order item response.

    Attributes:
        id: Order item ID.
        movie_id: The movie's ID.
        price_at_order: Price of the movie at order time.
    """
    id: int
    movie_id: int
    price_at_order: float

    model_config = ConfigDict(from_attributes=True)


class OrderResponseSchema(BaseModel):
    """
    Schema for order response.

    Attributes:
        id: Order ID.
        user_id: Owner user ID.
        created_at: Order creation timestamp.
        status: Order status (pending, paid, canceled).
        total_amount: Total order cost.
        items: List of order items.
    """
    id: int
    user_id: int
    created_at: datetime
    status: str
    total_amount: Optional[float] = None
    items: list[OrderItemResponseSchema] = []

    model_config = ConfigDict(from_attributes=True)


class OrderListResponseSchema(BaseModel):
    """
    Schema for paginated order list.

    Attributes:
        items: List of orders.
        total: Total number of orders.
        page: Current page.
        per_page: Items per page.
    """
    items: list[OrderResponseSchema]
    total: int
    page: int
    per_page: int
