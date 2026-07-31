"""
API routes for the payments module.

Provides endpoints for initiating payments via Stripe,
handling webhooks, and viewing payment history.
"""
from datetime import date

import stripe
import aiosmtplib
from typing import cast

from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi.responses import HTMLResponse

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
    BackgroundTasks
)
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from src.accounts.models import UserModel, UserGroupEnum
from src.security.dependencies import (
    SessionDep,
    JWTManagerDep,
    get_token,
    decode_token,
    require_admin_or_moderator
)
from src.movies.models import MovieModel
from src.config import settings
from src.cart.models import CartModel, CartItemModel
from src.orders.models import OrderModel
from src.orders.models.enums import OrderStatusEnum
from src.payments.models import (
    PaymentModel,
    PaymentItemModel,
    PaymentStatusEnum
)
from src.payments.schemas import (
    PaymentResponseSchema,
    PaymentItemResponseSchema,
    PaymentListResponseSchema,
    StripeCheckoutResponseSchema,
)

from src.security.interfaces import JWTAuthManagerInterface

router = APIRouter(prefix="/payments", tags=["Payments"])

# Set Stripe secret key from environment variables
stripe.api_key = settings.STRIPE_SECRET_KEY


def _build_payment_response(payment: PaymentModel) -> PaymentResponseSchema:
    """
    Build a PaymentResponseSchema from a PaymentModel instance.

    Args:
        payment: The PaymentModel ORM instance.

    Returns:
        PaymentResponseSchema: Serialized payment.
    """
    return PaymentResponseSchema(
        id=payment.id,
        user_id=payment.user_id,
        order_id=payment.order_id,
        created_at=payment.created_at,
        status=payment.status,
        amount=payment.amount,
        external_payment_id=payment.external_payment_id,
        items=[
            PaymentItemResponseSchema(
                id=item.id,
                order_item_id=item.order_item_id,
                price_at_payment=item.price_at_payment
            )
            for item in payment.items
        ]
    )


