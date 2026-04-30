---
name: fastapi-clean-architecture-template
description: Scaffold a new project following Clean Architecture principles on FastAPI — strict 4-layer structure (Domain, Application, Infrastructure, API) with unidirectional dependencies, repository pattern, result-enum error handling, and fastapi-injector DI. Supports PostgreSQL, MongoDB, SQLite; JWT, OAuth2, API key auth; optional Redis cache.
argument-hint: "<project-name> [--db postgres|mongodb|sqlite] [--auth jwt|oauth2|apikey] [--cache none|redis] [--no-docker]"
disable-model-invocation: true
metadata:
  version: "1.1.0"
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
│   ├── container.py
│   ├── config/settings.py
│   ├── domain/
│   │   ├── entities/
│   │   ├── enums/operation_results.py
│   │   └── repositories/
│   ├── application/
│   │   ├── services/
│   │   └── use_cases/
│   ├── infrastructure/
│   │   ├── auth/
│   │   ├── database/
│   │   │   └── models/__init__.py
│   │   └── repositories/
│   └── api/
│       ├── dependencies/
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

Add `alembic/` + `alembic.ini` for `postgres` or `sqlite`. Add `Dockerfile` + `docker-compose.yml` unless `--no-docker`.

### Step 3 — Generate shared files

Generate these regardless of stack. Use concise, idiomatic Python — no unnecessary comments.

- **`operation_results.py`**: Three `StrEnum` classes — `CreateResult`, `UpdateResult`, `DeleteResult`. Values: `success`, `failure`, `concurrency_error`, `unique_constraint_error` on all three; add `not_found` to `UpdateResult` and `DeleteResult`.
- **`base_schema.py`**: Pydantic `BaseModel` subclass `APIModelBase` with `alias_generator=to_camel` and `populate_by_name=True`.
- **`operation_schema.py`**: Three `APIModelBase` subclasses — `CreateOperationResponse(id: int | None)`, `UpdateOperationResponse(message: str)`, `DeleteOperationResponse(message: str)`.
- **`result_status_maps.py`**: Three functions — `create_response`, `update_response`, `delete_response` — each mapping the corresponding result enum to a `JSONResponse` with the correct HTTP status code (201 success-create, 200 success-update/delete, 404 not-found, 409 conflict, 500 failure).

### Step 4 — Generate database layer

#### `postgres` or `sqlite`

Four files following the SQLAlchemy 2.0 async session pattern:

- **`connection_factory_base.py`** (application layer): abstract `get_session()` async context manager and `close()`.
- **`connection_factory.py`** (infrastructure): creates `AsyncEngine` + `async_sessionmaker`. `get_session()` checks a `ContextVar[AsyncSession | None]` called `_active_session` — yields the active session if set, otherwise opens a new one with its own commit/rollback.
- **`transaction_manager_base.py`** (application layer): abstract `begin_transaction()` async context manager.
- **`transaction_manager.py`** (infrastructure): injects `ConnectionFactoryBase`; `begin_transaction()` sets `_active_session` ContextVar, delegates to the connection factory, handles commit/rollback.
- **`base.py`**: SQLAlchemy `DeclarativeBase` subclass.

Driver: `asyncpg` for postgres (`postgresql+asyncpg://`), `aiosqlite` for sqlite (`sqlite+aiosqlite:///`).

#### `mongodb`

- **`mongo_client_base.py`** (application layer): abstract `get_database()`.
- **`mongo_client.py`** (infrastructure): wraps `motor.motor_asyncio.AsyncIOMotorClient`. No session or transaction manager needed.

No Alembic for MongoDB.

### Step 5 — Generate auth layer

#### `jwt`

- `PasswordHasherBase` / `PasswordHasher` — bcrypt via passlib.
- `TokenServiceBase` / `TokenService` — python-jose; issues access + refresh JWTs from settings.
- `UserContextBase` / `UserContext` — request-scoped; `populate()` raises `RuntimeError` on second call; scalar properties only (`user_id`, `role`).
- `jwt_dependency.py` — decodes JWT, calls `user_context.populate()`, returns `TokenClaimsDTO`.
- Auth use case + DTO + routes under `src/application/use_cases/auth/` and `src/api/routers/auth/`.

#### `oauth2`

- `OAuthServiceBase` / `OAuthService` — exchanges provider token via `httpx`.
- Keep `UserContextBase` / `UserContext` and JWT guard for internal session tokens issued after OAuth exchange.
- No `PasswordHasher`.

#### `apikey`

- `APIKeyServiceBase` / `APIKeyService` — validates key against DB.
- Guard in `src/api/dependencies/api_key_dependency.py`.
- No `UserContextBase` unless user identity is needed.

### Step 6 — Generate cache layer (redis only)

- `CacheServiceBase` (application layer): abstract `get()`, `set()`, `delete()`.
- `RedisService` (infrastructure): `redis.asyncio` client, singleton scope, `close()` method.
- Bind as singleton in `container.py`; call `close()` in `lifespan` shutdown.

### Step 7 — Generate `settings.py`

`pydantic-settings` `BaseSettings`. Include only fields for the resolved stack:

- Always: `APP_NAME`, `DEBUG`
- postgres/sqlite: `DATABASE_URL`, `IS_SQL_ECHO_ENABLED: bool = False`
- mongodb: `MONGODB_URL`, `MONGODB_DB_NAME`
- jwt/oauth2: `SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES = 30`, `REFRESH_TOKEN_EXPIRE_DAYS = 7`
- redis: `REDIS_URL`

### Step 8 — Generate `main.py`

Key ordering requirement — strictly in this order:
1. Create `Injector([AppModule()])`
2. Create `FastAPI(lifespan=lifespan)`
3. `app.add_middleware(InjectorMiddleware, injector=injector)`
4. `attach_injector(app, injector)`
5. `app.include_router(...)` for each router

`lifespan` shutdown block closes all singletons that have a `close()` method.

### Step 9 — Generate `container.py`

`injector.Module` subclass `AppModule` with a `configure(binder)` method. Bind every Base/implementation pair. Use `singleton` scope only for `ConnectionFactory`, external service clients, and `RedisService`.

### Step 10 — Generate `pyproject.toml`

Base dependencies: `fastapi>=0.115`, `fastapi-injector>=0.6`, `injector>=0.22`, `pydantic>=2.0`, `pydantic-settings>=2.0`, `uvicorn[standard]>=0.30`.

Stack additions:

| Stack | Extra |
|-------|-------|
| postgres | `sqlalchemy[asyncio]>=2.0`, `asyncpg>=0.29`, `alembic>=1.13` |
| sqlite | `sqlalchemy[asyncio]>=2.0`, `aiosqlite>=0.20`, `alembic>=1.13` |
| mongodb | `motor>=3.4` |
| jwt | `python-jose[cryptography]>=3.3`, `passlib[bcrypt]>=1.7` |
| oauth2 | `httpx>=0.27`, `python-jose[cryptography]>=3.3` |
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
