"""
API routes for the cart module.

Provides endpoints for managing the shopping cart: viewing,
adding/removing items, and clearing the cart.
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from security.dependencies import get_token
from src.accounts.routes import SessionDep, JWTManagerDep
from cart.models import (
    CartModel,
    CartItemModel
)
from cart.schemas import (
    CartResponseSchema,
    CartItemResponseSchema
)
from movies.models import MovieModel
from security.exceptions import BaseSecurityError
from security.interfaces import JWTAuthManagerInterface


router = APIRouter(prefix="/cart", tags=["Cart"])


def _decode_token(token: str, jwt_manager: JWTAuthManagerInterface) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token: The raw JWT token string.
        jwt_manager: JWT manager instance for decoding.

    Returns:
        dict: The decoded token payload.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        return jwt_manager.decode_access_token(token)
    except BaseSecurityError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


async def _get_or_create_cart(db: AsyncSession, user_id: int) -> CartModel:
    """
    Get the user's cart or create one if it doesn't exist.

    Args:
        db: Async database session.
        user_id: The user's ID.

    Returns:
        CartModel: The user's cart.
    """
    stmt = select(CartModel).where(CartModel.user_id == user_id)
    result = await db.execute(stmt)
    cart = result.scalars().first()
    if not cart:
        cart = CartModel(user_id=user_id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)
    return cart


async def _build_cart_item_response(
        db: AsyncSession, item: CartItemModel
) -> CartItemResponseSchema:
    """
    Build a CartItemResponseSchema with movie details.

    Args:
        db: Async database session.
        item: The CartItemModel instance.

    Returns:
        CartItemResponseSchema: Serialized cart item with movie info.
    """
    movie = (
        await db.execute(
            select(MovieModel).where(MovieModel.id == item.movie_id))
    ).scalars().first()

    return CartItemResponseSchema(
        id=item.id,
        movie_id=item.movie_id,
        movie_name=movie.name if movie else None,
        movie_price=float(movie.price) if movie else None,
        movie_year=movie.year if movie else None,
        movie_genres=[g.name for g in movie.genres] if movie else [],
        added_at=item.added_at,
    )


@router.get(
    "/",
    response_model=CartResponseSchema,
    summary="View cart contents",
)
async def get_cart(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> CartResponseSchema:
    """
    View the authenticated user's shopping cart.

    Steps:
    - Authenticate user.
    - Get or create the user's cart.
    - Return cart with item details including movie info.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        CartResponseSchema: The user's cart with items.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")
    cart = await _get_or_create_cart(db, user_id)

    # Fetch cart items.
    stmt = select(CartItemModel).where(CartItemModel.cart_id == cart.id)
    result = await db.execute(stmt)
    items = result.scalars().all()

    item_responses = [
        await _build_cart_item_response(db, item) for item in items
    ]

    return CartResponseSchema(
        id=cart.id,
        user_id=cart.user_id,
        items=item_responses
    )


@router.delete(
    "/items/{movie_id}/",
    response_model=dict,
    summary="Remove movie from cart",
)
async def remove_from_cart(
    movie_id: int,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> dict:
    """
    Remove a movie from the shopping cart.

    Args:
        movie_id (int): The movie's ID to remove.
        token (str): The authentication token.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        db (AsyncSession): The asynchronous database session.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If movie not in cart.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")
    cart = await _get_or_create_cart(db, user_id)

    item = (
        await db.execute(
            select(CartItemModel).where(
                CartItemModel.cart_id == cart.id,
                CartItemModel.movie_id == movie_id,
            )
        )
    ).scalars().first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not in cart."
        )

    await db.delete(item)
    await db.commit()

    return {"detail": "Movie removed from cart."}
