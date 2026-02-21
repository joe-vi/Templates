# Agent Instructions for FastAPI Clean Architecture Template

## 1. Architecture

Dependencies flow **inward only**: API → Infrastructure → Application → Domain. Domain never imports from any other layer.

| Layer | Location | Contains | Depends On |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities, Repository ABCs, QueryRows, result enums | Nothing |
| Application | `src/application/` | Use case ABCs/impls, DTOs, converters, service ABCs | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, repository impls, auth impls | Domain + Application |
| API | `src/api/` | Routes, request/response schemas, API converters | Application (Base classes) |
| DI Container | `src/container.py` | `injector.Module` with `Binder.bind()` wiring | All layers |

### File Organisation

Files are organised by **type** first, then **entity name** within each layer.

```
src/
├── domain/
│   ├── entities/<entity>/<entity>.py
│   ├── repositories/<entity>/
│   │   ├── <entity>_repository_base.py
│   │   └── <entity>_query_row.py          # when needed
│   └── enums/
│       ├── <entity>_enum.py
│       └── operation_results.py
│
├── application/
│   ├── use_cases/<entity>/
│   │   ├── <entity>_dto.py
│   │   ├── <entity>_converter.py
│   │   ├── <entity>_use_case_base.py
│   │   └── <entity>_use_case.py
│   └── services/
│       ├── transaction_manager_base.py
│       ├── user_context_base.py
│       └── <service>_base.py
│
├── infrastructure/
│   ├── repositories/<entity>/<entity>_repository.py
│   ├── auth/
│   │   ├── password_hasher.py
│   │   ├── token_service.py
│   │   └── user_context.py
│   └── database/
│       ├── base.py
│       ├── models/
│       │   ├── __init__.py                # re-exports all models
│       │   └── <entity>_model.py
│       ├── connection_factory_base.py
│       ├── connection_factory.py
│       └── transaction_manager.py
│
└── api/
    ├── dependencies/jwt_dependency.py     # cross-cutting guards only
    ├── routers/<entity>/
    │   ├── <entity>_schema.py
    │   ├── <entity>_converter.py
    │   └── <entity>_routes.py
    ├── schemas/operation_schema.py        # shared response schemas
    └── result_status_maps.py             # shared response helpers
```

**Rule**: For every new entity, create `src/{layer}/{type}/{entity}/` folders across all layers. Never scatter entity files into flat shared directories.

---

## 2. Naming Conventions

### Classes
- ABCs/interfaces **must** end with `Base` — `UserRepositoryBase`, `UserUseCaseBase`
- Entities: singular nouns — `User`, `Order`
- Status Enums: singular noun describing the concept with `StrEnum` (e.g., `GreetingStatus`, `OrderState`)
- Operation result enums: generic and shared — `CreateResult`, `UpdateResult`, `DeleteResult`. Never entity-specific (e.g., `CreateUserResult` is forbidden)
- DTOs: frozen dataclasses with `DTO` suffix. Use `list[UserDTO]` directly as return types; never create a wrapper collection DTO (e.g., `UserListDTO` is forbidden)
- API schemas: `Request` suffix for inputs, `Response` suffix for outputs
- Use Cases: `UserUseCaseBase` (ABC) → `UserUseCase` (implementation)

### Variables & Properties
- Collections: plural names; sets: `_set` suffix; dicts: `_map` suffix
- Internal class members: `_` prefix; never access from outside the class
- Booleans must read like questions: `is_active`, `has_items`, `can_update` — never bare nouns (`success` → `is_successful`)
- No abbreviations: `repository` not `repo`, `connection` not `conn`
- No single-letter or vague names: `greeting` not `g`, `create_greeting_dto` not `dto`, `query_result` not `result`
- No numbered variants: use contextual names (`existing_greeting`, `created_greeting`) — not `greeting1`/`greeting2`

---

## 3. Core Patterns

