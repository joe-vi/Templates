# Agent Instructions for FastAPI Clean Architecture Template

## 1. Architecture

Dependencies flow **inward only**: API → Infrastructure → Application → Domain. Domain never imports from any other layer.

| Layer | Location | Contains | Depends On |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities, repository ports (Protocols), enums | Nothing |
| Application | `src/application/` | Use cases, DTOs, converters, service ports (Protocols) | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, repository adapters, auth/logging adapters, engine/session | Domain + Application |
| API | `src/api/` | Routes, request/response schemas, API converters, **dependency providers** | Application + Infrastructure (only in `dependencies/`) |

There is **no IoC container**. The composition root is FastAPI's own dependency system: provider functions in `src/api/dependencies/providers.py` build the graph, and FastAPI resolves and caches it per request.

### File Organisation

Files are organised by **type** first, then **entity name** within each layer.

```
src/
├── domain/
│   ├── entities/<entity>/<entity>.py
│   ├── repositories/<entity>/<entity>_repository.py   # Protocol port (clean name)
│   └── enums/{<entity>_enum.py, operation_results.py}
├── application/
│   ├── use_cases/<entity>/
│   │   ├── <entity>_dto.py
│   │   ├── <entity>_converter.py       # module functions, not a class
│   │   └── <entity>_use_case.py        # concrete class, no separate ABC
│   └── services/<service>.py           # Protocol ports (password_hasher, token_service, logger)
├── infrastructure/
│   ├── repositories/<entity>/sqlalchemy_<entity>_repository.py   # adapter (mechanism-qualified name)
│   ├── auth/{bcrypt_password_hasher.py, jwt_token_service.py}
│   ├── logging/{json_logger.py, log_context.py}
│   └── database/{base.py, session.py, models/<entity>_model.py}
└── api/
    ├── dependencies/
    │   ├── database.py        # get_session (request-scoped AsyncSession)
    │   ├── providers.py       # composition root: ports -> adapters, use-case builders
    │   └── jwt_dependency.py  # get_current_user guard
    ├── routers/<entity>/{<entity>_schema.py, <entity>_converter.py, <entity>_routes.py}
    ├── schemas/{base_schema.py, operation_schema.py}
    └── result_status_maps.py  # result enum -> HTTP status + message maps
└── main.py                    # app, lifespan (engine), request-id middleware, routers
```

**Rule**: For every new entity, create `src/{layer}/{type}/{entity}/` folders across all layers. Never scatter entity files into flat shared directories.

---

## 2. Naming Conventions

### Classes
- **Ports are `typing.Protocol`s with the clean, central name** — `UserRepository`, `PasswordHasher`, `TokenService`, `Logger`. No `Base` suffix.
- **Adapters (implementations) are qualified by their mechanism** — `SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`.
- Use cases are plain concrete classes (`UserUseCase`, `AuthUseCase`) — no separate interface; there is only ever one implementation and routes/tests depend on the concrete class.
- Entities: singular nouns — `User`, `Order`.
- Status enums: singular `StrEnum` (`UserRole`, `UserStatus`).
- Operation result enums: generic and shared — `CreateResult`, `UpdateResult`, `DeleteResult`. Never entity-specific. `LoginResult` is the one permitted auth-specific enum.
- DTOs: frozen dataclasses with `DTO` suffix. Return `list[UserDTO]` directly; never a wrapper collection DTO.
- API schemas: `Request` suffix for inputs, `Response` suffix for outputs; all inherit from `APIModelBase` (`src/api/schemas/base_schema.py`).
- `APIModelBase`: serialises to camelCase JSON, accepts both camelCase and snake_case on input.

### Variables & Properties
- Collections: plural; sets: `_set` suffix; dicts: `_map` suffix.
- Internal class members: `_` prefix; never access from outside the class.
- Booleans read like questions: `is_active`, `has_items`. No abbreviations (`repository` not `repo`).

---

## 3. Core Patterns

### Ports & Adapters (dependency inversion via Protocol)
- A **port** is a `typing.Protocol` defining the methods a collaborator must provide. It lives where it is *consumed*: repository ports in `src/domain/`, service ports in `src/application/services/`.
- An **adapter** is a plain class that structurally satisfies the port. It does **not** import or subclass the port — structural typing keeps the adapter decoupled from the abstraction.
- Use cases depend on ports (constructor parameters typed as the Protocol). Providers supply the concrete adapter.

