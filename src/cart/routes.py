"""
API routes for the cart module.

Provides endpoints for managing the shopping cart: viewing,
adding/removing items, and clearing the cart.
"""

from typing import cast

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.security.dependencies import (
    SessionDep,
    JWTManagerDep,
    get_token,
    decode_token
)
from src.orders.models import (
    OrderItemModel,
    OrderModel,
    OrderStatusEnum
)
from src.cart.models import (
    CartModel,
    CartItemModel
)
from src.cart.schemas import (
    CartResponseSchema,
    CartItemResponseSchema,
    CartItemAddSchema
)
from src.movies.models import MovieModel
from src.security.interfaces import JWTAuthManagerInterface


router = APIRouter(prefix="/cart", tags=["Cart"])


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
        movie_price=movie.price if movie else None,
        movie_year=movie.year if movie else None,
        movie_genres=[g.name for g in movie.genres] if movie else [],
        added_at=item.added_at,
    )


@router.get(
    "/",
    response_model=CartResponseSchema,
    summary="View cart contents"
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
    payload = decode_token(token, jwt_manager)
    user_id = cast(int, payload.get("user_id"))
    cart = await _get_or_create_cart(db, user_id)

    # Fetch cart items.
    stmt = select(CartItemModel).where(
        CartItemModel.cart_id == cart.id
    ).options(joinedload(CartItemModel.movie).selectinload(MovieModel.genres))
    result = await db.execute(stmt)
    items = result.scalars().all()

    item_responses = [
        CartItemResponseSchema(
            id=item.id,
            movie_id=item.movie_id,
            movie_name=item.movie.name if item.movie else None,
            movie_price=item.movie.price if item.movie else None,
            movie_year=item.movie.year if item.movie else None,
            movie_genres=[
                genre.name for genre in item.movie.genres
            ] if item.movie else [],
            added_at=item.added_at
        )
        for item in items
    ]

    return CartResponseSchema(
        id=cart.id,
        user_id=cart.user_id,
        items=item_responses
    )


@router.post(
    "/items/",
    response_model=CartItemResponseSchema,
    summary="Add movie to cart",
    status_code=status.HTTP_201_CREATED,
)
async def add_to_cart(
    data: CartItemAddSchema,
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> CartItemResponseSchema:
    """
    Add a movie to the shopping cart.

    Steps:
    - Authenticate user.
    - Verify movie exists.
    - Check movie hasn't already been purchased.
    - Check movie isn't already in the cart.
    - Add movie to cart.

    Args:
        data (CartItemAddSchema): Contains the movie_id to add.
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        CartItemResponseSchema: The added cart item.

    Raises:
        HTTPException: If movie not found, already purchased, or already in cart.
    """
    payload = decode_token(token, jwt_manager)
    user_id = cast(int, payload.get("user_id"))

    # Verify movie exists.
    movie = (
        await db.execute(
                select(MovieModel).where(MovieModel.id == data.movie_id))
            ).scalars().first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Movie not found."
        )

    # Check if movie already purchased.
    purchased = (
        await db.execute(
            select(OrderItemModel)
            .join(OrderModel)
            .where(
                OrderModel.user_id == user_id,
                OrderModel.status == OrderStatusEnum.PAID,
                OrderItemModel.movie_id == data.movie_id
            )
        )
    ).scalars().first()
    if purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie already purchased. Repeat purchases are not allowed.",
        )

    cart = await _get_or_create_cart(db, user_id)

    # Check if already in cart.
    existing = (
        await db.execute(
            select(CartItemModel).where(
                CartItemModel.cart_id == cart.id,
                CartItemModel.movie_id == data.movie_id,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie is already in the cart.",
        )

    # Add to cart.
    item = CartItemModel(cart_id=cast(int, cart.id), movie_id=data.movie_id)
    db.add(item)
    await db.commit()
    await db.refresh(item)

    return await _build_cart_item_response(db, item)


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
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        dict: Confirmation message.

    Raises:
        HTTPException: If movie not in cart.
    """
    payload = decode_token(token, jwt_manager)
    user_id = cast(int, payload.get("user_id"))
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


@router.delete(
    "/clear/",
    response_model=dict,
    summary="Clear entire cart",
)
async def clear_cart(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token)
) -> dict:
    """
    Clear all items from the shopping cart.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        dict: Confirmation message.
    """
    payload = decode_token(token, jwt_manager)
    user_id = cast(int, payload.get("user_id"))
    cart = await _get_or_create_cart(db, user_id)

    stmt = delete(CartItemModel).where(CartItemModel.cart_id == cart.id)
    await db.execute(stmt)
    await db.commit()

    return {"detail": "Cart cleared successfully."}
