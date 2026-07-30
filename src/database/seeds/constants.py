"""
Default development users for database seeding.
"""

from src.accounts.models.enums import UserGroupEnum


DEFAULT_USERS = [
    {
        "email": "admin@admin.com",
        "password": "Admin123!",
        "group": UserGroupEnum.ADMIN
    },
    {
        "email": "moderator@moderator.com",
        "password": "Moderator123!",
        "group": UserGroupEnum.MODERATOR
    },
    {
        "email": "user@user.com",
        "password": "User123!",
        "group": UserGroupEnum.USER
    }
]
