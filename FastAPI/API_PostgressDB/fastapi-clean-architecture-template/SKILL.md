---
name: fastapi-clean-architecture-template
description: Scaffold a new project following Clean Architecture + DDD principles on FastAPI — strict 4-layer structure (Domain, Application, Infrastructure, API) with unidirectional dependencies, rich domain entities with invariants and behaviour, ports as typing.Protocol, the repository pattern, result-enum error handling, and typed declarative dependency injection (injector + TypedBinder: one binding per line with explicit scopes, conformance checked by pyrefly). Supports PostgreSQL, MongoDB, SQLite; JWT, OAuth2, API key auth; optional Redis cache.
argument-hint: "<project-name> [--db postgres|mongodb|sqlite] [--auth jwt|oauth2|apikey] [--cache none|redis] [--no-docker]"
disable-model-invocation: true
metadata:
  version: "3.0.0"
---

# FastAPI Clean Architecture — Scaffold Skill

Generates a production-ready project with Clean Architecture + DDD enforced across all 4 layers. The tech stack (database, auth, cache) is configurable; the architecture is not — layer boundaries, naming rules, documentation policy, and DI patterns are always applied.

For auditing an existing project use `/fastapi-clean-architecture-review`. To activate rules in an existing session use `/fastapi-clean-architecture-mode`.

## Tech stack flags

| Flag | Values | Default |
|------|--------|---------|
| `--db` | `postgres`, `mongodb`, `sqlite` | `postgres` |
| `--auth` | `jwt`, `oauth2`, `apikey` | `jwt` |
| `--cache` | `none`, `redis` | `none` |
| `--no-docker` | flag | docker enabled |

---

## Cross-cutting rules (apply to every generated file)

- **No module docstrings or top-of-file comments.** The contract is documented once, on the Protocol port with **concise** docstrings — a one-line summary plus `Args`/`Returns`/`Raises` only, never implementation details, rationale, or usage examples; implementations explicitly subclass their port and inherit the docs. Implementation classes get a short mechanism-note class docstring only; no `__init__` docstrings.
- **Rich domain**: entities enforce invariants in `__post_init__` (raise `ValueError`) and expose behaviour (`activate()`, `is_active`) — never anemic field bags.
- **Use cases are plain concrete classes, one per operation** with a single `execute` method (`Create<Entity>UseCase`) — no separate interface; each declares only the ports its operation needs and carries its own method docstrings.
- Line length 140 with `skip-magic-trailing-comma = true`.

## Workflow

Make a todo list and work through each step sequentially.

### Step 1 — Resolve tech stack

Parse all flags. Apply defaults for any flag not provided.

### Step 2 — Create directory structure

```
<project-name>/
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config/settings.py
│   ├── domain/
│   │   ├── entities/              # aggregate roots: invariants + behaviour
│   │   ├── enums/operation_results.py
│   │   └── repositories/          # Protocol ports, one per aggregate root
│   ├── application/
│   │   ├── services/              # Protocol ports
│   │   └── use_cases/             # <operation>_use_case.py (one concrete class per operation)
│   ├── infrastructure/
│   │   ├── di/                    # request_scope.py, typed_binder.py (injector extensions)
│   │   ├── auth/
│   │   ├── database/
│   │   │   └── models/__init__.py
│   │   └── repositories/
│   └── api/
│       ├── dependencies/          # injected.py, providers.py (AppModule), guards
│       ├── routers/
│       └── schemas/operation_schema.py
├── tests/
│   ├── domain/                    # pure entity tests (no mocks)
│   ├── application/use_cases/
│   ├── api/routers/
│   └── infrastructure/di/
├── pyproject.toml
├── .env.example
├── CLAUDE.md
└── AGENT.md
```

There is **no `container.py`** — the composition root is `src/api/dependencies/providers.py`. Add `alembic/` + `alembic.ini` for `postgres` or `sqlite`. Add `Dockerfile` + `docker-compose.yml` unless `--no-docker`.

### Step 3 — Generate shared files

Generate these regardless of stack. Use concise, idiomatic Python — no unnecessary comments.

- **`operation_results.py`**: Three `StrEnum` classes — `CreateResult`, `UpdateResult`, `DeleteResult`. Values: `success`, `failure`, `concurrency_error`, `unique_constraint_error` on all three; add `not_found` to `UpdateResult` and `DeleteResult`.
- **`src/application/dto_base.py`**: Pydantic `BaseModel` subclass `DTOBase` with `alias_generator=to_camel`, `populate_by_name=True`, `frozen=True`. Every DTO inherits it and doubles as the API request/response body — do NOT generate per-entity `Request`/`Response` schemas or API converters.
- **`operation_schema.py`**: Three `DTOBase` subclasses — `CreateOperationResponse(result, message, id: int | None)`, `UpdateOperationResponse(result, message)`, `DeleteOperationResponse(result, message)`.
- **`result_status_maps.py`**: `*_STATUS_MAP` and `*_MESSAGE_MAP` dicts mapping each result enum to its HTTP status (201 success-create, 200 success-update/delete, 404 not-found, 409 conflict, 500 failure) and message. Routes look these up, set `response.status_code`, and return the response model — never hand-build a `JSONResponse`.

