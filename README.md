
---

# 🎬 FastAPI Online Cinema API

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)
![Celery](https://img.shields.io/badge/Celery-37814A?style=for-the-badge&logo=celery&logoColor=white)

A production-ready REST API for an online cinema platform built with **FastAPI**.

The project demonstrates modern backend architecture, asynchronous programming, JWT authentication, role-based authorization, payments, background tasks, object storage, automated database seeding, and comprehensive testing.

---

## ✨ Features

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

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **Docker & Docker Compose** (for containerized setup)
- **Poetry** (for local development)

### 1. Clone the repository

```bash
git clone https://github.com/vmyronets/fastapi-online-cinema

```
Go to the project directory:
```bash
cd fastapi-online-cinema

```

### 2. Configure the Environment

Create an `.env` file from the provided template:

```bash
cp .env.sample .env

```

Ensure the host addresses in your `.env` are set correctly for local access:

```ini
POSTGRES_HOST=localhost
DATABASE_URL=postgresql+asyncpg://cinema_user:cinema_password@localhost:5432/cinema_db
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT_URL=http://localhost:9000

```

---

### 3. Start the Development Environment

Boot up the infrastructure and API using Docker Compose:

```bash
docker compose -f docker-compose.yml -f docker-compose-dev.yml up --build

```

💡This starts:
- **PostgreSQL 17** — database (with health check)
- **Redis** — Celery broker (with health check)
- **MinIO** — S3-compatible storage (with auto bucket creation)
- **FastAPI app** — API server (waits for all dependencies)
- **Celery worker** — background task processing
- **Celery beat** — periodic task scheduler

It will also automatically apply Alembic migrations, create the default MinIO storage bucket, and safely seed the database
with default roles, categories, and administrator accounts. Finally, the FastAPI server boots with hot-reload enabled.

### 4. Access the Services

Once running, you can access the following interfaces:

* **API Base URL:** [http://localhost:8000](http://localhost:8000)
* **Swagger UI (Interactive Docs):** [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
* **MinIO Console:** [http://localhost:9001](http://localhost:9001) *(Default credentials: `minioadmin` / `minioadmin`)*

### 5. Stopping the Environment

To gracefully stop all services:

```bash
docker compose down

```

*(Append `-v` to the command if you want to completely wipe the database volumes and start fresh next time).*

---

## 👥 Accounts & Authorization

The automatic seeding process provisions initial administrative accounts. Passwords and specific emails are configured in `./src/database/seeds/constants.py`.

### Roles and Permissions

| Role | Capabilities |
| --- | --- |
| **User** | Browse catalog, manage cart & orders, rate/comment/like movies, manage personal profile. |
| **Moderator** | *All User permissions* + CRUD operations for movies, genres, actors, and viewing sales metrics. |
| **Admin** | *All Moderator permissions* + user management, changing user groups, and account activation. |


---

## 🧪 Testing

The project includes a comprehensive suite of unit, integration, and end-to-end API tests.
Tests run in isolation using **SQLite**, a mocked S3 client, and mocked email dispatchers, meaning no external network services are required.

To run the test suite and generate a coverage report:

```bash
docker compose -f docker-compose-test.yml run --rm tests

```

> Coverage reports are automatically generated in the `htmlcov/` directory and `coverage.xml`.

---

## 💻 Useful Commands

Here are some helpful shortcuts for common development tasks:

**Rebuild Docker containers from scratch:**

```bash
docker compose build --no-cache

```

**Access the running application container:**

```bash
docker compose exec app bash

```

**Access the PostgreSQL database directly:**

```bash
docker compose exec db psql -U $POSTGRES_USER -d$POSTGRES_DB

```

**Run an Alembic migration manually:**

```bash
docker compose exec app alembic upgrade head

```

---

## 📈 Future Improvements

* [ ] GitHub Actions CI pipeline
* [ ] Production deployment configurations
* [ ] Docker image publishing to a registry
* [ ] Kubernetes manifests (Helm charts)
* [ ] Monitoring & Logging (Prometheus/Grafana)
* [ ] API rate limiting implementation

---

## 📄 License

This project was created for educational purposes.

```

```