async def send_payment_confirmation_email(
        user_email: str,
        order_id: int,
        amount: Decimal
) -> None:
    """
    Asynchronously sends a payment confirmation email.

    Uses MIMEMultipart to send both plain-text and HTML versions of the email
    to ensure high deliverability and good formatting.

    Args:
        user_email (str): The email address of the user.
        order_id (int): The ID of the confirmed order.
        amount (Decimal): The total amount paid.
    """
    # Format the amount to two decimal places (for example, 10.50)
    formatted_amount = amount.quantize(Decimal("0.01"))

    # Create a container. The "alternative" type tells the client to choose
    # the best format it supports.
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Payment Confirmation - Order #{order_id}"
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = user_email

    # Creating a basic text version (fallback)
    text_body = (
        f"Hello,\n\n"
        f"Thank you for your order!\n"
        f"Your payment of ${formatted_amount} for Order #{order_id} "
        f"was successfully processed.\n\n"
        f"Best regards,\n"
        f"The Best Team"
    )
    part_text = MIMEText(text_body, "plain")

    # Create an HTML version
    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #4CAF50;">Payment Successful! 🎉</h2>
        <p>Hello,</p>
        <p>Thank you for your order. We are pleased to confirm that your payment of
           <strong>${formatted_amount}</strong> for Order <strong>#{order_id}</strong>
           was successfully processed.
        </p>
        <br>
        <p>Best regards,<br><strong>The Best Team</strong></p>
      </body>
    </html>
    """
    part_html = MIMEText(html_body, "html")

    msg.attach(part_text)
    msg.attach(part_html)

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True
        )
        print(
            f"ASYNC EMAIL SENT: Success for Order #{order_id} to {user_email}")

    except aiosmtplib.SMTPException as e:
        print(f"FAILED to send async email to {user_email}. Error: {str(e)}")


@router.post(
    "/orders/{order_id}/pay/",
    response_model=StripeCheckoutResponseSchema,
    summary="Initiate payment for an order",
    status_code=status.HTTP_201_CREATED,
)
async def pay_order(
        db: SessionDep,
        jwt_manager: JWTManagerDep,
        order_id: int,
        token: str = Depends(get_token),
) -> StripeCheckoutResponseSchema:
    """
    Initiate a Stripe Checkout session for a pending order.

    Steps:
    1. Authenticate user & verify the order is PENDING.
    2. Calculate total amount.
    3. Create a Stripe Checkout Session with order line items.
    4. Create a Payment record with status PENDING and link the Stripe session ID.

    Args:
    db (AsyncSession): The asynchronous database session.
    jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
    order_id (int): The order's ID.
    token (str): The authentication token.

    Returns:
        StripeCheckoutResponseSchema: The created payment details.

    Raises:
        HTTPException: If order not found, not pending, or payment fails.
    """
    payload = decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    # Fetch order with its items
    order = (
        await db.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order_id,
                   OrderModel.user_id == user_id
                   )
        )
    ).scalars().first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found."
        )

    if order.status != OrderStatusEnum.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is already {order.status}. "
                   f"Only pending orders can be paid."
        )

    movie_ids = [item.movie_id for item in order.items]

    movies = (
        await db.execute(
            select(MovieModel).where(MovieModel.id.in_(movie_ids))
        )
    ).scalars().all()

    if len(movies) != len(movie_ids):
        raise HTTPException(
            status_code=400,
            detail="Some movies are no longer available."
        )

    movie_map = {movie.id: movie for movie in movies}

    # Build Stripe line items from order items
    # Stripe expects amounts in cents (e.g., $10.00 = 1000)
    line_items = []
    total_amount = Decimal("0")

    for item in order.items:
        movie = movie_map[item.movie_id]
        current_price = movie.price
        item.price_at_order = current_price
        total_amount += current_price

        line_items.append({
            "price_data": {
                "currency": "usd",
                "product_data": {
                    "name": movie.name
                },
                "unit_amount": int(current_price * 100)
            },
            "quantity": 1
        })

    order.total_amount = total_amount

    try:
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            # Stripe will automatically replace
            # {CHECKOUT_SESSION_ID} with the actual ID
            success_url=f"{settings.APP_BASE_URL}/payments/success"
                        f"?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.APP_BASE_URL}/payments/cancel",
            # We store the order_id in metadata so the webhook
            # knows which order to update
            metadata={"order_id": order.id, "user_id": user_id}
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Stripe: {str(e)}"
        )

    # Create Payment record in PENDING state
    payment = PaymentModel(
        user_id=cast(int, user_id),
        order_id=cast(int, order.id),
        status=PaymentStatusEnum.PENDING,
        amount=total_amount,
        external_payment_id=checkout_session.id
    )
    db.add(payment)
    await db.commit()

    return StripeCheckoutResponseSchema(
        checkout_url=checkout_session.url,
        session_id=checkout_session.id
    )


@router.get(
    "/",
    response_model=PaymentListResponseSchema,
    summary="List user's payments",
)
async def list_payments(
    db: SessionDep,
    jwt_manager: JWTManagerDep,
    token: str = Depends(get_token),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    payment_status: PaymentStatusEnum | None = Query(
        None,
        description="Filter by status: successful, canceled, refunded"
    )
) -> PaymentListResponseSchema:
    """
    List the authenticated user's payment history.

    Args:
        db (AsyncSession): The asynchronous database session.
        jwt_manager (JWTAuthManagerInterface): JWT manager for decoding.
        token (str): The authentication token.
        page (int): Page number.
        per_page (int): Items per page.
        payment_status (str, optional): Filter by payment status.

    Returns:
        PaymentListResponseSchema: Paginated list of payments.
    """
    payload = decode_token(token, jwt_manager)
    user_id = payload.get("user_id")

    stmt = select(PaymentModel).where(PaymentModel.user_id == user_id)
    if payment_status:
        stmt = stmt.where(PaymentModel.status == payment_status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = (
        stmt.order_by(PaymentModel.created_at.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )
    result = await db.execute(stmt)
    payments = result.scalars().unique().all()

    return PaymentListResponseSchema(
        items=[_build_payment_response(payment) for payment in payments],
        total=total,
        page=page,
        per_page=per_page
    )


@router.post(
    "/webhook/stripe/",
    summary="Stripe webhook handler",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(
        request: Request,
        background_tasks: BackgroundTasks,
        db: SessionDep
) -> dict:
    """
    Handle incoming Stripe webhook events.

    This endpoint verifies the signature sent by Stripe to ensure security,
    then processes specific events like 'checkout.session.completed' and
    clears the cart after order creation.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        # Verify the signature using the webhook secret
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        # Invalid payload
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the successful checkout session
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        session_id = session.get("id")

        # We need to find our PENDING payment by the session ID
        payment = (
            await db.execute(
                select(PaymentModel).where(
                    PaymentModel.external_payment_id == session_id)
            )
        ).scalars().first()

        if payment and payment.status == PaymentStatusEnum.PENDING:
            # Update Payment status
            payment.status = PaymentStatusEnum.SUCCESSFUL

            # Fetch Order and update its status
            order = (
                await db.execute(
                    select(OrderModel)
                    .options(selectinload(OrderModel.items),
                             selectinload(OrderModel.user)
                             )
                    .where(OrderModel.id == payment.order_id)
                )
            ).scalars().first()

            if order:
                order.status = OrderStatusEnum.PAID

                # Create PaymentItems exactly at the moment of payment success
                for order_item in order.items:
                    payment_item = PaymentItemModel(
                        payment_id=payment.id,
                        order_item_id=order_item.id,
                        price_at_payment=order_item.price_at_order,
                    )
                    db.add(payment_item)

                # Clear cart.
                cart = (
                    await db.execute(
                        select(CartModel).where(
                            CartModel.user_id == order.user_id)
                    )
                ).scalars().first()

                if cart:
                    await db.execute(
                        delete(CartItemModel).where(
                            CartItemModel.cart_id == cart.id
                        )
                    )

                # Retrieve user email for the background task
                user_email = order.user.email

                # Schedule confirmation email in the background
                background_tasks.add_task(
                    send_payment_confirmation_email,
                    user_email=user_email,
                    order_id=order.id,
                    amount=payment.amount
                )

            await db.commit()

    return {"status": "success"}


