"""
Enumerations for the orders module.

Defines order status values used in the Order model.
"""

import enum


class OrderStatusEnum(str, enum.Enum):
    """
    Enumeration of possible order statuses.

    Values:
        PENDING: Order placed but not yet paid.
        PAID: Order successfully paid.
        CANCELED: Order canceled by user or system.
    """
    PENDING = "pending"
    PAID = "paid"
    CANCELED = "canceled"
