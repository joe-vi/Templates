# FastAPI Clean Architecture Template

A production-ready FastAPI application template built with Clean Architecture principles, PostgreSQL (via Docker), async SQLAlchemy, JWT authentication, and dependency injection.

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
- **Dependency Injection**: FastAPI-native `Depends` providers; the composition root lives in `src/api/dependencies/providers.py` (no separate IoC container)
- **Request-Scoped Sessions**: A single `AsyncSession` per request, provided by `get_session` and shared by every adapter in that request — a natural unit of work, with no module-global session state
- **Ports & Adapters**: Collaborators are defined as `typing.Protocol` ports and implemented by mechanism-qualified adapters (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`)
- **Role-Based Access**: User roles (`admin`, `user`) and statuses (`active`, `inactive`) stored as lowercase enums
- **Package Management**: Modern Python package management with `uv`
- **Database Migrations**: Alembic for schema versioning; bootstrap admin user seeded via migration

## Project Structure

```
.
├── src/
│   ├── config/
│   │   └── settings.py                     # Pydantic settings + cached get_settings()
│   ├── domain/                             # Business entities, enums, repository ports (no external deps)
│   │   ├── entities/
│   │   │   └── user/
│   │   │       └── user.py                 # User domain entity (dataclass)
│   │   ├── enums/
│   │   │   ├── operation_results.py        # Generic CreateResult, UpdateResult, DeleteResult, LoginResult
│   │   │   └── user_enum.py                # UserRole, UserStatus (StrEnum, lowercase values)
│   │   └── repositories/
│   │       └── user/
│   │           └── user_repository.py      # UserRepository Protocol (port)
│   ├── application/                        # Use cases, DTOs, service ports (imports Domain only)
│   │   ├── services/                       # Protocol ports
│   │   │   ├── logger.py                    # Logger
│   │   │   ├── password_hasher.py           # PasswordHasher
│   │   │   └── token_service.py             # TokenService
│   │   └── use_cases/
│   │       ├── auth/
│   │       │   ├── auth_dto.py
│   │       │   └── auth_use_case.py        # AuthUseCase (concrete)
│   │       └── user/
│   │           ├── user_converter.py       # Entity ↔ DTO conversion (module functions)
│   │           ├── user_dto.py
│   │           └── user_use_case.py        # UserUseCase (concrete)
│   ├── infrastructure/                     # Adapters (imports Domain + Application)
│   │   ├── auth/
│   │   │   ├── bcrypt_password_hasher.py   # bcrypt via passlib
│   │   │   └── jwt_token_service.py        # PyJWT access + refresh tokens
│   │   ├── database/
│   │   │   ├── base.py                     # SQLAlchemy DeclarativeBase
│   │   │   ├── session.py                  # create_engine / create_session_factory
│   │   │   └── models/
│   │   │       └── user_model.py           # ORM model for users table
│   │   ├── logging/
│   │   │   ├── json_logger.py              # Structured JSON logger (singleton)
│   │   │   └── log_context.py              # request_id / user_id context vars
│   │   └── repositories/
│   │       └── user/
│   │           └── sqlalchemy_user_repository.py   # Async CRUD adapter
│   ├── api/                                # Routes, schemas, dependency providers
│   │   ├── dependencies/
│   │   │   ├── database.py                 # get_session (request-scoped AsyncSession)
│   │   │   ├── providers.py                # composition root: ports → adapters, use-case builders
│   │   │   └── jwt_dependency.py           # JWT guard (get_current_user)
│   │   ├── routers/
│   │   │   ├── auth/{auth_converter,auth_routes,auth_schema}.py
│   │   │   └── user/{user_converter,user_routes,user_schema}.py
│   │   ├── schemas/
│   │   │   ├── base_schema.py              # APIModelBase — camelCase JSON base for all schemas
│   │   │   └── operation_schema.py         # Shared response envelope
│   │   └── result_status_maps.py           # Operation result → HTTP status + message maps
│   └── main.py                             # FastAPI app, lifespan (engine), request-id middleware, routers
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
- **Repository Ports**: `typing.Protocol` interfaces with clean names (`UserRepository`)
- **Rule**: No dependencies on any other layer

### 2. Application Layer (`src/application/`)
- **Use Cases**: Plain concrete classes holding the business logic (`UserUseCase`, `AuthUseCase`)
- **DTOs**: Frozen dataclasses with `DTO` suffix
- **Service Ports**: `PasswordHasher`, `TokenService`, `Logger` (Protocols)
- **Converters**: Module-level functions for entity ↔ DTO mapping
- **Rule**: Imports Domain only

### 3. Infrastructure Layer (`src/infrastructure/`)
- **Database**: `session.py` builds the engine + `async_sessionmaker`; the session is provided per request (no factory object, no shared `ContextVar`)
- **Repository Adapters**: `SqlAlchemyUserRepository` takes an `AsyncSession`; mutations own their commit and map DB errors to result enums
- **Auth/Logging Adapters**: `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`
- **Rule**: Implements (structurally satisfies) the ports from the Domain and Application layers

### 4. API Layer (`src/api/`)
- **Routes**: FastAPI endpoints that depend on the concrete use case via `Annotated[UserUseCase, Depends(get_user_use_case)]` and **return response models** (FastAPI serialises them to camelCase)
- **Dependencies**: `providers.py` is the composition root (ports → adapters); `database.py` yields the request-scoped session; `jwt_dependency.py` is the JWT guard
- **Schemas**: Pydantic request/response models; all inherit `APIModelBase` (camelCase JSON, snake_case Python attributes)
- **Rule**: Wires adapters to ports in `dependencies/`; routes never call repositories directly

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

PostgreSQL 18 is the storage layer for this template. A `docker-compose.yml` is included so no local Postgres installation is required — Docker is the only prerequisite.

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

1. **Domain**: Add entity in `src/domain/entities/<name>/` and a repository **Protocol** port in `src/domain/repositories/<name>/<name>_repository.py` (clean name, e.g. `OrderRepository`)
2. **Application**: Add DTO, converter functions, and a concrete use case in `src/application/use_cases/<name>/`
3. **Infrastructure**: Add ORM model in `src/infrastructure/database/models/` and a `sqlalchemy_<name>_repository.py` adapter (takes an `AsyncSession`) in `src/infrastructure/repositories/<name>/`
4. **API**: Add Pydantic schemas (inheriting `APIModelBase`), converter functions, and routes in `src/api/routers/<name>/` that return response models
5. **Providers**: Add provider functions in `src/api/dependencies/providers.py`:
   ```python
   def get_order_repository(session: Annotated[AsyncSession, Depends(get_session)]) -> OrderRepository:
       return SqlAlchemyOrderRepository(session)

   def get_order_use_case(repository: Annotated[OrderRepository, Depends(get_order_repository)]) -> OrderUseCase:
       return OrderUseCase(repository=repository)
   ```
6. **Main**: Include the new router in `src/main.py`
7. **Migration**: Generate and apply an Alembic migration for any new DB models

## Design Principles

1. **Dependency Inversion**: Use cases depend on `Protocol` ports, not concrete adapters
2. **Single Responsibility**: One use case per operation; one CRUD operation per repository method
3. **Open/Closed**: Swap an adapter by changing the `return` in its provider function only
4. **Interface Segregation**: Small, focused ports (Protocols) per collaborator
5. **Async/Await**: Full async support for all database and I/O operations

## License

MIT License