### Step 4 — Generate domain + database layer

Every entity is an aggregate root: a dataclass whose `__post_init__` enforces its invariants (raise `ValueError`) and which exposes intention-revealing behaviour. One repository `Protocol` port per aggregate root in `src/domain/repositories/`.

#### `postgres` or `sqlite`

- **`base.py`**: SQLAlchemy `DeclarativeBase` subclass.
- **`session.py`** (infrastructure): `create_engine(settings) -> AsyncEngine` and `create_session_factory(engine) -> async_sessionmaker[AsyncSession]` (with `expire_on_commit=False`). No connection-factory object, no `ContextVar`.

The engine + session factory are singleton `@provider` methods on `AppModule` (the engine disposed in `lifespan` shutdown); the session is a request-scoped `@provider`. Repository adapters explicitly subclass their port, receive the `AsyncSession` by constructor injection, and never commit or roll back — mutations `flush()` and map errors to result enums. Driver: `asyncpg` for postgres (`postgresql+asyncpg://`), `aiosqlite` for sqlite (`sqlite+aiosqlite:///`).

Also generate the unit-of-work pair:

- **`transaction_context.py`** (application services): `Transaction` and `TransactionContext` Protocols — `begin()` returns an async context manager yielding a `Transaction` with `commit()`; rollback-unless-committed semantics.
- **`sqlalchemy_transaction_context.py`** (infrastructure/database): adapter over the request-scoped session.

Mutating use cases inject `TransactionContext`, wrap repository calls in `async with ...begin() as transaction:`, and call `await transaction.commit()` only when every operation succeeded. Calls spanning several repositories inside one block are atomic — they share the request session.

#### `mongodb`

- **`mongo_client.py`** (infrastructure): wraps `motor.motor_asyncio.AsyncIOMotorClient`, created in `lifespan` and stored on `app.state`. A `get_database` dependency provides it. No session or transaction manager needed.

No Alembic for MongoDB.

### Step 5 — Generate auth layer

Ports are `typing.Protocol`s in `src/application/services/`; adapters are mechanism-qualified classes in `src/infrastructure/` that subclass their port.

#### `jwt`

- `PasswordHasher` port / `BcryptPasswordHasher` adapter — bcrypt via passlib.
- `TokenService` port / `JwtTokenService` adapter — PyJWT; issues access + refresh JWTs from settings.
- `Logger` port / `JsonLogger` adapter — request-scoped bound logger; the `request_context` middleware (`src/api/middleware.py`) mints (or accepts an inbound `X-Request-ID`) and calls `bind_request_id` once (raises on a second call), echoing it back as the `X-Request-ID` response header, and `user_id` is read from the request-scoped `UserContext`. Log emission never raises when the id is unbound (the field is simply omitted). `configure_logging()` sets up the process-wide handler once at startup.
- `UserContext` port / `RequestUserContext` adapter — request-scoped holder of the caller's identity; `populate()` once by the guard (second call raises), unpopulated reads raise. Inject into use cases needing the caller (auditing, roles/permissions).
- `jwt_dependency.py` — `get_current_user` decodes the JWT, populates `UserContext`, returns `TokenClaimsDTO`. Protect routers with `dependencies=[Depends(get_current_user)]`.
- Auth use cases (one per operation: login, refresh) + DTOs + per-operation route modules under `src/application/use_cases/auth/` and `src/api/routers/auth/`.

#### `oauth2`

- `OAuthService` port / adapter — exchanges provider token via `httpx`.
- Keep the JWT guard for internal session tokens issued after OAuth exchange. No `PasswordHasher`.

#### `apikey`

- `APIKeyService` port / adapter — validates key against DB.
- Guard in `src/api/dependencies/api_key_dependency.py`.

### Step 6 — Generate cache layer (redis only)

- `CacheService` port (application layer): `get()`, `set()`, `delete()`.
- `RedisCacheService` adapter (infrastructure): `redis.asyncio` client created in `lifespan`, disposed on shutdown.
- Bind it with `bind_typed(CacheService).to(RedisCacheService, scope=singleton)` in `AppModule`; dispose the client in `lifespan` shutdown alongside the engine.

### Step 7 — Generate `settings.py`

`pydantic-settings` `BaseSettings` plus an `@lru_cache def get_settings() -> Settings`. Include only fields for the resolved stack:

- Always: `APP_NAME`, `DEBUG`
- postgres/sqlite: `DATABASE_URL`, `IS_SQL_ECHO_ENABLED: bool = False`
- mongodb: `MONGODB_URL`, `MONGODB_DB_NAME`
- jwt/oauth2: `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES = 30`, `REFRESH_TOKEN_EXPIRE_DAYS = 7`
- redis: `REDIS_URL`