### Repository Pattern
- **One CRUD operation per method** — never combine read+write in a single repository method. If a use case needs to read then write, it calls two separate methods. Orchestration belongs in the use case.
- **Mutation methods catch all DB exceptions internally** and return the appropriate result enum. Nothing propagates to use cases. Exception mapping:
  - `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`
  - `DBAPIError` where `isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError)` → `CONCURRENCY_ERROR`; otherwise → `FAILURE`
  - `Exception` → `FAILURE`
- **ABC methods have Google-style docstrings** (Args + Returns). Overriding implementations do NOT repeat docstrings.
- Repositories inject `ConnectionFactoryBase`; each method opens its own session with `async with self._connection_factory.get_session()`.
- Never pass sessions to repository constructors.

### Dependency Injection (fastapi-injector)
- Every injectable class `__init__` **must** have `@inject` from `injector`. Omitting it causes `TypeError` at startup because the injector calls `__init__()` with no arguments.
- In `main.py`: call `app.add_middleware(InjectorMiddleware, injector=injector)` **before** `attach_injector(app, injector)`. Missing `InjectorMiddleware` causes `LookupError` for any request-scoped service. `attach_injector` must be called before including routers.
- Routes inject use cases/services with `Injected(BaseClass)` — never `Depends()` for this purpose.
- `Depends()` is only permitted in `src/api/dependencies/` for cross-cutting guards, and in `dependencies=[...]` on an `APIRouter`.
- `singleton` scope only for `ConnectionFactory` and external service clients (HTTP clients, connection pools). Never singleton for repositories or use cases.
- The injector resolves the full dependency chain automatically from constructor signatures.

### Authentication Guards
- Guard functions live exclusively in `src/api/dependencies/` — never inline in route files.
- The guard decodes the JWT, calls `user_context.populate()` once, and returns `TokenClaimsDTO`.
- Protect an entire router by declaring `dependencies=[Depends(get_current_user)]` on the `APIRouter` — never scatter individual `Depends(get_current_user)` in route function signatures.

### Request-Scoped User Context
- `UserContextBase` is bound with `request_scope` (never `singleton`); one fresh instance per HTTP request.
- `populate()` raises `RuntimeError` on a second call — prevents accidental identity overwrites.
- Inject into use cases that need the caller's identity. Read scalar values (`user_context.user_id`) and pass those to repositories — never pass the context object to repos.
- Only valid on routes protected by `get_current_user`. Accessing properties on unprotected routes raises `RuntimeError`.
- Implementation lives in `src/infrastructure/auth/`.

---

## 4. Enums

- Use `StrEnum` (Python 3.11+); values are lowercase strings matching DB storage (`ACTIVE = "active"`). Compatible with Pydantic and SQLAlchemy without extra configuration.
- All enums live in `src/domain/enums/` and can be imported by any layer.
- In SQLAlchemy models, define the `SQLAlchemyEnum` type object at module level (not inline) and reuse it across the model.
- Enums flow unchanged through all layers — entity, DTO, and API schema all use the same enum type directly; no conversion needed.

### Operation Result Enums
- Three generic shared enums in `src/domain/enums/operation_results.py`: `CreateResult`, `UpdateResult`, `DeleteResult`.
- Never create entity-specific variants (e.g., `CreateGreetingResult` is wrong).
- `LoginResult` is the one permitted operation-specific enum (auth only), also in `operation_results.py`. It covers outcomes unique to auth (`INVALID_CREDENTIALS`, `USER_INACTIVE`).
- `CreateResult` values: `SUCCESS`, `FAILURE`, `CONCURRENCY_ERROR`, `UNIQUE_CONSTRAINT_ERROR`.
- `UpdateResult` values: above + `NOT_FOUND`.
- `DeleteResult` values: `SUCCESS`, `FAILURE`, `CONCURRENCY_ERROR`, `NOT_FOUND`.
- Create use cases return `tuple[CreateResult, int | None]` — id is `None` on failure. Update/delete return just the result enum.
- Use cases contain no exception handling for mutations — they forward repository results as-is.

