---
name: fastapi-clean-architecture-template
description: Scaffold a new project following Clean Architecture principles on FastAPI — strict 4-layer structure (Domain, Application, Infrastructure, API) with unidirectional dependencies, ports as typing.Protocol, the repository pattern, result-enum error handling, and typed declarative dependency injection (injector + TypedBinder: one binding per line with explicit singleton/request scopes, conformance checked by mypy). Supports PostgreSQL, MongoDB, SQLite; JWT, OAuth2, API key auth; optional Redis cache.
argument-hint: "<project-name> [--db postgres|mongodb|sqlite] [--auth jwt|oauth2|apikey] [--cache none|redis] [--no-docker]"
disable-model-invocation: true
metadata:
  version: "2.0.0"
---

# FastAPI Clean Architecture — Scaffold Skill

Generates a production-ready project with Clean Architecture enforced across all 4 layers. The tech stack (database, auth, cache) is configurable; the architecture is not — layer boundaries, naming rules, and DI patterns are always applied.

For auditing an existing project use `/fastapi-clean-architecture-review`. To activate rules in an existing session use `/fastapi-clean-architecture-mode`.

## Tech stack flags

| Flag | Values | Default |
|------|--------|---------|
| `--db` | `postgres`, `mongodb`, `sqlite` | `postgres` |
| `--auth` | `jwt`, `oauth2`, `apikey` | `jwt` |
| `--cache` | `none`, `redis` | `none` |
| `--no-docker` | flag | docker enabled |

---

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
│   │   ├── entities/
│   │   ├── enums/operation_results.py
│   │   └── repositories/
│   ├── application/
│   │   ├── services/          # Protocol ports
│   │   └── use_cases/
│   ├── infrastructure/
│   │   ├── auth/
│   │   ├── database/
│   │   │   └── models/__init__.py
│   │   └── repositories/
│   └── api/
│       ├── dependencies/      # injection.py (scope + TypedBinder), providers.py (AppModule), guards
│       ├── routers/
│       └── schemas/
│           ├── base_schema.py
│           └── operation_schema.py
├── tests/
│   ├── application/use_cases/
│   └── api/routers/
├── pyproject.toml
├── .env.example
├── CLAUDE.md
└── AGENT.md
```

There is **no `container.py`** — the composition root is `src/api/dependencies/providers.py`. Add `alembic/` + `alembic.ini` for `postgres` or `sqlite`. Add `Dockerfile` + `docker-compose.yml` unless `--no-docker`.

### Step 3 — Generate shared files

Generate these regardless of stack. Use concise, idiomatic Python — no unnecessary comments.

- **`operation_results.py`**: Three `StrEnum` classes — `CreateResult`, `UpdateResult`, `DeleteResult`. Values: `success`, `failure`, `concurrency_error`, `unique_constraint_error` on all three; add `not_found` to `UpdateResult` and `DeleteResult`.
- **`base_schema.py`**: Pydantic `BaseModel` subclass `APIModelBase` with `alias_generator=to_camel` and `populate_by_name=True`.
- **`operation_schema.py`**: Three `APIModelBase` subclasses — `CreateOperationResponse(result, message, id: int | None)`, `UpdateOperationResponse(result, message)`, `DeleteOperationResponse(result, message)`.
- **`result_status_maps.py`**: `*_STATUS_MAP` and `*_MESSAGE_MAP` dicts mapping each result enum to its HTTP status (201 success-create, 200 success-update/delete, 404 not-found, 409 conflict, 500 failure) and message. Routes look these up, set `response.status_code`, and return the response model — never hand-build a `JSONResponse`.

### Step 4 — Generate database layer

#### `postgres` or `sqlite`

- **`base.py`**: SQLAlchemy `DeclarativeBase` subclass.
- **`session.py`** (infrastructure): `create_engine(settings) -> AsyncEngine` and `create_session_factory(engine) -> async_sessionmaker[AsyncSession]` (with `expire_on_commit=False`). No connection-factory object, no `ContextVar`.
- The `AsyncSession` is a `Scope.REQUEST` generator provider in `AppProvider` (`async with factory() as session: yield session`) — no separate dependency module.

The engine + session factory are `Scope.APP` providers (the engine as a generator provider so `container.close()` disposes it on shutdown). Repository adapters receive the `AsyncSession` by constructor injection and never commit or roll back — mutations `flush()` and map errors to result enums. Driver: `asyncpg` for postgres (`postgresql+asyncpg://`), `aiosqlite` for sqlite (`sqlite+aiosqlite:///`).

