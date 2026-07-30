"""
Seed default application users with different roles (ADMIN, MODERATOR, USER).
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.accounts.models.user import UserModel
from src.accounts.models.user_group import UserGroupModel
from src.database.seeds.constants import DEFAULT_USERS
from src.database.seeds.helpers import insert_if_not_exists
from src.security.password import hash_password


async def seed_users(session: AsyncSession) -> None:
    """
    Create default application users if they do not exist.
    """

    result = await session.execute(select(UserGroupModel))
    groups = {
        group.name: group.id
        for group in result.scalars()
    }

    values = [
        {
            "email": user["email"],
            "hashed_password": hash_password(user["password"]),
            "is_active": True,
            "group_id": groups[user["group"]]
        }
        for user in DEFAULT_USERS
    ]

    await insert_if_not_exists(
        session=session,
        model=UserModel,
        values=values,
        conflict_columns=["email"]
    )
