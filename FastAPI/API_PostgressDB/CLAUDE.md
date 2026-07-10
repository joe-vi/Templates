# Claude Code — Codebase Instructions

## Mandatory: Read AGENT.md Before Every Task

Before writing, editing, or reviewing any code in this repository, read the full contents of
[AGENT.md](AGENT.md). It is the single source of truth for all architecture rules, naming
conventions, patterns, and anti-patterns. **These rules override any general defaults.**

## Architecture (Clean Architecture — 4 Layers)

```
API → Infrastructure → Application → Domain   (dependencies point inward only)
```

Domain never imports from any other layer. The composition root is `AppModule` in
`src/api/dependencies/providers.py` (injector + in-house `TypedBinder`/request scope in
`typed_binder.py`/`request_scope.py`) — one line binds implementation, port, and scope, and a mismatched
implementation is a mypy error at that line. No graph-completeness validation: a missing
binding fails at runtime on first resolution (accepted).

| Layer | Location | Key Rule |
|---|---|---|
| Domain | `src/domain/` | Entities, repository ports (Protocols), enums. No external deps. |
| Application | `src/application/` | Use cases, DTOs, converter functions, service ports (Protocols). Imports Domain only. |
| Infrastructure | `src/infrastructure/` | DB models, repository/auth/logging adapters, engine + session. |
| API | `src/api/` | Routes, schemas, converters, dependency providers. Wires adapters to ports. |

## Critical Rules (Quick Reference)

### Naming
- **Ports are `typing.Protocol`s with clean names** (`UserRepository`, `PasswordHasher`, `TokenService`, `Logger`, `UserContext`) — no `Base` suffix.
- **Adapters are mechanism-qualified** (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`, `RequestUserContext`).
- Use cases are plain concrete classes (`UserUseCase`, `AuthUseCase`) — no separate interface.
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult`.
- DTOs: Pydantic models inheriting `DTOBase` (`src/application/dto_base.py`; frozen, camelCase aliases on the wire) with `DTO` suffix; validation rules live on the DTOs; use `list[UserDTO]` directly.
- **No per-entity API schemas or API converters**: routes accept/return DTOs directly (`response_model=UserDTO`); only the generic operation envelopes in `api/schemas/operation_schema.py` remain (also `DTOBase`).
- Converters are **module functions**, not static-method classes.
- Booleans read like questions (`is_active`); no abbreviations (`repository` not `repo`).

### Dependency Injection (FastAPI `Depends`)
- Composition root: `AppModule.configure()` uses `TypedBinder` — `typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository, scope=request)`; wrong implementation for a port = mypy error. Concrete classes: `bind_self_typed(UserUseCase, scope=request)`.
- Scopes: `singleton` (engine, stateless services) and `request` (session, repositories, transaction context, use cases). Request-scope state lives in a ContextVar; entered per request by the `request_context` middleware; disposes objects on exit (LIFO, `aclose()` preferred, async `close()` awaited).
- **`@inject` required** on every implementation whose `__init__` takes dependencies (auto-wiring). Construction logic lives in `@provider` methods on `AppModule`.
- Routes/guards resolve via `Annotated[UseCase, Injected(UseCase)]` (thin `Depends` over `app.state.injector`).
- Tests: bind mock instances in a `TestModule` and set `app.state.injector = Injector([TestModule()])`; `app.dependency_overrides` for plain guards.

### Session, Transactions & Repositories
- The engine + `async_sessionmaker` are singleton `@provider` methods; the engine is disposed in `lifespan` shutdown.
- The `AsyncSession` is a **request-scoped `@provider` method**; every repository and the transaction context in one request share it, and the scope teardown closes it via `aclose()`. Repositories receive the session by constructor — never via ambient state.
- Repository **adapters receive the `AsyncSession`** via constructor and **never commit or roll back**. Mutations `flush()`/`execute()` and map DB errors to result enums (`IntegrityError`→`UNIQUE_CONSTRAINT_ERROR`; deadlock→`CONCURRENCY_ERROR`; else `FAILURE`). Reads just query. `flush()` populates `id`/server defaults via RETURNING — no `session.refresh()`.
- **The use case owns the transaction boundary** via the `TransactionContext` port (adapter `SqlAlchemyTransactionContext`): wrap mutations in `async with self._transaction_context.begin() as transaction:`; call `await transaction.commit()` only when every operation succeeded. Rollback-unless-committed.
- **Atomic multi-repository operations**: call several repositories inside one `begin()` block — they share the request session and succeed or fail together.
- One CRUD operation per repository method.

### Routes & Responses
- Routes **return the response model**; FastAPI serialises it (camelCase). Never return `JSONResponse(model.model_dump())`.
- For result-dependent status, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, return the model. Use `HTTPException` for not-found / auth failures.

### Auth
- `get_current_user` decodes the Bearer JWT, raises 401, populates the request-scoped `UserContext`, records the user id in the logging context, returns `TokenClaimsDTO`. Protect routers with `dependencies=[Depends(get_current_user)]`.
- `UserContext` port (adapter `RequestUserContext`, `request` scope): inject into use cases/services needing the caller's identity (auditing, roles/permissions). `populate()` once by the guard — second call raises; unpopulated reads raise. Pass scalar values to repositories, never the context object.
- Log correlation (`request_id`, `user_id`) lives in context vars in `src/infrastructure/logging/log_context.py` (set by the request-id middleware and the guard).

### Database
- All constraints **must** have an explicit `name` (`uq_`, `fk_`, `ck_`, `ix_` prefix).
- `id`, `created_at` are DB-generated — never set in Python; `flush()` RETURNING populates them (no `session.refresh()`).
- All DB operations are async.

### Enums
- `StrEnum` (3.11+), lowercase values matching DB storage; all enums in `src/domain/enums/`.

### Code Style
- Max line length: **80 characters**. Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/` after every change.
- Always use `uv run`. API prefix: `/api/v1`.

### Testing
- Use case tests: `AsyncMock(spec=UserRepository)` for the repository port.
- Route tests: minimal `FastAPI()` + `app.dependency_overrides` for the use-case provider and `get_current_user` — never import `src/main.py`.
- `asyncio_mode = "auto"` is configured (no `@pytest.mark.asyncio`).

### Anti-Patterns (Never)
- Do not wire bindings outside `AppModule.configure()`, and always bind through `TypedBinder`.
- Do not omit `@inject` on implementations whose `__init__` takes dependencies — resolution fails with `TypeError`.
- Do not let repositories consult ambient state for the session; it is injected by constructor.
- Do not pass sessions to use cases.
- Do not commit or roll back inside repositories — the use case owns the boundary via `TransactionContext`.
- Do not call `transaction.commit()` after any failed result in the block.
- Do not return `JSONResponse(model.model_dump())` from routes.
- Do not make ports ABCs or suffix them `Base`; use `Protocol`.
- Do not create classes of only static methods; use module functions.
- Do not bypass use cases — routes never call repositories directly.
