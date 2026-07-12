"""
FastAPI Online Cinema application entry point.

Configures the FastAPI application with all routers, middleware,
and startup/shutdown events. Serves as the main ASGI application.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.accounts.routes import router as accounts_router
from src.movies.routes import router as movies_router
from src.cart.routes import router as cart_router
from src.orders.routes import router as orders_router
from src.payments.routes import router as payments_router
from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    On startup, initializes database connections and services.
    On shutdown, cleans up resources.

    Args:
        app: The FastAPI application instance.
    """
    # Startup: any initialization logic can go here.
    yield
    # Shutdown: cleanup logic can go here.


app = FastAPI(
    title="FastAPI Online Cinema",
    description=(
        "A comprehensive movie streaming platform with user authentication, "
        "movie catalog, shopping cart, orders, and payment processing."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None
)

# ──────────────────────────────────────────────
# Register API routers
# ──────────────────────────────────────────────

api_version_prefix = "/api/v1"

app.include_router(
    accounts_router,
    prefix=api_version_prefix,
    tags=["Accounts"]
)
app.include_router(
    movies_router,
    prefix=api_version_prefix,
    tags=["Movies"]
)
app.include_router(
    cart_router,
    prefix=api_version_prefix,
    tags=["Cart"]
)
app.include_router(
    orders_router,
    prefix=api_version_prefix,
    tags=["Orders"]
)
app.include_router(
    payments_router,
    prefix=api_version_prefix,
    tags=["Payments"]
)


@app.get("/", summary="Health check", tags=["Health"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns a simple status message to verify the API is running.

    Returns:
        dict: Status message.
    """
    return {"status": "ok", "message": "FastAPI Online Cinema is running."}
