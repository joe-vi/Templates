# FastAPI Clean Architecture Template

A production-ready FastAPI application template built with Clean Architecture principles, async SQLAlchemy, JWT authentication, and dependency injection.

## Get This Template

Navigate to your target directory first, then run the appropriate command for your OS:

**macOS / Linux**
```bash
curl -fsSL https://github.com/joe-vi/Templates/archive/refs/heads/main.tar.gz | tar -xz --strip-components=3 "Templates-main/FastAPI/API_PostgressDB"
```

**Windows (PowerShell)**
```powershell
Invoke-WebRequest -Uri "https://github.com/joe-vi/Templates/archive/refs/heads/main.zip" -OutFile t.zip; Expand-Archive t.zip .; Move-Item "Templates-main/FastAPI/API_PostgressDB/*" .; Remove-Item Templates-main,t.zip -Recurse
```

## Features

- **Clean Architecture**: Four-layer separation of concerns — Domain, Application, Infrastructure, API
- **Async Database**: Asynchronous PostgreSQL operations using SQLAlchemy 2.0+ and asyncpg
- **JWT Authentication**: Access and refresh token pair with configurable expiry
- **Dependency Injection**: Automatic DI with `fastapi-injector` using `Injected[Type]` annotations
- **Connection Factory**: Async context manager for per-repository session management (singleton scope)
- **Transaction Manager**: Atomic multi-repository operations via a shared session
- **Role-Based Access**: User roles (`admin`, `user`) and statuses (`active`, `inactive`) stored as lowercase enums
- **Type Safety**: Full type hints with ABC base classes (`Base` suffix) for all abstractions
- **Package Management**: Modern Python package management with `uv`
- **Database Migrations**: Alembic for schema versioning; bootstrap admin user seeded via migration

## Project Structure

```
.
├── src/
│   ├── config/
│   │   └── settings.py                     # Pydantic settings loaded from .env
│   ├── domain/                             # Business entities, enums, repository ABCs (no external deps)
│   │   ├── entities/
│   │   │   └── user/
│   │   │       └── user.py                 # User domain entity (dataclass)
│   │   ├── enums/
│   │   │   ├── operation_results.py        # Generic CreateResult, UpdateResult, DeleteResult, LoginResult
│   │   │   └── user_enum.py                # UserRole, UserStatus (StrEnum, lowercase values)
│   │   └── repositories/
│   │       └── user/
│   │           └── user_repository_base.py # Abstract user repository interface
│   ├── application/                        # Use cases, DTOs, service ABCs (imports Domain only)
│   │   ├── services/
│   │   │   ├── custom_logger_base.py
│   │   │   ├── password_hasher_base.py
│   │   │   ├── token_service_base.py
│   │   │   ├── transaction_manager_base.py
│   │   │   └── user_context_base.py
│   │   └── use_cases/
│   │       ├── auth/
│   │       │   ├── auth_dto.py
│   │       │   ├── auth_use_case.py
│   │       │   └── auth_use_case_base.py
│   │       └── user/
│   │           ├── user_converter.py       # Domain entity ↔ DTO conversion
│   │           ├── user_dto.py
│   │           ├── user_use_case.py
│   │           └── user_use_case_base.py
│   ├── infrastructure/                     # Concrete implementations (imports Domain + Application)
│   │   ├── auth/
│   │   │   ├── password_hasher.py          # bcrypt via passlib
│   │   │   ├── token_service.py            # PyJWT access + refresh tokens
│   │   │   └── user_context.py             # Extracts user identity from JWT
│   │   ├── database/
│   │   │   ├── base.py                     # SQLAlchemy DeclarativeBase
│   │   │   ├── connection_factory.py       # Async session factory (singleton)
│   │   │   ├── connection_factory_base.py
│   │   │   ├── transaction_manager.py      # Shared-session atomic operations
│   │   │   └── models/
│   │   │       └── user_model.py           # ORM model for users table
│   │   ├── logging/
│   │   │   └── custom_logger.py            # Request-scoped structured logger
│   │   └── repositories/
│   │       └── user/
│   │           └── user_repository.py      # Async CRUD implementation
│   ├── api/                                # Routes and schemas (imports Application ABCs only)
│   │   ├── dependencies/
│   │   │   └── jwt_dependency.py           # JWT guard — resolves current user via Depends()
│   │   ├── routers/
│   │   │   ├── auth/
│   │   │   │   ├── auth_converter.py
│   │   │   │   ├── auth_routes.py
│   │   │   │   └── auth_schema.py
│   │   │   └── user/
│   │   │       ├── user_converter.py
│   │   │       ├── user_routes.py
│   │   │       └── user_schema.py
│   │   ├── schemas/
│   │   │   └── operation_schema.py         # Shared response envelope
│   │   └── result_status_maps.py           # Operation result → HTTP status + message
│   ├── container.py                        # DI bindings (imports all layers)
│   └── main.py                             # FastAPI app, middleware, router registration
├── tests/
│   ├── api/
│   │   └── routers/
│   │       └── user/
│   │           ├── test_user_converter.py
│   │           └── test_user_routes.py     # Route tests via minimal FastAPI + TestModule
│   └── application/
│       └── use_cases/
│           └── user/
│               ├── test_user_converter.py
│               └── test_user_use_case.py   # Use case tests via AsyncMock repositories
├── alembic/                                # Database migration scripts
├── alembic.ini
├── docker-compose.yml                      # PostgreSQL 18
├── pyproject.toml
├── .env.example
└── README.md
```