### API Response Conventions
- Shared schemas in `src/api/schemas/operation_schema.py`: `CreateOperationResponse`, `UpdateOperationResponse`, `DeleteOperationResponse`.
- Shared helpers in `src/api/result_status_maps.py`: `create_response()`, `update_response()`, `delete_response()`. Routes call these to build the response and set the correct HTTP status code.

| Result | HTTP Code |
|--------|-----------|
| SUCCESS (create) | 201 Created |
| SUCCESS (update/delete) | 200 OK |
| NOT_FOUND | 404 Not Found |
| UNIQUE_CONSTRAINT_ERROR | 409 Conflict |
| CONCURRENCY_ERROR | 409 Conflict |
| FAILURE | 500 Internal Server Error |

For read endpoints returning `None` from the use case: raise `HTTPException(status_code=404, detail="Resource not found")`.

---

## 5. Database

### DB-Generated Values
Never set these in Python code — the database generates them:
- **`id`**: `autoincrement=True` on the model. Entity holds `id: int | None = None` before insert; populated after `session.refresh()`.
- **`created_at`**: `server_default=func.now()` on the model. Never set in Python code (no `datetime.now()`, no `__post_init__`, no default in the entity). Entity field is `datetime | None = None`. Do not pass to the model constructor.
- **`updated_at`**: `onupdate=func.now()` on the model. SQLAlchemy automatically includes it in every UPDATE. Never set manually. Stays `None` until first update.
- **Always call `session.refresh()`** after every insert/update to populate DB-generated values back onto the model.

### Database Constraints
- Every constraint **must** have an explicit `name` parameter so Alembic can reference and drop it by name across environments.
- Applies to: `UniqueConstraint`, `ForeignKeyConstraint`, `CheckConstraint`, `Index`, and any other SQLAlchemy constraint.
- Declare all constraints in `__table_args__`, not as column-level shorthand (except primary key).
- For `Index`, the name is the **first positional argument** (not a `name=` kwarg): `Index("ix_orders_status", "status")`.

| Constraint | Naming pattern | Example |
|---|---|---|
| Unique | `uq_{table}_{column(s)}` | `uq_users_username` |
| Foreign key | `fk_{table}_{column}` | `fk_orders_user_id` |
| Check | `ck_{table}_{description}` | `ck_orders_amount_positive` |
| Index | `ix_{table}_{column(s)}` | `ix_orders_status` |

---

## 6. Multi-Repository Operations

### Non-Atomic (independent operations)
Inject each repository directly via constructor injection. Each method opens its own session. Use when failure in one operation does not need to roll back others.

### Atomic (`begin_transaction`)
Inject `TransactionManagerBase` (application layer) alongside repositories. Wrap the block with `async with self._transaction_manager.begin_transaction()`. `ConnectionFactory` maintains a `ContextVar[AsyncSession | None]` called `_active_session`; the active session is shared transparently across all repository calls within that block — repositories require zero changes.

`TransactionManagerBase` lives in the application layer; use cases inject it. `ConnectionFactoryBase` lives in the infrastructure layer; repositories inject it. `TransactionManager` (infrastructure) implements `TransactionManagerBase` by injecting `ConnectionFactoryBase` and delegating `begin_transaction()` to it. The two abstractions are completely independent — no inheritance relationship.

Session resolution inside `get_session()`:
```
_active_session set?
  → yes: yield it (begin_transaction owns commit/rollback)
  → no:  open new session, commit/rollback on exit
```

| Scenario | Pattern |
|---|---|
| Single or multiple repos, independent ops | Inject repos only |
| Multiple repos (or single repo, multiple methods) that must all succeed or all fail | `TransactionManagerBase` + `begin_transaction()` |

Do not use `begin_transaction` when operations are independent.

---

## 7. External Services

