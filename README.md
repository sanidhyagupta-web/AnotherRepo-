# FastAPI Production Template

A reusable, production-ready FastAPI boilerplate that includes:
- JWT authentication and RBAC (`user`, `admin`)
- Async SQLAlchemy + PostgreSQL integration
- Environment-driven configuration
- Structured JSON logging
- Standardized error responses
- Pytest setup with coverage threshold
- Alembic migrations
- Docker image support

## Project Structure

```text
app/
  api/v1/endpoints/
  core/
  db/
  middleware/
  models/
  repositories/
  schemas/
  services/
alembic/
tests/
scripts/
```

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. Configure environment

```bash
cp .env.example .env
```

Update at least:
- `SECRET_KEY`
- `DATABASE_URL`

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the application

```bash
uvicorn app.main:app --reload
```

Docs:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- OpenAPI JSON: `http://localhost:8000/api/v1/openapi.json`

## Required Environment Variables

| Variable | Description |
|---|---|
| `APP_ENV` | `development`, `test`, or `production` |
| `DATABASE_URL` | Primary async DB URL (PostgreSQL recommended) |
| `TEST_DATABASE_URL` | Separate DB URL for tests |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT algorithm (default: `HS256`) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry time |
| `CORS_ALLOW_ORIGINS` | JSON array of CORS origins |
| `TRUSTED_HOSTS` | JSON array of trusted hosts |
| `LOG_LEVEL` | Logging level by environment |

## Authentication Endpoints

- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Get JWT token
- `GET /api/v1/users/me` - Authenticated user profile
- `GET /api/v1/users/admin` - Admin-only user list

## Error Response Standard

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload",
    "details": []
  }
}
```

## Testing

Run tests with coverage:

```bash
pytest
```

Coverage threshold is enforced at `70%` via `pytest-cov`.

## Docker

Build image:

```bash
docker build -t fastapi-template:latest .
```

Run with compose:

```bash
docker compose up --build
```

## Security Notes

- Passwords are hashed with `passlib` (`pbkdf2_sha256`)
- JWT secrets come from environment variables
- Input validation uses Pydantic schemas
- Production can enforce trusted hosts
- Standardized errors avoid leaking internals

## How to Extend This Template

1. Add new API modules under `app/api/v1/endpoints`.
2. Keep routers thin and move logic to `services/`.
3. Use repositories for repeated query patterns.
4. Add schemas for every request/response contract.
5. Add tests for new behavior in `tests/unit` and `tests/integration`.
6. Generate and apply new Alembic migrations.

## Developer Workflow

You can use `scripts/bootstrap.sh` for local startup:

```bash
./scripts/bootstrap.sh
```
# AI-Track
