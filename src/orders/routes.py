"""
API routes for the orders module.

Provides endpoints for creating orders from cart, listing orders,
canceling orders, and admin order management.
"""
from decimal import Decimal
from typing import cast

from fastapi import (
    APIRouter,
    HTTPException,
    status,
    Depends,
    Query
)
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from cart.models import CartModel, CartItemModel
from movies.models import MovieModel
from orders.models import (
    OrderModel,
    OrderItemModel,
    OrderStatusEnum
)
from src.accounts.routes import SessionDep, JWTManagerDep
from src.orders.schemas import (
    OrderResponseSchema,
    OrderItemResponseSchema,
    OrderListResponseSchema
)
from src.security.dependencies import get_token
from src.security.exceptions import BaseSecurityError
from src.security.interfaces import JWTAuthManagerInterface

router = APIRouter(prefix="/orders", tags=["Orders"])


def _decode_token(
        token: str,
        jwt_manager: JWTAuthManagerInterface
) -> dict:
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


def _build_order_response(order: OrderModel) -> OrderResponseSchema:
    """
    Build an OrderResponseSchema from an OrderModel instance.

    Args:
        order: The OrderModel ORM instance.

    Returns:
        OrderResponseSchema: Serialized order.
    """
    return OrderResponseSchema(
        id=order.id,
        user_id=order.user_id,
        created_at=order.created_at,
        status=order.status,
        total_amount=float(order.total_amount) if order.total_amount else None,
        items=[
            OrderItemResponseSchema(
                id=item.id,
                movie_id=item.movie_id,
                price_at_order=float(item.price_at_order),
            )
            for item in order.items
        ]
    )


@router.post(
    "/",
    response_model=OrderResponseSchema,
    summary="Create order from cart",
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
) -> OrderResponseSchema:
    """
    Create an order from the user's shopping cart.

    Steps:
    - Authenticate user.
    - Verify cart is not empty.
    - Exclude already purchased movies.
    - Ensure all movies are available.
    - Check no pending orders with the same movies exist.
    - Create order with items and total amount.
    - Clear the cart after order creation.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.

    Returns:
        OrderResponseSchema: The created order.

    Raises:
        HTTPException: If cart is empty, movies unavailable, or duplicate pending order.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = cast(int, payload.get("user_id"))

    # Get user's cart.
    cart = (
        await db.execute(
            select(CartModel).where(CartModel.user_id == user_id))
    ).scalars().first()

    if not cart:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty."
        )

    # Get cart items.
    cart_items = (
        await db.execute(
            select(CartItemModel).where(CartItemModel.cart_id == cart.id))
    ).scalars().all()

    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart is empty."
        )

    # Get movie IDs and fetch movies.
    movie_ids = [item.movie_id for item in cart_items]
    movies = (
        await db.execute(
            select(MovieModel).where(MovieModel.id.in_(movie_ids)))
    ).scalars().all()
    movie_map = {movie.id: movie for movie in movies}

    # Filter out already purchased movies.
    purchased_ids_result = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(
            OrderModel.user_id == user_id,
            OrderModel.status == OrderStatusEnum.PAID,
            OrderItemModel.movie_id.in_(movie_ids),
        )
    )
    purchased_ids = {row[0] for row in purchased_ids_result.all()}

    available_items = [
        item for item in cart_items
        if item.movie_id in movie_map and item.movie_id not in purchased_ids
    ]

    if not available_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "No available movies to order. "
                "All items are already purchased or unavailable."
            )
        )

    # Create order.
    total = sum(
        movie_map[item.movie_id].price for item in available_items
    )
    order = OrderModel(
        user_id=user_id,
        status=OrderStatusEnum.PENDING,
        total_amount=total,
    )
    try:
        db.add(order)
        await db.flush()

        # Create order items.
        for item in available_items:
            movie = movie_map[item.movie_id]
            order_item = OrderItemModel(
                order_id=order.id,
                movie_id=item.movie_id,
                price_at_order=movie.price,
            )
            db.add(order_item)

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    await db.refresh(order)

    return _build_order_response(order)


@router.get(
    "/",
    response_model=OrderListResponseSchema,
    summary="List user's orders",
)
async def list_orders(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    order_status: str | None = Query(
        None,
        description="Filter by status: pending, paid, canceled"
    ),
) -> OrderListResponseSchema:
    """
    List the authenticated user's orders with optional status filter.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.
        page (int): Page number.
        per_page (int): Items per page.
        order_status (str, optional): Filter by order status.

    Returns:
        OrderListResponseSchema: Paginated list of orders.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    stmt = select(OrderModel).where(OrderModel.user_id == user_id)
    if order_status:
        stmt = stmt.where(OrderModel.status == order_status)

    # Count.
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(
        OrderModel.created_at.desc()
    ).offset(
        (page - 1) * per_page
    ).limit(per_page)
    result = await db.execute(stmt)
    orders = result.scalars().unique().all()

    return OrderListResponseSchema(
        items=[_build_order_response(o) for o in orders],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "/{order_id}/cancel/",
    response_model=OrderResponseSchema,
    summary="Cancel an order",
)
async def cancel_order(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    order_id: int,
    token: str = Depends(get_token),
) -> OrderResponseSchema:
    """
    Cancel a pending order.

    Only orders with 'pending' status can be canceled directly.
    Paid orders require a refund request.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        order_id (int): The order's ID.
        token (str): The authentication token.

    Returns:
        OrderResponseSchema: The canceled order.

    Raises:
        HTTPException: If order not found, not owned by user, or not pending.
    """
    payload = _decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    order = (
        await db.execute(
            select(OrderModel).where(
                OrderModel.id == order_id,
                OrderModel.user_id == user_id))
    ).scalars().first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only pending orders can be canceled. "
                "Paid orders require a refund request."
            )
        )

    order.status = OrderStatusEnum.CANCELED
    await db.commit()
    await db.refresh(order)

    return _build_order_response(order)
