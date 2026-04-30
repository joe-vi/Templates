---
name: fastapi-template
description: Scaffold a new FastAPI Clean Architecture project or audit an existing one for architecture compliance. Supports PostgreSQL, MongoDB, and SQLite; JWT, OAuth2, and API key auth; optional Redis cache.
argument-hint: "scaffold <project-name> [--db postgres|mongodb|sqlite] [--auth jwt|oauth2|apikey] [--cache none|redis] [--no-docker] | review [--fix]"
when_to_use: When starting a new FastAPI service from scratch, or when auditing an existing FastAPI project for clean architecture violations.
version: "1.0.0"
---

# FastAPI Clean Architecture Skill

## Arguments

- `scaffold <project-name> [options]` — generate a new project (see Scaffold Workflow)
- `review [--fix]` — audit the current project for architecture violations (see Review Workflow)

### Scaffold options

| Flag | Values | Default | Effect |
|------|--------|---------|--------|
| `--db` | `postgres`, `mongodb`, `sqlite` | `postgres` | Database + ORM layer |
| `--auth` | `jwt`, `oauth2`, `apikey` | `jwt` | Authentication strategy |
| `--cache` | `none`, `redis` | `none` | Cache layer |
| `--no-docker` | — | docker on | Skip Dockerfile + docker-compose |

---

## Architecture Rules (applies to both modes)

Dependencies flow **inward only**: API → Infrastructure → Application → Domain.

| Layer | Location | Contains | Imports from |
|-------|----------|----------|--------------|
| Domain | `src/domain/` | Entities, Repository ABCs, result enums | Nothing |
| Application | `src/application/` | Use cases, DTOs, converters, service ABCs | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, repository impls, auth impls | Domain + Application |
| API | `src/api/` | Routes, schemas, API converters | Application (ABCs only) |
| DI Container | `src/container.py` | `Binder.bind()` wiring | All layers |

### Naming

- ABCs **must** end with `Base`: `UserRepositoryBase`, `UserUseCaseBase`
- DTOs: frozen dataclasses, `DTO` suffix. Return `list[UserDTO]` directly — no wrapper DTO
- API schemas: `Request` (input) / `Response` (output) suffix; all inherit `APIModelBase`
- Enums: `StrEnum`, lowercase values; all in `src/domain/enums/`
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult` — never entity-specific
- Booleans read as questions: `is_active`, `has_items` — never bare nouns
- No abbreviations: `repository` not `repo`, `connection` not `conn`
- No single-letter names, no numbered variants (`greeting1`), no vague names (`dto`, `result`)

### Dependency Injection (`fastapi-injector`)

- Every injectable `__init__` **must** have `@inject` from `injector` — omitting causes `TypeError` at startup
- In `main.py`: add `InjectorMiddleware` **before** `attach_injector()`, then include routers after `attach_injector()`
- Routes use `Injected(BaseClass)` for use cases/services — **never** `Depends()` for these
- `Depends()` only in `src/api/dependencies/` for cross-cutting guards and `dependencies=[...]` on `APIRouter`
- `singleton` scope only for `ConnectionFactory` and external service clients — never for repos or use cases

### Repository Pattern

- One CRUD operation per method — no combined read+write
- Mutation methods catch all DB exceptions internally and return result enums — nothing propagates to use cases
- Exception mapping: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`; `DeadlockDetectedError` → `CONCURRENCY_ERROR`; all others → `FAILURE`
- Repos inject `ConnectionFactoryBase`; each method opens its own session with `async with self._connection_factory.get_session()`
- Never pass sessions to repository constructors

### Database (PostgreSQL / SQLite)

- `id`, `created_at`, `updated_at` are DB-generated — never set in Python
- Call `session.refresh()` after every insert/update
- All constraints need an explicit `name`: `uq_{table}_{col}`, `fk_{table}_{col}`, `ck_{table}_{desc}`, `ix_{table}_{col}`
- Declare constraints in `__table_args__`, not as column-level shorthand (except primary key)

### Testing

- Use case tests: `AsyncMock(spec=RepositoryBase)` to mock the repo; annotate fixture as `-> RepositoryBase`
- Route tests: minimal `FastAPI()` + `TestModule` — never import `src/main.py` or `src/container.py`
- `asyncio_mode = "auto"` is configured — no `@pytest.mark.asyncio` needed
- Never test infrastructure repositories in unit tests (requires live DB)

---

## Scaffold Workflow

Make a todo list and work through each step sequentially.

### Step 1 — Resolve tech stack

Parse all flags from the arguments. Use these defaults if a flag is absent:
- `--db` → `postgres`
- `--auth` → `jwt`
- `--cache` → `none`
- docker → enabled unless `--no-docker` is present

