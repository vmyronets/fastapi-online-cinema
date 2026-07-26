"""
Seed default user groups.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from src.accounts.models.enums import UserGroupEnum
from src.accounts.models.user_group import UserGroupModel

from src.database.seeds.helpers import insert_if_not_exists


async def seed_groups(session: AsyncSession) -> None:
    """
    Create default user groups if they do not exist.
    """

    values = [
        {"name": group}
        for group in UserGroupEnum
    ]

    await insert_if_not_exists(
        session=session,
        model=UserGroupModel,
        values=values
    )
