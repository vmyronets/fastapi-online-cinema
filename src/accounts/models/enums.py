"""
Enumerations for the accounts module.

Defines user group roles and gender options used across
the account models and schemas.
"""

import enum


class UserGroupEnum(str, enum.Enum):
    """
    Enumeration of possible user groups (roles).

    Values:
        USER: A regular user with basic interface access.
        MODERATOR: Can manage content, view sales, and perform admin tasks.
        ADMIN: Full access — can manage users, change groups, activate accounts.
    """
    USER = "USER"
    MODERATOR = "MODERATOR"
    ADMIN = "ADMIN"


class GenderEnum(str, enum.Enum):
    """
    Enumeration for storing a user's gender.

    Values:
        MAN: Male gender.
        WOMAN: Female gender.
    """
    MAN = "MAN"
    WOMAN = "WOMAN"