### Step 2 — Create directory structure

```
<project-name>/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── container.py
│   ├── config/
│   │   └── settings.py
│   ├── domain/
│   │   ├── entities/
│   │   ├── enums/
│   │   │   └── operation_results.py
│   │   └── repositories/
│   ├── application/
│   │   ├── services/
│   │   │   ├── transaction_manager_base.py   # postgres/sqlite only
│   │   │   └── user_context_base.py          # jwt/oauth2 only
│   │   └── use_cases/
│   │       └── auth/                          # jwt/oauth2 only
│   ├── infrastructure/
│   │   ├── auth/                              # jwt/oauth2/apikey
│   │   ├── database/
│   │   │   └── models/
│   │   │       └── __init__.py
│   │   └── repositories/
│   └── api/
│       ├── dependencies/
│       ├── routers/
│       └── schemas/
│           ├── base_schema.py
│           └── operation_schema.py
├── tests/
│   ├── application/
│   │   └── use_cases/
│   └── api/
│       └── routers/
├── pyproject.toml
├── .env.example
├── CLAUDE.md
└── AGENT.md
```

Add `alembic/` + `alembic.ini` for `--db postgres` and `--db sqlite`.
Add `Dockerfile` + `docker-compose.yml` unless `--no-docker`.

### Step 3 — Generate shared infrastructure files

Generate these files identically regardless of tech stack:

**`src/domain/enums/operation_results.py`**
```python
"""Shared operation result enums."""

from enum import StrEnum


class CreateResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"


class UpdateResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    UNIQUE_CONSTRAINT_ERROR = "unique_constraint_error"
    NOT_FOUND = "not_found"


class DeleteResult(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    CONCURRENCY_ERROR = "concurrency_error"
    NOT_FOUND = "not_found"
```

**`src/api/schemas/base_schema.py`**
```python
"""Base Pydantic schema for all API models."""

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class APIModelBase(BaseModel):
    """Base for all API request/response schemas — camelCase JSON serialisation."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
```

**`src/api/schemas/operation_schema.py`**
```python
"""Shared operation response schemas."""

from src.api.schemas.base_schema import APIModelBase


class CreateOperationResponse(APIModelBase):
    """Response envelope for create operations."""

    id: int | None


class UpdateOperationResponse(APIModelBase):
    """Response envelope for update operations."""

    message: str


class DeleteOperationResponse(APIModelBase):
    """Response envelope for delete operations."""

    message: str
```

**`src/api/result_status_maps.py`**
```python
"""Helpers mapping operation results to HTTP responses."""

from fastapi import Response
from fastapi.responses import JSONResponse

from src.domain.enums.operation_results import CreateResult, DeleteResult, UpdateResult


def create_response(result: CreateResult, entity_id: int | None) -> Response:
    """Return a JSONResponse with the correct HTTP status for a create operation."""
    status_map = {
        CreateResult.SUCCESS: 201,
        CreateResult.UNIQUE_CONSTRAINT_ERROR: 409,
        CreateResult.CONCURRENCY_ERROR: 409,
        CreateResult.FAILURE: 500,
    }
    return JSONResponse(
        content={"id": entity_id},
        status_code=status_map[result],
    )


def update_response(result: UpdateResult) -> Response:
    """Return a JSONResponse with the correct HTTP status for an update operation."""
    status_map = {
        UpdateResult.SUCCESS: 200,
        UpdateResult.NOT_FOUND: 404,
        UpdateResult.UNIQUE_CONSTRAINT_ERROR: 409,
        UpdateResult.CONCURRENCY_ERROR: 409,
        UpdateResult.FAILURE: 500,
    }
    return JSONResponse(
        content={"message": result.value},
        status_code=status_map[result],
    )


def delete_response(result: DeleteResult) -> Response:
    """Return a JSONResponse with the correct HTTP status for a delete operation."""
    status_map = {
        DeleteResult.SUCCESS: 200,
        DeleteResult.NOT_FOUND: 404,
        DeleteResult.CONCURRENCY_ERROR: 409,
        DeleteResult.FAILURE: 500,
    }
    return JSONResponse(
        content={"message": result.value},
        status_code=status_map[result],
    )
```

### Step 4 — Generate database layer (varies by --db)

#### `--db postgres` or `--db sqlite`

Generate `src/infrastructure/database/base.py`, `connection_factory_base.py`, `connection_factory.py`, and `transaction_manager.py` following the SQLAlchemy 2.0 async session pattern:

- `ConnectionFactoryBase` (application layer): abstract `get_session()` and `close()`
- `ConnectionFactory` (infrastructure): creates `AsyncEngine` + `async_sessionmaker`; `get_session()` yields `AsyncSession`; checks `_active_session` ContextVar before opening a new session
- `TransactionManagerBase` (application layer): abstract `begin_transaction()` async context manager
- `TransactionManager` (infrastructure): injects `ConnectionFactoryBase`; sets `_active_session` ContextVar inside `begin_transaction()`

For `--db postgres`: use `asyncpg` driver (`postgresql+asyncpg://`)
For `--db sqlite`: use `aiosqlite` driver (`sqlite+aiosqlite:///`)

#### `--db mongodb`

Generate `src/infrastructure/database/mongo_client_base.py` (application layer ABC) and `src/infrastructure/database/mongo_client.py` using `motor.motor_asyncio.AsyncIOMotorClient`.

No Alembic, no session pattern. Repository methods use `self._client.get_database().get_collection()`.

Exception mapping for MongoDB:
- `DuplicateKeyError` → `UNIQUE_CONSTRAINT_ERROR`
- All others → `FAILURE`

### Step 5 — Generate auth layer (varies by --auth)

#### `--auth jwt`

Generate (application layer ABCs + infrastructure implementations):
- `PasswordHasherBase` / `PasswordHasher` (bcrypt)
- `TokenServiceBase` / `TokenService` (python-jose; issues access + refresh JWT)
- `UserContextBase` / `UserContext` (request-scoped; `populate()` raises on second call)
- `JWTDependency` guard in `src/api/dependencies/jwt_dependency.py`
- Auth use case + DTO in `src/application/use_cases/auth/`
- Auth router in `src/api/routers/auth/`

#### `--auth oauth2`

Generate an `OAuthServiceBase` / `OAuthService` that exchanges provider tokens. No password hasher needed. Keep `UserContextBase` / `UserContext` and JWT guard for internal session tokens issued after OAuth exchange.

#### `--auth apikey`

Generate an `APIKeyServiceBase` / `APIKeyService` that validates keys against the DB. Guard lives in `src/api/dependencies/api_key_dependency.py`. No `UserContextBase` unless user identity is needed.

### Step 6 — Generate cache layer (only if --cache redis)

Generate:
- `CacheServiceBase` in `src/application/services/cache_service_base.py` with abstract `get()`, `set()`, `delete()`
- `RedisService` in `src/infrastructure/cache/redis_service.py` using `redis.asyncio`
- Bind in `container.py` as singleton
- Add `close()` to `RedisService` and call in `lifespan` shutdown

### Step 7 — Generate `src/config/settings.py`

Use `pydantic-settings` (`BaseSettings`). Include only the fields needed for the resolved stack:

```python
# Always present
APP_NAME: str = "<project-name>"
DEBUG: bool = False

# --db postgres / sqlite
DATABASE_URL: str

# --db mongodb
MONGODB_URL: str
MONGODB_DB_NAME: str

# --auth jwt / oauth2
SECRET_KEY: str
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# --cache redis
REDIS_URL: str

# debugging
IS_SQL_ECHO_ENABLED: bool = False   # postgres/sqlite only
```

### Step 8 — Generate `src/main.py`

```python
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_injector import attach_injector, InjectorMiddleware
from injector import Injector

from src.container import AppModule


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of singleton resources."""
    yield
    # close connection factory (and redis if present)
    injector.get(ConnectionFactoryBase).close()  # adapt to resolved stack


injector = Injector([AppModule()])

app = FastAPI(lifespan=lifespan)

app.add_middleware(InjectorMiddleware, injector=injector)  # BEFORE attach_injector
attach_injector(app, injector)

# include routers AFTER attach_injector
app.include_router(...)
```

Adapt the lifespan block to close whichever singletons exist in the resolved stack.

### Step 9 — Generate `src/container.py`

```python
"""Dependency injection bindings."""

from injector import Module, Binder, singleton

# import all base classes and implementations for the resolved stack


class AppModule(Module):
    """Wires all base classes to their concrete implementations."""

    def configure(self, binder: Binder) -> None:
        """Bind all base/implementation pairs."""
        binder.bind(ConnectionFactoryBase, to=ConnectionFactory, scope=singleton)
        # add remaining bindings for auth, cache, use cases, repos
```

### Step 10 — Generate `pyproject.toml`

Use these base dependencies, then add stack-specific ones:

```toml
[project]
name = "<project-name>"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "fastapi-injector>=0.6",
    "injector>=0.22",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "uvicorn[standard]>=0.30",
]

[tool.ruff]
line-length = 80
```

Stack-specific additions:

