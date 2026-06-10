---
name: fastapi-clean-architecture-template
description: Scaffold a new project following Clean Architecture principles on FastAPI — strict 4-layer structure (Domain, Application, Infrastructure, API) with unidirectional dependencies, ports as typing.Protocol, the repository pattern, result-enum error handling, and FastAPI-native dependency injection (Depends providers). Supports PostgreSQL, MongoDB, SQLite; JWT, OAuth2, API key auth; optional Redis cache.
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
│       ├── dependencies/      # database.py, providers.py, guards
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
- **`api/dependencies/database.py`**: `get_session(request) -> AsyncIterator[AsyncSession]` — reads `request.app.state.session_factory` and yields a request-scoped session via `async with`.

The engine + session factory are created once in `main.lifespan` and stored on `app.state.session_factory`; the engine is disposed on shutdown. Repository adapters receive the `AsyncSession` by constructor injection. Driver: `asyncpg` for postgres (`postgresql+asyncpg://`), `aiosqlite` for sqlite (`sqlite+aiosqlite:///`).

For an operation that must be atomic across repositories, manage a single transaction in the use case over the shared request session. The template ships the non-atomic default and does not include a transaction-manager abstraction.

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
- Provide it via an `@lru_cache` provider (or `app.state`) in `dependencies/providers.py`.

### Step 7 — Generate `settings.py`

`pydantic-settings` `BaseSettings` plus an `@lru_cache def get_settings() -> Settings`. Include only fields for the resolved stack:

- Always: `APP_NAME`, `DEBUG`
- postgres/sqlite: `DATABASE_URL`, `IS_SQL_ECHO_ENABLED: bool = False`
- mongodb: `MONGODB_URL`, `MONGODB_DB_NAME`
- jwt/oauth2: `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES = 30`, `REFRESH_TOKEN_EXPIRE_DAYS = 7`
- redis: `REDIS_URL`

### Step 8 — Generate `main.py`

- `lifespan`: build the engine + session factory (or Mongo/Redis clients), store on `app.state`, dispose on shutdown.
- `FastAPI(lifespan=lifespan)`.
- A request-id middleware that sets the `request_id` context var per request.
- `app.include_router(...)` for each router.

No `Injector`, no `InjectorMiddleware`, no `attach_injector`.

### Step 9 — Generate dependency providers

`src/api/dependencies/providers.py` is the composition root. Plain functions wire ports to adapters:
- Stateless singletons (`PasswordHasher`, `TokenService`, `Logger`, cache) via `@lru_cache`.
- `get_<entity>_repository(session: Annotated[AsyncSession, Depends(get_session)])` returns the adapter.
- `get_<entity>_use_case(...)` composes the repository + service ports and returns the concrete use case.

### Step 10 — Generate `pyproject.toml`

Base dependencies: `fastapi>=0.115`, `pydantic>=2.0`, `pydantic-settings>=2.0`, `uvicorn[standard]>=0.30`. (No `injector` / `fastapi-injector`.)

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