### Step 8 — Generate `main.py`

- `injector = Injector([AppModule()])` at module level; `app.state.injector = injector`.
- `lifespan`: dispose the engine on shutdown (`await app.state.injector.get(AsyncEngine).dispose()`).
- `FastAPI(lifespan=lifespan)` (lifespan calls `configure_logging(settings)` at startup and disposes the engine at shutdown); register the `request_context` middleware (from `src/api/middleware.py`), which enters `async_request_scope()` per request, binds the `X-Request-ID` on the `Logger`, and echoes it back as the response header.
- `app.include_router(...)` for each router.

Copy `request_scope.py` and `typed_binder.py` verbatim from `FastAPI/API_PostgressDB/src/infrastructure/di/` into the new project's `src/infrastructure/di/`, `injected.py` from `FastAPI/API_PostgressDB/src/api/dependencies/`, and `middleware.py` from `FastAPI/API_PostgressDB/src/api/`.

### Step 9 — Generate the use cases and composition root

For each entity generate a concrete use case class with concise contract docstrings on its methods (no port — it is the single source).

`AppModule` in `src/api/dependencies/providers.py` is the composition root — one declarative line per binding via `TypedBinder`, constructors auto-wired via `@inject`:
- Stateless singletons (`PasswordHasher`, `TokenService`, cache): `typed_binder.bind_typed(PasswordHasher).to(BcryptPasswordHasher, scope=singleton)`. The bound `Logger` is request-scoped (`bind_typed(Logger).to(JsonLogger, scope=request)`).
- Engine, session factory: singleton `@provider` methods; the session: a request-scoped `@provider` method (disposed via `aclose()` by the scope teardown).
- `bind_typed(TransactionContext).to(SqlAlchemyTransactionContext, scope=request)` (cross-cutting, in `AppModule`). Repositories are **transient** (`bind_typed(<Entity>Repository).to(Sqlalchemy<Entity>Repository)`) but still receive the one request-scoped session, so they and the transaction context share one transaction.
- Per-domain binds live in `src/api/dependencies/bindings/<domain>.py` as `register(typed_binder)`, called from `AppModule.configure()`: the repository (transient) and one `bind_self_typed(<Operation>UseCase)` per operation (transient). Each route depends on its use case via `Annotated[<Operation>UseCase, Injected(<Operation>UseCase)]`.
- Add `@inject` to every implementation whose `__init__` takes dependencies.

### Step 10 — Generate `pyproject.toml`

Base dependencies: `fastapi>=0.115`, `injector>=0.22`, `pydantic>=2.0`, `pydantic-settings>=2.0`, `uvicorn[standard]>=0.30`. (No `fastapi-injector`, no `dishka` — the request scope and typed binder are in-house.)

Stack additions:

| Stack | Extra |
|-------|-------|
| postgres | `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`, `alembic>=1.13` |
| sqlite | `sqlalchemy[asyncio]>=2.0`, `aiosqlite>=0.20`, `alembic>=1.13` |
| mongodb | `motor>=3.4` |
| jwt | `PyJWT>=2.10`, `passlib[bcrypt]>=1.7` |
| oauth2 | `httpx>=0.27`, `PyJWT>=2.10` |
| redis | `redis[asyncio]>=5.0` |

Dev: `pytest>=8.0`, `pytest-asyncio>=0.23`, `httpx>=0.27`, `ruff>=0.4`, `pyrefly>=1.1.0`.

`[tool.ruff]` with `line-length = 140`, `[tool.ruff.format]` with `skip-magic-trailing-comma = true`, `[tool.ruff.lint.isort]` with `split-on-trailing-comma = false`. `[tool.pyrefly]` with `python-version` matching the target Python, `project-includes = ["src/**", "tests/**"]`, `preset = "legacy"` (pyrefly's own recommended preset for mypy-equivalent strictness — no plugin needed for Pydantic models, and no suppression required for passing Protocol classes as `type[P]` to `TypedBinder`). `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`.

### Step 11 — Copy architecture docs

Copy `CLAUDE.md` and `AGENT.md` verbatim from `FastAPI/API_PostgressDB/` into the new project root.

### Step 12 — Generate `.env.example`

Only variables for the resolved stack with placeholder values. No real secrets.

### Step 13 — Generate tests

- `tests/domain/`: pure entity tests — invariants and behaviour, no mocks.
- `tests/application/use_cases/`: use case tests with `AsyncMock(spec=<Entity>Repository)` and a fake `TransactionContext`.
- `tests/api/routers/`: one test module per route, binding `AsyncMock(spec=<Operation>UseCase)` instances in a `TestModule`.

### Step 14 — Validate

```bash
uv run ruff check src/ --fix && uv run ruff format src/ && uv run pyrefly check
```

### Step 15 — Summary

Report: project name and path, resolved stack, file count by layer, ruff and pyrefly results, and next steps (install deps, copy `.env`, run migrations if applicable, start with `uvicorn src.main:app --reload`).
