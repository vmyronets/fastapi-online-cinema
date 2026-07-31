
---

# FastAPI Online Cinema API

A production-style REST API for an online cinema platform built with **FastAPI**.

The project demonstrates modern backend architecture, asynchronous programming, JWT authentication, role-based authorization, payments, background tasks, object storage, automated database seeding, and comprehensive testing.

---

## Features

* JWT authentication (Access & Refresh tokens)
* User registration and email activation
* Password reset via email
* User profiles
* Movies, genres and certifications
* Shopping cart
* Orders
* Stripe payments
* Payment history
* Comments and likes
* Role-based permissions (User / Moderator / Admin)
* S3-compatible file storage (MinIO)
* Background tasks with Celery
* Database migrations with Alembic
* Automated database seeding
* Async SQLAlchemy 2.0
* Comprehensive pytest test suite

---

## Tech Stack

| Category           | Technologies            |
| ------------------ | ----------------------- |
| Language           | Python 3.12             |
| Framework          | FastAPI                 |
| Database           | PostgreSQL              |
| ORM                | SQLAlchemy 2.0          |
| Migrations         | Alembic                 |
| Validation         | Pydantic v2             |
| Authentication     | JWT                     |
| Background Tasks   | Celery + Redis          |
| Object Storage     | MinIO (S3 API)          |
| Payments           | Stripe                  |
| Testing            | Pytest + pytest-cov     |
| Dependency Manager | Poetry                  |
| Containerization   | Docker & Docker Compose |

---

## Project Structure

```text
.
├── alembic/
├── docker/
│   ├── entrypoint.dev.sh
│   └── entrypoint.test.sh
├── src/
│   ├── accounts/
│   ├── cart/
│   ├── config/
│   ├── database/
│   │   ├── models/
│   │   └── seeds/
│   ├── movies/
│   ├── notifications/
│   ├── orders/
│   ├── payments/
│   ├── security/
│   └── main.py
├── tests/
├── Dockerfile
├── docker-compose.yml
├── docker-compose-dev.yml
├── docker-compose-test.yml
├── pyproject.toml
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (for containerized setup)
- **Poetry** (for local development)

## Running the Application

**1. Clone the repository:**

```bash
git clone https://github.com/vmyronets/fastapi-online-cinema
cd fastapi-online-cinema
```

**2. Create an `.env` file from the template:**

```bash
cp .env.sample .env
```

Edit `.env` and update host addresses for local access:
```
POSTGRES_HOST=localhost
DATABASE_URL=postgresql+asyncpg://cinema_user:cinema_password@localhost:5432/cinema_db
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT_URL=http://localhost:9000
```

---

**3. Start development environment:**

```bash
docker compose -f docker-compose.yml -f docker-compose-dev.yml up --build
```

This starts:
- **PostgreSQL 17** — database (with health check)
- **Redis** — Celery broker (with health check)
- **MinIO** — S3-compatible storage (with auto bucket creation)
- **FastAPI app** — API server (waits for all dependencies)
- **Celery worker** — background task processing
- **Celery beat** — periodic task scheduler

**4. Access the application:**

- API: [http://localhost:8000](http://localhost:8000)
- Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- MinIO Console: [http://localhost:9001](http://localhost:9001) (minioadmin/minioadmin)

**5. Stop all services:**

```bash
docker compose down
# To also remove volumes (database data):
docker compose down -v
```

---

The application will:

* wait until PostgreSQL is ready
* apply Alembic migrations
* seed the database
* create the default MinIO bucket
* start FastAPI with hot reload

You can find the API documentation at the link:

```
http://localhost:8000/docs
```

---

## Running Tests

The test suite uses:

* SQLite
* mocked email sender
* mocked S3 client

No external services are required.

Run:

```bash
docker compose -f docker-compose-test.yml run --rm tests
```

Coverage reports:

```
htmlcov/
coverage.xml
```

---

## Default Accounts

The seed process automatically creates administrator accounts.

| Role      | Email                                             |
|-----------|---------------------------------------------------|
| Admin     | configured in `./src/database/seeds/constants.py` |
| Moderator | configured in `./src/database/seeds/constants.py` |
| User      | configured in `./src/database/seeds/constants.py` |

Passwords are also loaded from `./src/database/seeds/constants.py`.

## User Roles

| Role          | Permissions                                                                   |
|---------------|-------------------------------------------------------------------------------|
| **User**      | Browse catalog, manage cart/orders, rate/comment/like movies, manage profile  |
| **Moderator** | All User permissions + CRUD movies/genres/actors, view sales                  |
| **Admin**     | All Moderator permissions + manage users, change groups, activate accounts    |

---

## Database Seeding

The development environment automatically seeds:

* user groups
* administrator accounts
* certifications
* genres
* movies

Running the seed multiple times is safe.

---

## Useful Commands

Rebuild containers

```bash
docker compose build --no-cache
```

Open application container

```bash
docker compose exec app bash
```

Open PostgreSQL

```bash
docker compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

Run Alembic migration

```bash
docker compose exec app alembic upgrade head
```

---

## Testing

The project includes:

* unit tests
* integration tests
* end-to-end API tests

Coverage is generated automatically with `pytest-cov`.

---

## Future Improvements

* GitHub Actions CI
* Production deployment
* Docker image publishing
* Kubernetes manifests
* Monitoring & logging
* API rate limiting

---

## License

This project was created for educational purposes.

---