| Stack | Extra dependencies |
|---|---|
| `--db postgres` | `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`, `alembic>=1.13` |
| `--db sqlite` | `sqlalchemy[asyncio]>=2.0`, `aiosqlite>=0.20`, `alembic>=1.13` |
| `--db mongodb` | `motor>=3.4`, `beanie>=1.25` (optional ODM) |
| `--auth jwt` | `python-jose[cryptography]>=3.3`, `bcrypt>=4.0`, `passlib[bcrypt]>=1.7` |
| `--auth oauth2` | `httpx>=0.27`, `python-jose[cryptography]>=3.3` |
| `--cache redis` | `redis[asyncio]>=5.0` |

Dev dependencies (always):
```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "httpx>=0.27",
    "ruff>=0.4",
]
```

### Step 11 — Copy architecture docs

Copy `CLAUDE.md` and `AGENT.md` verbatim from `FastAPI/API_PostgressDB/` into the new project root. These files ensure future Claude sessions in the new project follow the same rules.

### Step 12 — Generate `.env.example`

Include only variables relevant to the resolved stack with placeholder values. Never include real secrets.

### Step 13 — Validate

Run:
```bash
uv run ruff check src/ --fix && uv run ruff format src/
```

If `uv` is not available, note it in the summary and skip.

### Step 14 — Summary

Report:
- Project name and location
- Tech stack resolved (db, auth, cache, docker)
- Files created (count by layer)
- Ruff result
- Next steps (install deps, copy `.env.example` to `.env`, run migrations if applicable, start with `uvicorn src.main:app --reload`)

---

## Review Workflow

Make a todo list. Audit the project in the current working directory against every rule below. Report all violations as a table with `file:line`, rule violated, and a fix description. If `--fix` is passed, apply fixes automatically after reporting.

### Check 1 — Import direction

Scan all `import` statements. Flag any:
- `src/domain/` importing from `src/application/`, `src/infrastructure/`, or `src/api/`
- `src/application/` importing from `src/infrastructure/` or `src/api/`
- `src/api/` importing from `src/infrastructure/`

### Check 2 — Naming conventions

- ABCs not ending with `Base`
- DTOs not ending with `DTO` or defined as non-frozen dataclass
- API schemas not ending with `Request` or `Response`
- API schemas not inheriting from `APIModelBase`
- Boolean fields/variables not prefixed with `is_`, `has_`, or `can_`
- Abbreviations: `repo`, `conn`, `svc`, `mgr`, `cfg`
- Entity-specific result enums (e.g., `CreateUserResult`)
- Wrapper collection DTOs (e.g., `UserListDTO`)

### Check 3 — Dependency injection

- Injectable `__init__` missing `@inject`
- `Depends()` used for use case or service injection in route signatures (outside `src/api/dependencies/`)
- `InjectorMiddleware` added after `attach_injector()` in `main.py`
- `attach_injector()` called before adding `InjectorMiddleware`
- Routers included before `attach_injector()`
- `singleton` scope on repositories or use cases

### Check 4 — Repository pattern

- Repository method performs more than one CRUD operation
- Mutation method propagates DB exceptions (raises instead of returning result enum)
- Repository method accepts a session parameter
- Use case directly calls a repository without going through a use case method
- Route bypasses the use case and calls a repository directly

### Check 5 — Database constraints (SQLAlchemy only)

- `UniqueConstraint`, `ForeignKeyConstraint`, `CheckConstraint`, or `Index` missing an explicit `name`
- Constraint names not following the `uq_`, `fk_`, `ck_`, `ix_` prefix conventions
- `id`, `created_at`, or `updated_at` set in Python code
- Missing `session.refresh()` after insert/update

### Check 6 — Enums

- Enums not using `StrEnum`
- Enum values not lowercase
- Enums defined outside `src/domain/enums/`
- `SQLAlchemyEnum` type object defined inline rather than at module level

### Check 7 — Authentication guards

- Guard functions defined inside route files instead of `src/api/dependencies/`
- `Depends(get_current_user)` scattered in individual route function signatures instead of on `APIRouter`

### Check 8 — Code style

- Lines exceeding 80 characters (excluding `# noqa: E501`)
- Use of `List[X]`, `Optional[X]`, `Dict[K, V]` instead of modern `list[X]`, `X | None`, `dict[K, V]`
- Synchronous DB operations (missing `async def` / `await`)

### Check 9 — Documentation

- `.py` files missing module-level docstring
- Classes missing class-level docstring
- `__init__` missing docstring
- Public abstract methods on ABCs missing Google-style docstring

### Final report format

```
## Architecture Review — <project-name>

### Violations found: <N>

| # | File | Line | Rule | Fix |
|---|------|------|------|-----|
| 1 | src/domain/entities/user.py | 3 | Domain imports from Infrastructure | Remove import of `UserRepository` |
...

### Passed checks
- Import direction: ✅
- Naming conventions: ✅
...
```

If `--fix` was passed, list the changes made after the table.
