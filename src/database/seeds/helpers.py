"""
Shared helper functions for database seeding.

These helpers encapsulate PostgreSQL-specific bulk insert operations
and common utilities reused by individual seed modules.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


BULK_INSERT_CHUNK_SIZE = 1000


async def insert_if_not_exists(
    session: AsyncSession,
    model: type[Any],
    values: Sequence[dict[str, Any]],
    *,
    conflict_columns: Sequence[str] | None = None
) -> None:
    """
    Bulk insert rows into a table.

    Existing rows are ignored using PostgreSQL
    ON CONFLICT DO NOTHING.

    Args:
        session:
            Active async SQLAlchemy session.

        model:
            SQLAlchemy ORM model.

        values:
            Sequence of dictionaries to insert.

        conflict_columns:
            Columns used for conflict detection.
            If omitted, the helper automatically uses
            the table's unique column when possible.
    """

    if not values:
        return

    if conflict_columns is None:
        mapper = inspect(model)

        conflict_columns = [
            column.key
            for column in mapper.columns
            if column.unique
        ]

    for start in range(0, len(values), BULK_INSERT_CHUNK_SIZE):
        chunk = values[start:start + BULK_INSERT_CHUNK_SIZE]

        stmt = insert(model).values(chunk)

        if conflict_columns:
            stmt = stmt.on_conflict_do_nothing(
                index_elements=list(conflict_columns)
            )

        await session.execute(stmt)
