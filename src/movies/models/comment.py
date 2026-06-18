"""
Comment ORM model.

Represents the comments table storing user comments on movies.
Supports nested replies via parent_id self-referencing foreign key.
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    Text,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from src.database.session import Base


class CommentModel(Base):
    """
    SQLAlchemy model for the comments table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        movie_id: Foreign key to movies table.
        parent_id: Self-referencing FK for reply threading (optional).
        content: Comment text content.
        created_at: Timestamp of comment creation.

    Relationships:
        replies: One-to-many self-referencing for nested comments.
    """
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False
    )
    parent_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Self-referencing relationship for nested replies.
    replies: Mapped[list["CommentModel"]] = relationship(
        "CommentModel",
        back_populates="parent",
        lazy="selectin"
    )
    parent: Mapped["CommentModel | None"] = relationship(
        "CommentModel",
        back_populates="replies",
        remote_side=[id],
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<CommentModel(id={self.id}, "
            f"user_id={self.user_id}, "
            f"movie_id={self.movie_id})>"
        )