Also generate the unit-of-work pair:

- **`transaction_context.py`** (application services): `Transaction` and `TransactionContext` Protocols — `begin()` returns an async context manager yielding a `Transaction` with `commit()`; rollback-unless-committed semantics.
- **`sqlalchemy_transaction_context.py`** (infrastructure/database): adapter over the request-scoped session.

Mutating use cases inject `TransactionContext`, wrap repository calls in `async with ...begin() as transaction:`, and call `await transaction.commit()` only when every operation succeeded. Calls spanning several repositories inside one block are atomic — they share the request session.

#### `mongodb`

- **`mongo_client.py`** (infrastructure): wraps `motor.motor_asyncio.AsyncIOMotorClient`, created in `lifespan` and stored on `app.state`. A `get_database` dependency provides it. No session or transaction manager needed.

No Alembic for MongoDB.

### Step 5 — Generate auth layer

Ports are `typing.Protocol`s in `src/application/services/`; adapters are mechanism-qualified classes in `src/infrastructure/`.

#### `jwt`

- `PasswordHasher` port / `BcryptPasswordHasher` adapter — bcrypt via passlib.
- `TokenService` port / `JwtTokenService` adapter — PyJWT; issues access + refresh JWTs from settings.
- `Logger` port / `JsonLogger` adapter — structured logger; request correlation (`request_id`, `user_id`) via context vars in `infrastructure/logging/log_context.py`.
- `jwt_dependency.py` — `get_current_user` decodes the JWT, records the user id in the logging context, returns `TokenClaimsDTO`. Protect routers with `dependencies=[Depends(get_current_user)]`.
- Auth use case + DTOs + routes under `src/application/use_cases/auth/` and `src/api/routers/auth/`.

#### `oauth2`

- `OAuthService` port / adapter — exchanges provider token via `httpx`.
- Keep the JWT guard for internal session tokens issued after OAuth exchange. No `PasswordHasher`.

#### `apikey`

- `APIKeyService` port / adapter — validates key against DB.
- Guard in `src/api/dependencies/api_key_dependency.py`.

### Step 6 — Generate cache layer (redis only)

- `CacheService` port (application layer): `get()`, `set()`, `delete()`.
- `RedisCacheService` adapter (infrastructure): `redis.asyncio` client created in `lifespan`, disposed on shutdown.
- Bind it at `Scope.APP` in `AppProvider` (generator provider so cleanup runs at `container.close()`).

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
- `FastAPI(lifespan=lifespan)`; a `request_context` middleware that enters `async_request_scope()` and scopes the `request_id`/`user_id` context vars per request.
- `app.include_router(...)` for each router.

Copy `injection.py` (RequestScope, request_scope context managers, TypedBinder, Injected) verbatim from `FastAPI/API_PostgressDB/src/api/dependencies/injection.py`.

### Step 9 — Generate the composition root

`AppModule` in `src/api/dependencies/providers.py` is the composition root — one declarative line per binding via `TypedBinder`, constructors auto-wired via `@inject`:
- Stateless singletons (`PasswordHasher`, `TokenService`, `Logger`, cache): `typed_binder.bind_typed(PasswordHasher).to(BcryptPasswordHasher, scope=singleton)`.
- Engine, session factory: singleton `@provider` methods; the session: a request-scoped `@provider` method (disposed via `aclose()` by the scope teardown).
- `bind_typed(<Entity>Repository).to(Sqlalchemy<Entity>Repository, scope=request)` and `bind_typed(TransactionContext).to(SqlAlchemyTransactionContext, scope=request)` — same request session, so repositories and the transaction context share one transaction.
- `bind_self_typed(<Entity>UseCase, scope=request)` — dependencies resolved automatically.
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

Dev: `pytest>=8.0`, `pytest-asyncio>=0.23`, `httpx>=0.27`, `ruff>=0.4`.

`[tool.ruff]` with `line-length = 80`. `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`.

### Step 11 — Copy architecture docs

Copy `CLAUDE.md` and `AGENT.md` verbatim from `FastAPI/API_PostgressDB/` into the new project root.

### Step 12 — Generate `.env.example`

Only variables for the resolved stack with placeholder values. No real secrets.

### Step 13 — Validate

```bash
uv run ruff check src/ --fix && uv run ruff format src/
```

### Step 14 — Summary

Report: project name and path, resolved stack, file count by layer, ruff result, and next steps (install deps, copy `.env`, run migrations if applicable, start with `uvicorn src.main:app --reload`).