- Interface (`<Service>Base`) lives in `src/application/services/` — use cases depend only on this abstraction. Keeps use cases framework-agnostic and the provider swappable with a single line change in `container.py`.
- Implementation lives in `src/infrastructure/<service>/`.
- Bound in `container.py`; typically `singleton` for shared client connections.
- Any singleton holding a long-lived resource (HTTP client, connection pool, socket) **must** have a `close()` method on its base class; call it in the `lifespan` shutdown block in `main.py`. Follow the `ConnectionFactoryBase.close()` pattern for every new singleton that manages external resources.
- Add required config to `src/config/settings.py` (loaded from `.env`). Never hardcode configuration values.
- To switch providers: create the new implementation in `src/infrastructure/<service>/` and update `to=NewImpl` in `container.py`. The use case is untouched.

---

## 8. Query Row Pattern

Use when a repository query returns more data than a single domain entity holds — JOINs, aggregations, or projections with computed/nested values.

- **Core idea**: Repo returns a `QueryRow` dataclass (flat projection), application converter maps it to a DTO, use case returns the DTO. Keeps the domain entity clean while surfacing richer data.
- `QueryRow`: frozen dataclass, flat scalar fields (no nested objects; unfold joined data into scalar fields), read-only, never mutated or passed back to a repository.
- Name: `{Entity}{Qualifier}QueryRow` — qualifier describes what the query adds (e.g., `GreetingWithAuthorQueryRow`, `OrderWithStatsQueryRow`).
- Lives in `src/domain/repositories/{entity}/`, co-located with the repository base that declares it as a return type. Not an entity (no lifecycle, no identity) — exists solely to carry the result of a specific query.
- One `QueryRow` per query shape; if two queries return different projections, create two classes.
- Create a **dedicated DTO** in the application layer for the richer result; do not reuse a simpler entity DTO if the shape differs.
- Data flow: Repo returns `QueryRow` → application converter maps to DTO → use case returns DTO → API layer never receives a `QueryRow` directly.

---

## 9. Documentation

- **Class-level docstring**: always required (one-line purpose statement).
- **`__init__` docstring**: always required; document all parameters in an `Args` section.
- **Public abstract methods on ABCs**: Google-style docstrings with Args, Returns, Raises, Yields as applicable.
- **Implementation overrides**: no docstring — the ABC already documents the contract.
- **Private (`_`) methods**: no docstring needed.
- Methods not used outside the class must be prefixed with `_`.

---

## 10. Code Style

- Max line length: **140 characters**.
- Use `ruff` for linting and formatting (configured in `pyproject.toml`). After every code change: `ruff check src/ --fix && ruff format src/`.
- Always use `uv run`; never access `.venv` directly.
- Modern type annotations: `list[X]` not `List[X]`, `X | None` not `Optional[X]`.
- All DB operations are async; use `async def` and `await`.
- API prefix: `/api/v1`.
- **Never add `#` inline comments.** Code must be self-explanatory through clear naming — descriptive variable names, explicit function names, and well-structured logic eliminate the need for inline narration. If a line needs a comment to be understood, rename or restructure until it does not.

---

## 11. Adding a New Entity

Follow this layer order. Create `src/{layer}/{type}/{entity}/` folders at each step.

1. **Domain**: Define enums in `src/domain/enums/<entity>_enum.py`; entity dataclass in `src/domain/entities/<entity>/`; repository ABC in `src/domain/repositories/<entity>/`.
2. **Infrastructure**: Create DB model in `src/infrastructure/database/models/<entity>_model.py` and re-export from `models/__init__.py`; create repository implementation in `src/infrastructure/repositories/<entity>/`.
3. **Application**: Define frozen DTO dataclasses, entity converter with static methods, use case ABC and implementation in `src/application/use_cases/<entity>/`.
4. **API**: Define Pydantic request/response schemas, API converter, and routes using `Injected(UseCaseBase)` in `src/api/routers/<entity>/`.
5. **Wire up**: Add `binder.bind(BaseClass, to=Implementation)` pairs in `AppModule.configure()` in `container.py`; include the router in `main.py`. The injector automatically resolves the full dependency chain — no manual wiring beyond `binder.bind()`.

---

## 12. Testing