### Dependency Injection (FastAPI `Depends`)
- The composition root is `src/api/dependencies/providers.py`. Each provider is a plain function; collaborators are declared with `Annotated[Port, Depends(provider)]`.
- Stateless singletons (`PasswordHasher`, `TokenService`, `Logger`) use `@lru_cache` on their provider. Per-request objects (repositories, use cases) are built fresh by their provider each request; FastAPI caches each dependency once per request.
- Routes depend on the **concrete use case** via `Annotated[UserUseCase, Depends(get_user_use_case)]`.
- Tests override any provider with `app.dependency_overrides[provider] = ...` — no second container, no `@inject`, no middleware ordering.

### Database session & transactions
- The engine and `async_sessionmaker` are created once in `main.lifespan` and stored on `app.state.session_factory`.
- `api.dependencies.database.get_session` yields a **request-scoped `AsyncSession`**. Because FastAPI caches it per request, every adapter in one request shares the same session — a natural unit of work. There is **no module-global session state**.
- Repository **adapters receive the `AsyncSession`** by constructor injection. Never pass sessions to use cases; never keep session state in a `ContextVar`.
- **Mutation methods own their commit** and map DB errors to result enums (so the route can map the result to a status before responding). Read methods just query.
  - `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`
  - `DBAPIError` whose `__cause__` is `asyncpg…DeadlockDetectedError` → `CONCURRENCY_ERROR`; otherwise `FAILURE`
  - any other `Exception` → `FAILURE` (after `rollback()`)
- For an operation spanning multiple repositories that must be atomic, manage a single transaction in the use case over the shared session (repositories would not self-commit in that flow). The template ships the non-atomic default; it does not include a transaction-manager abstraction.

### Converters
- Converters are **module-level functions**, not classes of static methods. `user_converter.to_dto(...)`, `to_entity(...)`, etc.

### Authentication & current user
- `get_current_user` (in `src/api/dependencies/jwt_dependency.py`) decodes the Bearer JWT, raises 401 on failure, records the user id in the logging context, and returns a `TokenClaimsDTO`.
- Protect a whole router with `dependencies=[Depends(get_current_user)]` on the `APIRouter`. Components needing the caller's identity depend on `get_current_user`.
- Request correlation for logs (`request_id`, `user_id`) is carried in context variables in `src/infrastructure/logging/log_context.py` — set by the request-id middleware and the guard. Context variables are appropriate here because they carry cross-cutting observability metadata, not control-flow or transactional state.

### Routes & responses
- Routes return the **response model object**; FastAPI serialises it (camelCase, via `response_model`). **Never** return a hand-built `JSONResponse(model.model_dump())` — that bypasses `response_model` and the alias generator.
- For operations whose status varies by result enum, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, and return the response model. Use `HTTPException` for read-not-found and auth failures.

---

## 4. Enums

- Use `StrEnum` (Python 3.11+); values are lowercase strings matching DB storage. All enums live in `src/domain/enums/`.
- In SQLAlchemy models, define the `SQLAlchemyEnum` type object at module level and reuse it.
- Operation result enums: `CreateResult` (`SUCCESS`, `FAILURE`, `CONCURRENCY_ERROR`, `UNIQUE_CONSTRAINT_ERROR`), `UpdateResult` (+`NOT_FOUND`), `DeleteResult` (`SUCCESS`, `FAILURE`, `CONCURRENCY_ERROR`, `NOT_FOUND`). Create use cases return `tuple[CreateResult, int | None]`.

### API Response Conventions
| Result | HTTP Code |
|--------|-----------|
| SUCCESS (create) | 201 Created |
| SUCCESS (update/delete) | 200 OK |
| NOT_FOUND | 404 Not Found |
| UNIQUE_CONSTRAINT_ERROR / CONCURRENCY_ERROR | 409 Conflict |
| FAILURE | 500 Internal Server Error |

Status/message maps live in `src/api/result_status_maps.py`.

---

## 5. Database

### DB-Generated Values
Never set these in Python code:
- **`id`**: `autoincrement=True`. Entity holds `id: int | None = None` before insert; populated after `session.refresh()`.
- **`created_at`**: `server_default=func.now()`. Entity field is `datetime | None = None`. Call `session.refresh()` after insert to populate it.

### Database Constraints
- Every constraint **must** have an explicit `name` so Alembic can manage it. Declare constraints in `__table_args__`.

