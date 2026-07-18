# FastAPI Clean Architecture Template

A production-ready FastAPI application template built with Clean Architecture and Domain-Driven Design principles, PostgreSQL (via Docker), async SQLAlchemy, JWT authentication, and dependency injection.

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

- **Clean Architecture**: Four-layer separation of concerns — Domain, Application, Infrastructure, API — with dependencies flowing inward only, plus two dependency-free leaves (`src/ports/`, `src/shared/`) that every layer except Domain may import
- **Domain-Driven Design**: Rich aggregate roots that enforce their own invariants and expose intention-revealing behaviour (`user.activate()`, `user.is_active`) — never an anemic domain
- **Async Database**: Asynchronous PostgreSQL operations using SQLAlchemy 2.0+ and asyncpg
- **JWT Authentication**: Access and refresh token pair with configurable expiry
- **Dependency Injection**: `injector` with an in-house typed facade — one line binds implementation, port, and scope (`bind_typed(UserRepository).to(SqlAlchemyUserRepository, scope=request)`), constructors auto-wired via `@inject`, and a mismatched implementation is a pyrefly error at the binding line
- **Request-Scoped Sessions**: A single `AsyncSession` per request (a request-scoped provider, disposed automatically on request end), shared by every adapter in that request
- **Unit of Work**: Mutating use cases own the transaction boundary via the `TransactionContext` port — commit only on all-success, rollback-unless-committed; operations spanning several repositories inside one `begin()` block are atomic
- **Ports & Adapters**: Collaborators are defined as `typing.Protocol` ports and implemented by mechanism-qualified adapters (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`) that subclass their port and inherit its docstrings, so every contract is documented exactly once and IDE hover shows it everywhere
- **Fully Testable API Layer**: Route tests bind an `AsyncMock(spec=CreateUserUseCase)` in a test injector module — no database or adapters involved
- **Role-Based Access**: User roles (`admin`, `user`) and statuses (`active`, `inactive`) stored as lowercase enums
- **Package Management**: Modern Python package management with `uv`
- **Database Migrations**: Alembic for schema versioning; bootstrap admin user seeded via migration

## Project Structure

```
.
├── src/
│   ├── config/
│   │   └── settings.py                     # Pydantic settings + cached get_settings()
│   ├── domain/                             # Aggregate roots, enums, repository ports (no external deps)
│   │   ├── entities/
│   │   │   └── user/
│   │   │       └── user.py                 # User aggregate root: invariants + behaviour
│   │   ├── enums/
│   │   │   ├── operation_results.py        # Generic CreateResult, UpdateResult, DeleteResult, LoginResult
│   │   │   └── user_enum.py                # UserRole, UserStatus (StrEnum, lowercase values)
│   │   └── repositories/
│   │       └── user/
│   │           └── user_repository.py      # UserRepository Protocol (port)
│   ├── application/                        # Use cases, request/response contracts (imports Domain + Ports)
│   │   └── use_cases/                      # One concrete use case class per operation, single execute()
│   │       ├── auth/
│   │       │   ├── auth_contracts.py       # LoginRequest, RefreshTokenRequest, TokenResponse
│   │       │   ├── login_use_case.py       # LoginUseCase
│   │       │   └── refresh_token_use_case.py   # RefreshTokenUseCase
│   │       └── user/
│   │           ├── user_converter.py       # Entity ↔ contract conversion (module functions)
│   │           ├── user_contracts.py       # CreateUserRequest, UserResponse
│   │           ├── create_user_use_case.py # CreateUserUseCase
│   │           ├── get_user_use_case.py    # GetUserUseCase
│   │           ├── get_all_users_use_case.py   # GetAllUsersUseCase
│   │           ├── update_user_role_use_case.py    # UpdateUserRoleUseCase
│   │           └── delete_user_use_case.py # DeleteUserUseCase
│   ├── ports/                              # Technical service ports (Protocols) — a leaf; imports Domain enums only
│   │   ├── logger.py                       # Logger
│   │   ├── password_hasher.py              # PasswordHasher
│   │   ├── token_service.py                # TokenService + TokenClaims (the type it returns)
│   │   ├── transaction_context.py          # TransactionContext (unit of work)
│   │   └── user_context.py                 # UserContext (caller identity)
│   ├── shared/                             # Dependency-free leaf; imports only pydantic
│   │   └── contract_model.py               # ContractModel: camelCase JSON on the wire + frozen; base for contracts and envelopes
│   ├── infrastructure/                     # Adapters (imports Domain + Ports + Application)
│   │   ├── di/
│   │   │   ├── request_scope.py            # RequestScope + disposal context managers
│   │   │   └── typed_binder.py             # TypedBinder (pyrefly-checked bindings)
│   │   ├── auth/
│   │   │   ├── bcrypt_password_hasher.py   # bcrypt via passlib
│   │   │   ├── jwt_token_service.py        # PyJWT access + refresh tokens
│   │   │   └── request_user_context.py     # Request-scoped caller identity
│   │   ├── database/
│   │   │   ├── base.py                     # SQLAlchemy DeclarativeBase
│   │   │   ├── session.py                  # create_engine / create_session_factory
│   │   │   ├── sqlalchemy_transaction_context.py   # Unit-of-work adapter
│   │   │   └── models/
│   │   │       └── user_model.py           # ORM model for users table
│   │   ├── logging/
│   │   │   └── json_logger.py              # Structured JSON logger (request-scoped, bound to request_id + UserContext)
│   │   └── repositories/
│   │       └── user/
│   │           └── sqlalchemy_user_repository.py   # Async CRUD adapter
│   ├── api/                                # Routes, envelopes, composition root
│   │   ├── middleware/                     # One middleware per module; __init__.py stays empty
│   │   │   ├── request_scope_middleware.py # request_scope: opens the DI request scope (outermost)
│   │   │   ├── request_id_middleware.py    # request_id: binds X-Request-ID on the Logger, echoes it back
│   │   │   └── registration.py             # register(app): adds every middleware in order — outermost last
│   │   ├── dependencies/
│   │   │   ├── injected.py                 # Injected[T] route-side accessor
│   │   │   ├── providers.py                # composition root: AppModule (cross-cutting binds; calls each domain's register())
│   │   │   ├── bindings/<domain>.py        # per-domain register(typed_binder): repository + use-case binds
│   │   │   └── jwt_dependency.py           # JWT guard (get_current_user)
│   │   ├── routers/                        # One route module per operation (own APIRouter(), resource-relative paths);
│   │   │   ├── auth/                       # router.py (prefix="/api") aggregates via include_router(op.router, prefix="/<entity>/v1")
│   │   │   │   ├── login_route.py          # Routes take/return the contracts directly
│   │   │   │   ├── refresh_token_route.py
│   │   │   │   └── router.py               # aggregated APIRouter; __init__.py stays empty
│   │   │   └── user/
│   │   │       ├── create_user_route.py
│   │   │       ├── get_user_route.py
│   │   │       ├── get_all_users_route.py
│   │   │       ├── update_user_role_route.py
│   │   │       ├── delete_user_route.py
│   │   │       └── router.py               # aggregated APIRouter; __init__.py stays empty
│   │   ├── schemas/
│   │   │   └── operation_schema.py         # Shared response envelope
│   │   └── result_status_maps.py           # Operation result → HTTP status + message maps
│   └── main.py                             # FastAPI app, lifespan (engine), calls middleware register(app), routers
├── tests/
│   ├── domain/
│   │   └── entities/
│   │       └── user/
│   │           └── test_user.py            # Pure entity tests: invariants + behaviour (no mocks)
│   ├── api/
│   │   └── routers/
│   │       ├── auth/                       # One test module per route; conftest.py binds the mocked
│   │       │   ├── conftest.py             # use cases in a test injector module
│   │       │   ├── test_login_route.py
│   │       │   └── test_refresh_token_route.py
│   │       └── user/
│   │           ├── conftest.py
│   │           ├── test_create_user_route.py
│   │           ├── test_get_user_route.py
│   │           ├── test_get_all_users_route.py
│   │           ├── test_update_user_role_route.py
│   │           └── test_delete_user_route.py
│   ├── application/
│   │   └── use_cases/
│   │       └── user/                       # One test module per use case, via AsyncMock ports
│   │           ├── conftest.py             # Shared fakes (transaction context) + mock fixtures
│   │           ├── test_user_converter.py
│   │           ├── test_create_user_use_case.py
│   │           ├── test_get_user_use_case.py
│   │           ├── test_get_all_users_use_case.py
│   │           ├── test_update_user_role_use_case.py
│   │           └── test_delete_user_use_case.py
│   └── infrastructure/
│       ├── auth/
│       │   └── test_request_user_context.py  # Identity holder semantics + scope isolation
│       ├── database/
│       │   └── test_sqlalchemy_transaction_context.py  # Unit-of-work atomicity (in-memory SQLite)
│       └── di/
│           ├── test_request_scope.py       # Scope isolation + disposal machinery
│           └── test_typed_binder.py        # Binding facade wiring
├── alembic/                                # Database migration scripts
├── alembic.ini
├── docker-compose.yml                      # PostgreSQL 18
├── pyproject.toml
├── .env.example
└── README.md
```

## Clean Architecture + DDD Layers

### 1. Domain Layer (`src/domain/`)
- **Entities**: Aggregate roots as dataclasses with **invariants and behaviour** (`User` validates its email/username on construction and owns `activate()`/`deactivate()`/`is_active`)
- **Enums**: `UserRole` (admin/user), `UserStatus` (active/inactive), generic operation result enums
- **Repository Ports**: `typing.Protocol` interfaces with clean names (`UserRepository`) — one per aggregate root
- **Rule**: No dependencies on any other layer; business rules for one aggregate live on the entity

### 2. Ports & Shared Kernel (`src/ports/`, `src/shared/`)
- **Service Ports** (`src/ports/`): `PasswordHasher`, `TokenService`, `Logger`, `TransactionContext`, `UserContext` (Protocols) — plus any type a port returns, such as `TokenClaims` beside `TokenService`
- **Shared Kernel** (`src/shared/`): `ContractModel`, the neutral base for anything crossing the API boundary
- **Rule**: Both are **leaves** — `ports/` imports only Domain enums, `shared/` imports only pydantic. Every layer except Domain may import them, and neither may import Application

### 3. Application Layer (`src/application/`)
- **Use Cases**: One plain concrete class per operation, each with a single `execute` method (`CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`, ...) — no separate interface; each declares only the ports its operation needs, and routes and tests depend on the class directly
- **Contracts** (`<entity>_contracts.py`): Frozen Pydantic models inheriting `ContractModel`, named for their role — `<Operation>Request` for a request body (`LoginRequest`, `CreateUserRequest`; validation lives here) and `<Entity>Response` for a response body (`UserResponse`, `TokenResponse`). They *are* the HTTP bodies. A type that never crosses the wire is not suffixed and lives beside its producer (`TokenClaims`, in `src/ports/token_service.py`)
- **Converters**: Module-level functions for entity ↔ contract mapping (`to_response`, `to_response_list`, `to_entity`)
- **Rule**: Imports Domain + Ports only

### 4. Infrastructure Layer (`src/infrastructure/`)
- **DI machinery** (`di/`): the ContextVar-backed request scope and the pyrefly-checked `TypedBinder` — framework plumbing, FastAPI-agnostic
- **Database**: `session.py` builds the engine + `async_sessionmaker`; the session is provided per request (no custom factory wrapper, no shared `ContextVar`)
- **Repository Adapters**: `SqlAlchemyUserRepository` subclasses the `UserRepository` port and takes an `AsyncSession`; mutations flush and map DB errors to result enums — they never commit; the use case owns the boundary via `SqlAlchemyTransactionContext` (commit on all-success, rollback otherwise)
- **Auth/Logging Adapters**: `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger` (request-scoped bound logger — the `request_id` middleware binds a per-request `X-Request-ID` via `bind_request_id`, and it reads `user_id` from `UserContext`), `RequestUserContext` (request-scoped caller identity, populated once by the JWT guard; reads return `None` when unauthenticated)
- **Logging output**: `configure_logging()` installs the JSON handler on the **root** logger at startup, so application, uvicorn, and third-party lines share one machine-parseable format, each tagged with its source `logger`. Uvicorn's own access log is disabled in favour of the `access_log` middleware, which emits a `request.completed` entry carrying `method`, `path`, `status_code`, `duration_ms`, and the `request_id`/`user_id` correlation fields
- **Rule**: Adapters explicitly subclass their ports — the contract (and its docstrings) is defined once on the port and inherited everywhere

### 5. API Layer (`src/api/`)
- **Routes**: URLs follow `/api/<entity>/<version>/<path>` (e.g. `/api/users/v1`, `/api/auth/v1/login`). One FastAPI route module per operation, each with its own `APIRouter()` and **resource-relative paths** (`""` for the collection root, `/{id}` for item routes — neither the `/users` segment nor the version is repeated per file), depending on its use case via `use_case: Injected[CreateUserUseCase]` and **returning response models** (FastAPI serialises them to camelCase); the entity's `router.py` carries the `/api` base (plus tags and JWT guard) and aggregates the operations with `include_router(op.router, prefix="/users/v1")`, so the version is per-endpoint — bump one endpoint to `/users/v2` without touching the others (`__init__.py` stays empty)
- **Dependencies**: `providers.py` is the composition root (ports → adapters); `jwt_dependency.py` is the JWT guard
- **Bodies**: routes accept and return the application contracts directly — `ContractModel` gives camelCase JSON on the wire (and in OpenAPI) with snake_case Python attributes; only the generic operation envelopes live in `api/schemas/`
- **Rule**: Wires adapters to ports in `dependencies/`; routes never call repositories directly

## Installation

### Prerequisites
- Python 3.13+
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

### Option A: VS Code

Create `.vscode/launch.json` (the `.vscode/` directory is gitignored) with the
configuration below, then press `F5`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload"],
      "jinja": false
    }
  ]
}
```

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

### Code Formatting & Linting

Line length is 140 characters; `skip-magic-trailing-comma` is enabled so the formatter uses the full width.

```bash
uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/
```

### Type Checking
```bash
uv run pyrefly check
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

1. **Domain**: Add an aggregate root with invariants + behaviour in `src/domain/entities/<name>/` and a repository **Protocol** port in `src/domain/repositories/<name>/<name>_repository.py` (clean name, e.g. `OrderRepository`)
2. **Application**: Add `<name>_contracts.py` (`*Request` / `*Response` models on `ContractModel`), converter functions, and one concrete use case class per operation (single `execute` method) in `src/application/use_cases/<name>/` — mutating use cases inject `TransactionContext`, wrap the mutation in `begin()`, commit only on success (several repository calls in one block are atomic)
3. **Infrastructure**: Add the ORM model in `src/infrastructure/database/models/` and a `sqlalchemy_<name>_repository.py` adapter (subclasses the port, takes an `AsyncSession`) in `src/infrastructure/repositories/<name>/`
4. **API**: Add one route module per operation in `src/api/routers/<name>/`, each with its own `APIRouter()` and resource-relative paths (`""` / `/{id}`), aggregated by `router.py` (`prefix="/api"`, tags, guard) via `include_router(op.router, prefix="/<name>/v1")` — giving `/api/<name>/v1/...` with the version per-endpoint; routes depend on their use case and accept/return the contracts directly (`response_model=<Entity>Response`) — no per-entity schemas or converters
5. **Bindings**: Add a `src/api/dependencies/bindings/<name>.py` with a `register(typed_binder)` that binds the domain's repository and use cases (transient), and call it from `AppModule.configure()` (which keeps the cross-cutting binds). Constructors are auto-wired via `@inject`; a wrong implementation is a pyrefly error:
   ```python
   # src/api/dependencies/bindings/order.py
   def register(typed_binder: TypedBinder) -> None:
       typed_binder.bind_typed(OrderRepository).to(SqlAlchemyOrderRepository)  # transient
       typed_binder.bind_self_typed(CreateOrderUseCase)                        # one line per operation use case
   ```
6. **Main**: Include the new router in `src/main.py`
7. **Migration**: Generate and apply an Alembic migration for any new DB models
8. **Tests**: Entity tests in `tests/domain/`, use case tests with mocked ports, route tests binding a mock use case instance in a `TestModule`

## Design Principles

1. **Dependency Inversion**: Use cases depend on `Protocol` ports, not concrete adapters
2. **Rich Domain**: Aggregate roots enforce invariants and own their state transitions — use cases orchestrate, they don't implement domain rules
3. **Single Responsibility**: One use case per operation; one CRUD operation per repository method
4. **Open/Closed**: Swap an adapter by changing one binding line in the composition root
5. **Interface Segregation**: Small, focused ports (Protocols) per collaborator
6. **Single-Source Documentation**: Contracts are documented once on the port; implementations inherit the docstrings via explicit subclassing
7. **Async/Await**: Full async support for all database and I/O operations

## License

MIT License