### Structure
Tests live in `tests/` and mirror the `src/` tree exactly. Per entity: `tests/application/use_cases/<entity>/` and `tests/api/routers/<entity>/` — one test file per source file being tested.

```bash
pytest                    # run all tests
pytest tests/application/ # application-layer only
pytest tests/api/         # API-layer only
pytest -v                 # verbose
```

### What to Test

| Layer | File | Test? | Reason |
|-------|------|-------|--------|
| Application | `<entity>_use_case.py` | Yes | Core business logic, mock the repository |
| Application | `<entity>_converter.py` | Yes | Entity ↔ DTO mapping correctness |
| API | `<entity>_converter.py` | Yes | Schema ↔ DTO mapping correctness |
| API | `<entity>_routes.py` | Yes | HTTP contract — status codes, request validation |
| Infrastructure | `<entity>_repository.py` | No | Requires a live DB; covered by integration tests |

### Use Case Tests
- Mock with `AsyncMock(spec=RepositoryBase)`.
- Annotate the fixture return type as `-> RepositoryBase` (not `-> AsyncMock`) — surfaces the repository's method names in the IDE. Mock-specific attributes like `.return_value` still work at runtime.
- `asyncio_mode = "auto"` is configured in `pyproject.toml`; no `@pytest.mark.asyncio` decorator needed.
- Group related assertions in inner test classes per method under test (e.g., `class TestCreateUser`, `class TestGetUser`).

### Route Tests
- Create a minimal `FastAPI()` app with only the router under test. **Never import `src/main.py` or `src/container.py`**.
- Use a `TestModule` that binds `AsyncMock(spec=UseCaseBase)` via `InstanceProvider`.
- Use `httpx.AsyncClient` with `ASGITransport`.
- `spec` on `AsyncMock` ensures mock methods match the real interface; async methods are automatically mocked correctly.
- Mock at the boundary nearest to the test: route tests mock the use case; use case tests mock the repository.

### Testing JWT-Protected Routes
- In `TestModule`, bind a mock `TokenServiceBase` (always returns valid `TokenClaimsDTO`) and a mock `UserContextBase` (pre-populated properties, no-op `populate()`).
- Send requests with a dummy `Authorization: Bearer <token>` header — the stub token service accepts any value.

---

## 13. Anti-Patterns

- Don't pass sessions to repository constructors — inject `ConnectionFactoryBase` instead
- Don't inject `ConnectionFactoryBase` into use cases — use `TransactionManagerBase` for atomic ops; only repositories inject `ConnectionFactoryBase`
- Don't use `Depends()` for use case or service injection in routes — use `Injected(BaseClass)`; `Depends()` is only for cross-cutting guards in `src/api/dependencies/` and `dependencies=[...]` on `APIRouter`
- Don't bypass use cases — routes never call repositories directly
- Don't let Domain import from Infrastructure or API layers
- Don't omit `Base` suffix on ABC classes
- Don't use concrete types in route signatures — always `Injected(UseCaseBase)`
- Don't create instances manually — let the injector resolve the chain
- Don't forget to add `binder.bind()` for new base/implementation pairs in `AppModule`
- Don't omit `@inject` on `__init__` — causes `TypeError: __init__() missing required positional arguments` at startup
- Don't omit `InjectorMiddleware` before `attach_injector()` — causes `LookupError` for request-scoped services
- Don't forget `attach_injector(app, injector)` before including routers
- Don't use `singleton` scope for repositories or use cases
- Don't forget to close singleton resources — implement `close()` on base class and call in `lifespan` shutdown
- Don't scatter entity files into flat shared directories
- Don't add `#` inline comments — use clear naming and structure to make code self-explanatory
- Don't create entity-specific result enums — use `CreateResult`, `UpdateResult`, `DeleteResult`
- Don't create a wrapper DTO for collections — return `list[EntityDTO]` directly
- Don't define guard functions inside route files — they belong in `src/api/dependencies/`
- Don't scatter `Depends(get_current_user)` in route function signatures — declare once on `APIRouter`
- Don't pass `UserContextBase` to repositories — extract scalar values and pass those

