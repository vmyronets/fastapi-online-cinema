"""
CommentLike ORM model.

Represents the comment_likes table storing user likes/dislikes on comments.
Each user can like or dislike a specific comment once.
"""

from datetime import datetime

from sqlalchemy import (
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database.session import Base


class CommentLikeModel(Base):
    """
    SQLAlchemy model for the comment_likes table.

    Attributes:
        id: Primary key (int), auto-incremented.
        user_id: Foreign key to users table.
        comment_id: Foreign key to comments table.
        is_like: True for like, False for dislike.
        created_at: Timestamp of the like/dislike action.

    Constraints:
        Unique constraint on (user_id, comment_id) — one reaction per user per comment.
    """
    __tablename__ = "comment_likes"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "comment_id",
            name="uq_like_user_comment"
        ),
    )

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
    comment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=False
    )
    is_like: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<CommentLikeModel(user_id={self.user_id}, "
            f"comment_id={self.comment_id}, is_like={self.is_like})>"
        )
