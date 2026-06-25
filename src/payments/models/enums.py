"""
Enumerations for the payments module.

Defines payment status values used in the Payment model.
"""

import enum


class PaymentStatusEnum(str, enum.Enum):
    """
    Enumeration of possible payment statuses.

    Values:
        SUCCESSFUL: Payment completed successfully.
        CANCELED: Payment was canceled before completion.
        REFUNDED: Payment was refunded after success.
    """
    SUCCESSFUL = "successful"
    CANCELED = "canceled"
    REFUNDED = "refunded"
