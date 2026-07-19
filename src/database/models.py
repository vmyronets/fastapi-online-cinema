# import all models so Alembic and Celery can detect them for autogenerate.
from src.accounts.models import *  # noqa: F401,F403
from src.movies.models import *  # noqa: F401,F403
from src.cart.models import *  # noqa: F401,F403
from src.orders.models import *  # noqa: F401,F403
from src.payments.models import *  # noqa: F401,F403