| Constraint | Naming pattern | Example |
|---|---|---|
| Unique | `uq_{table}_{column(s)}` | `uq_users_username` |
| Foreign key | `fk_{table}_{column}` | `fk_orders_user_id` |
| Check | `ck_{table}_{description}` | `ck_orders_amount_positive` |
| Index | `ix_{table}_{column(s)}` | `ix_orders_status` |

---

## 6. External Services

- Port (`Protocol`) lives in `src/application/services/<service>.py`. Use cases depend only on the port.
- Adapter lives in `src/infrastructure/<service>/`, mechanism-qualified name.
- Wire it in `src/api/dependencies/providers.py`. Stateless singletons use `@lru_cache`; resources needing teardown are created in `main.lifespan` and disposed there (see the database engine).
- To switch providers: write a new adapter and change the `return` in its provider. The use case is untouched.

---

## 7. Adding a New Entity

1. **Domain**: enums in `src/domain/enums/<entity>_enum.py`; entity dataclass in `src/domain/entities/<entity>/`; repository **Protocol** in `src/domain/repositories/<entity>/<entity>_repository.py`.
2. **Infrastructure**: ORM model in `src/infrastructure/database/models/<entity>_model.py` (re-export from `models/__init__.py`); adapter `sqlalchemy_<entity>_repository.py` taking an `AsyncSession`.
3. **Application**: frozen DTOs, converter **functions**, concrete use case in `src/application/use_cases/<entity>/`.
4. **API**: Pydantic schemas (inherit `APIModelBase`), converter functions, routes returning models; add providers in `src/api/dependencies/providers.py`; include the router in `main.py`.

---

## 8. Testing

Tests live in `tests/` and mirror `src/`.

### Use Case Tests
- Mock collaborators with `AsyncMock(spec=UserRepository)` / `MagicMock(spec=PasswordHasher)` — `spec` against the Protocol surfaces the real method names.
- `asyncio_mode = "auto"` is configured; no `@pytest.mark.asyncio` needed.

### Route Tests
- Create a minimal `FastAPI()`, include only the router under test. **Never import `src/main.py`.**
- Override the use-case provider and the auth guard with `app.dependency_overrides`:
  ```python
  app.dependency_overrides[get_user_use_case] = lambda: AsyncMock(spec=UserUseCase)
  app.dependency_overrides[get_current_user] = lambda: TokenClaimsDTO(user_id=1, role=UserRole.ADMIN)
  ```
- Use `httpx.AsyncClient` with `ASGITransport`.

| Layer | File | Test? |
|-------|------|-------|
| Application | `<entity>_use_case.py` | Yes — mock the repository port |
| Application | `<entity>_converter.py` | Yes |
| API | `<entity>_converter.py` | Yes |
| API | `<entity>_routes.py` | Yes — override providers |
| Infrastructure | repository adapter | No — needs a live DB (integration only) |

---

## 9. Documentation & Code Style

- Module, class, and `__init__`/public-method docstrings required (Google style). Port (Protocol) methods carry the documented contract; adapters don't repeat it.
- Max line length: **80 characters**. Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/` after every change.
- Always use `uv run`. Modern type annotations (`list[X]`, `X | None`). All DB I/O is async. API prefix: `/api/v1`.

---

## 10. Anti-Patterns

- Don't introduce an IoC container or `@inject` — wire dependencies with FastAPI `Depends` providers.
- Don't keep session (or other control-flow) state in a module-global `ContextVar`. Inject the request-scoped `AsyncSession`.
- Don't pass the `AsyncSession` to use cases, or sessions to repository constructors as constants — adapters get the request session via the provider.
- Don't return `JSONResponse(model.model_dump())` from routes — return the model and let FastAPI serialise it; set `response.status_code` for dynamic codes.
- Don't make ports ABCs — use `typing.Protocol`; don't suffix ports with `Base`.
- Don't create classes of only `@staticmethod`s — use module functions.
- Don't bypass use cases — routes never call repositories directly.
- Don't let Domain import from Infrastructure or API.
- Don't create entity-specific result enums or wrapper collection DTOs.
- Don't scatter entity files into flat shared directories.

---

## 11. Keeping Quick-Reference Files in Sync

`AGENT.md` is the single source of truth. The quick-reference files below mirror its critical rules and must be updated together: [.clinerules](.clinerules), [.cursorrules](.cursorrules), [.windsurfrules](.windsurfrules), [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md), [.antigravity/rules.md](.antigravity/rules.md), [.github/copilot-instructions.md](.github/copilot-instructions.md).