@router.get(
    "/admin/payments",
    response_model=PaymentListResponseSchema,
    summary="Moderator/Admin: List all payments with filters"
)
async def admin_list_payments(
        db: SessionDep,
        current_user: UserModel = Depends(require_admin_or_moderator),
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        user_id: int | None = Query(
            None,
            description="Filter payments by user ID"
        ),
        payment_status: PaymentStatusEnum | None = Query(
            None,
            description="Filter payments by status"
        ),
        date_from: date | None = Query(
            None,
            description="Filter from date (YYYY-MM-DD)"
        ),
        date_to: date | None = Query(
            None,
            description="Filter to date (YYYY-MM-DD)"
        )
) -> PaymentListResponseSchema:
    """
    List all user payments with optional filters.
    Accessible only by users in ADMIN or MODERATOR groups.
    """

    # Creating a basic query for Payments
    stmt = select(PaymentModel)

    # Applying filters
    if user_id:
        stmt = stmt.where(PaymentModel.user_id == user_id)
    if payment_status:
        stmt = stmt.where(PaymentModel.status == payment_status)
    if date_from:
        stmt = stmt.where(func.date(PaymentModel.created_at) >= date_from)
    if date_to:
        stmt = stmt.where(func.date(PaymentModel.created_at) <= date_to)

    # Calculate the total count (for pagination)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    # Pagination and sorting
    stmt = (
        stmt.order_by(PaymentModel.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    payments = (await db.execute(stmt)).scalars().unique().all()

    return PaymentListResponseSchema(
        items=[_build_payment_response(payment) for payment in payments],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get(
    "/success",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def payment_success_page(session_id: str):
    """Simple HTML page to redirect users after successful payment."""

    return f"""
    <html>
        <body style="font-family: Arial; display: flex; flex-direction:
         column; align-items: center; justify-content: center;
         height: 100vh; background-color: #f0fdf4;">
            <h1 style="color: #16a34a;">Payment Successful! 🎉</h1>
            <p>Your Stripe Session ID is: <b>{session_id}</b></p>
            <p>You can now close this tab.</p>
        </body>
    </html>
    """


@router.get(
    "/cancel",
    response_class=HTMLResponse,
    include_in_schema=False
)
async def payment_cancel_page():
    """Simple HTML page to redirect users after canceled payment."""
    return """
    <html>
        <body style="font-family: Arial; display: flex; flex-direction: column;
         align-items: center; justify-content: center; height: 100vh;
         background-color: #fef2f2;">
            <h1 style="color: #dc2626;">Payment failed or was canceled ❌.
                    Please try another payment method or another card.</h1>
            <p>The checkout process was aborted. No charges were made.</p>
        </body>
    </html>
    """
