"""
Pydantic schemas for the cart module.

Defines request/response schemas for shopping cart operations
including adding/removing items and viewing cart contents.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CartItemAddSchema(BaseModel):
    """
    Schema for adding a movie to the cart.

    Attributes:
        movie_id: The ID of the movie to add.
    """
    movie_id: int


class CartItemResponseSchema(BaseModel):
    """
    Schema for a single cart item response.

    Attributes:
        id: Cart item ID.
        movie_id: The movie's ID.
        movie_name: The movie's title.
        movie_price: The movie's current price.
        movie_year: The movie's release year.
        movie_genres: List of genre names for the movie.
        added_at: Timestamp when the item was added.
    """
    id: int
    movie_id: int
    movie_name: Optional[str] = None
    movie_price: Optional[Decimal] = None
    movie_year: Optional[int] = None
    movie_genres: list[str] = Field(default_factory=list)
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CartResponseSchema(BaseModel):
    """
    Schema for full cart response.

    Attributes:
        id: Cart ID.
        user_id: Owner user ID.
        items: List of cart items with movie details.
    """
    id: int
    user_id: int
    items: list[CartItemResponseSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