## Clean Architecture Layers

### 1. Domain Layer (`src/domain/`)
- **Entities**: Core business objects as dataclasses (`User`)
- **Enums**: `UserRole` (admin/user), `UserStatus` (active/inactive), generic operation result enums
- **Repository Interfaces**: Abstract base classes ending in `Base` (`UserRepositoryBase`)
- **Rule**: No dependencies on any other layer

### 2. Application Layer (`src/application/`)
- **Use Cases**: Business logic with paired Base abstractions (`UserUseCaseBase` / `UserUseCase`, `AuthUseCaseBase` / `AuthUseCase`)
- **DTOs**: Frozen dataclasses with `DTO` suffix
- **Service ABCs**: `PasswordHasherBase`, `TokenServiceBase`, `TransactionManagerBase`, `UserContextBase`, `CustomLoggerBase`
- **Rule**: Imports Domain only

### 3. Infrastructure Layer (`src/infrastructure/`)
- **Database**: `ConnectionFactory` (async session, singleton), `TransactionManager` (shared-session atomic ops)
- **Repository Implementations**: Concrete async CRUD for each domain repository interface
- **Auth Implementations**: `PasswordHasher` (bcrypt/passlib), `TokenService` (PyJWT), `UserContext` (JWT → user identity)
- **Rule**: Implements interfaces from Domain and Application layers

### 4. API Layer (`src/api/`)
- **Routes**: FastAPI endpoints using `Injected[BaseClass]` for use case injection
- **Dependencies**: `jwt_dependency.py` — JWT guard using `Depends()` (the only permitted use of `Depends()` for auth guards)
- **Schemas**: Pydantic request/response models
- **Rule**: Imports Application ABCs only; never calls repositories directly

## Installation

### Prerequisites
- Python 3.11+
- Docker (for PostgreSQL)
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Download the template (see **Get This Template** above) or clone the repository.

2. Install uv (if not already installed):

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

3. Install dependencies:
```bash
uv sync
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env — set a strong JWT_SECRET_KEY for production
```

5. Start PostgreSQL:
```bash
docker compose up -d
```

6. Run database migrations (creates tables and seeds the bootstrap admin):
```bash
uv run alembic upgrade head
```

## Running the Application

### Option A: VS Code (Recommended)

A `.vscode/launch.json` is included for one-click debugging. Press `F5` or open the **Run and Debug** panel and select **FastAPI**.

### Option B: Command Line

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_DRIVER` | SQLAlchemy async driver | `postgresql+asyncpg` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | `postgres` |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `DB_NAME` | Database name | `fastapi_db` |
| `IS_SQL_ECHO_ENABLED` | Log SQL queries | `false` |
| `POOL_SIZE` | Connection pool size | `5` |
| `MAX_OVERFLOW` | Max overflow connections | `10` |
| `JWT_SECRET_KEY` | Secret for signing JWTs | `changeme-use-a-strong-random-secret-in-production` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Development

### Running Tests
```bash
uv run pytest
```

### Code Formatting
```bash
uv run ruff format src/
```

### Linting
```bash
uv run ruff check src/ --fix
```

### Type Checking
```bash
uv run mypy src/
```

### Database — Docker

```bash
docker compose up -d       # Start PostgreSQL
docker compose down        # Stop (data preserved)
docker compose down -v     # Stop and delete volume
```

### Database Migrations

```bash
uv run alembic upgrade head                              # Apply all migrations
uv run alembic revision --autogenerate -m "description" # Generate new migration
uv run alembic downgrade -1                              # Roll back one step
```

## Adding New Features

1. **Domain**: Add entity in `src/domain/entities/<name>/` and repository ABC in `src/domain/repositories/<name>/` (class name ending with `Base`)
2. **Application**: Add DTO, use case ABC and implementation, and a converter in `src/application/use_cases/<name>/`
3. **Infrastructure**: Add ORM model in `src/infrastructure/database/models/` and repository implementation in `src/infrastructure/repositories/<name>/`
4. **API**: Add Pydantic schemas, a converter, and routes in `src/api/routers/<name>/` using `Injected[UseCaseBase]`
5. **Container**: Register bindings in `src/container.py`:
   ```python
   binder.bind(NewRepositoryBase, to=NewRepository)
   binder.bind(NewUseCaseBase, to=NewUseCase)
   ```
6. **Main**: Include the new router in `src/main.py`
7. **Migration**: Generate and apply an Alembic migration for any new DB models

## Design Principles

1. **Dependency Inversion**: High-level modules depend on abstractions, not implementations
2. **Single Responsibility**: One use case per operation; one CRUD operation per repository method
3. **Open/Closed**: Swap implementations by changing container bindings only
4. **Interface Segregation**: All ABC classes end with `Base`
5. **Async/Await**: Full async support for all database and I/O operations

## License

MIT License