---

## 14. Debugging Tips

1. **SQL logging**: set `IS_SQL_ECHO_ENABLED=true` in `.env`
2. **Session issues**: ensure `async with self._connection_factory.get_session()` in every repo method
3. **DI middleware order**: `InjectorMiddleware` must be added before `attach_injector()` in `main.py`
4. **Missing `@inject`**: produces `TypeError: __init__() missing required positional arguments` at startup
5. **Missing binding**: verify all base/implementation pairs in `AppModule.configure()`
6. **Layer violations**: domain must never import from infrastructure or API

**DB migrations**: This template uses `create_all()` for simplicity. In production, use Alembic for migrations.

---

## 15. Keeping Quick-Reference Files in Sync

**When you update rules in this file**, sync the relevant changes into the quick-reference sections of these files so their inline summaries stay accurate:

- [.clinerules](.clinerules)
- [.cursorrules](.cursorrules)
- [.windsurfrules](.windsurfrules)
- [AGENTS.md](AGENTS.md)
- [CLAUDE.md](CLAUDE.md)
- [.antigravity/rules.md](.antigravity/rules.md)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)

These files each contain a condensed quick-reference summary that mirrors the critical rules here. Agent.md remains the single source of truth — the other files are entry-point summaries only.

---

## 16. File References

**Shared infrastructure (present in every project)**
- [Operation result enums](src/domain/enums/operation_results.py)
- [Operation response schemas](src/api/schemas/operation_schema.py)
- [Response helpers and status maps](src/api/result_status_maps.py)
- [DB Base](src/infrastructure/database/base.py)
- [DB models](src/infrastructure/database/models/)
- [Connection factory Base](src/infrastructure/database/connection_factory_base.py)
- [Connection factory](src/infrastructure/database/connection_factory.py)
- [Transaction manager Base](src/application/services/transaction_manager_base.py)
- [Transaction manager](src/infrastructure/database/transaction_manager.py)
- [DI Container](src/container.py)
- [Settings](src/config/settings.py)
- [Main app](src/main.py)

**Authentication infrastructure (present in every project using JWT)**
- [JWT guard dependency](src/api/dependencies/jwt_dependency.py)
- [User context Base](src/application/services/user_context_base.py)
- [User context implementation](src/infrastructure/auth/user_context.py)
- [Password hasher Base](src/application/services/password_hasher_base.py)
- [Password hasher implementation](src/infrastructure/auth/password_hasher.py)
- [Token service Base](src/application/services/token_service_base.py)
- [Token service implementation](src/infrastructure/auth/token_service.py)
- [Auth use case Base](src/application/use_cases/auth/auth_use_case_base.py)
- [Auth use case implementation](src/application/use_cases/auth/auth_use_case.py)
- [Auth DTOs](src/application/use_cases/auth/auth_dto.py)
- [Auth routes](src/api/routers/auth/auth_routes.py)

**Per-entity file locations** (substitute `<entity>` with your entity name)

| Purpose | Path |
|---------|------|
| Entity dataclass | `src/domain/entities/<entity>/<entity>.py` |
| Entity enums | `src/domain/enums/<entity>_enum.py` |
| Repository Base | `src/domain/repositories/<entity>/<entity>_repository_base.py` |
| Repository implementation | `src/infrastructure/repositories/<entity>/<entity>_repository.py` |
| DTOs | `src/application/use_cases/<entity>/<entity>_dto.py` |
| Entity converter | `src/application/use_cases/<entity>/<entity>_converter.py` |
| Use case Base | `src/application/use_cases/<entity>/<entity>_use_case_base.py` |
| Use case implementation | `src/application/use_cases/<entity>/<entity>_use_case.py` |
| API schemas | `src/api/routers/<entity>/<entity>_schema.py` |
| API converter | `src/api/routers/<entity>/<entity>_converter.py` |
| Routes | `src/api/routers/<entity>/<entity>_routes.py` |
