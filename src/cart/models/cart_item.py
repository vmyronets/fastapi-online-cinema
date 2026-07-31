"""
CartItem ORM model.

Represents the cart_items table storing individual movies in a user's cart.
Unique constraint on (cart_id, movie_id) prevents duplicate entries.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Integer,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from src.database.session import Base

if TYPE_CHECKING:
    from src.cart.models.cart import CartModel
    from src.movies.models.movie import MovieModel


class CartItemModel(Base):
    """
    SQLAlchemy model for the cart_items table.

    Attributes:
        id: Primary key (int), auto-incremented.
        cart_id: Foreign key to carts table.
        movie_id: Foreign key to movies table.
        added_at: Timestamp when the movie was added to the cart.

    Constraints:
        Unique constraint on (cart_id, movie_id) — same movie cannot be added twice.

    Relationships:
        cart: Many-to-one back-reference to CartModel.
    """
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint(
            "cart_id",
            "movie_id",
            name="uq_cart_item_cart_movie"
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )
    cart_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False
    )
    movie_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("movies.id", ondelete="CASCADE"),
        nullable=False
    )
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Many-to-one back-reference to the cart.
    cart: Mapped["CartModel"] = relationship(
        "CartModel",
        back_populates="items",
        lazy="selectin"
    )

    # Many-to-one back-reference to the movie.
    movie: Mapped["MovieModel"] = relationship(
        "MovieModel",
        lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<CartItemModel(id={self.id},"
            f" cart_id={self.cart_id},"
            f" movie_id={self.movie_id})>"
        )
