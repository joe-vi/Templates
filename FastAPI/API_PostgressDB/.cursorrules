# Cursor / Antigravity — Codebase Instructions

## Mandatory: Read AGENT.md Before Every Task

Before writing, editing, or reviewing any code in this repository, read the full contents of
AGENT.md. It is the single source of truth for all architecture rules, naming conventions,
patterns, and anti-patterns. **These rules override any general defaults.**

## Architecture (Clean Architecture + DDD — 4 Layers)

Dependency direction: API → Infrastructure → Application → Domain (inward only). Domain never
imports from any other layer. The composition root is `AppModule` in
`src/api/dependencies/providers.py`, built on injector plus the in-house DI machinery in
`src/infrastructure/di/` (`request_scope.py`, `typed_binder.py`) and the FastAPI accessor
`src/api/dependencies/injected.py`: one line binds implementation, port, and scope, and a
mismatched implementation is a pyrefly error at that line. No graph-completeness validation — a
missing binding fails at runtime on first resolution (accepted trade-off).

- Domain (`src/domain/`): Entities (aggregate roots with invariants + behaviour), repository ports (Protocols), enums. No external deps.
- Application (`src/application/`): Use cases (concrete classes), DTOs, converter functions, service ports (Protocols). Imports Domain only.
- Infrastructure (`src/infrastructure/`): DB models, repository/auth/logging adapters, engine + session, DI machinery (`di/`).
- API (`src/api/`): Routes, operation envelopes, composition root. Wires adapters to ports in `dependencies/`.

## Critical Rules (Quick Reference)

### Domain-Driven Design
- Entities are aggregate roots with behaviour — invariants enforced in `__post_init__` (raise `ValueError`), state transitions via intention-revealing methods (`User.activate()`, `User.deactivate()`, `User.is_active`). NEVER an anemic domain: business rules for one aggregate live ON the entity; use cases orchestrate only.
- One repository port per aggregate root, defined in Domain. A targeted single-column update (e.g. `update_role`) is acceptable ONLY when no domain rule guards the change; otherwise load → entity behaviour → persist.
- Ubiquitous language everywhere; Domain imports nothing but stdlib (`dataclasses`, `enum`, `typing`).
- DTO validation guards input shape at the boundary; entity invariants are the last line of defence.
- Domain entities get pure unit tests in `tests/domain/` — no mocks, no I/O.

### Naming
- Ports are `typing.Protocol`s with clean names (`UserRepository`, `PasswordHasher`, `TokenService`, `Logger`, `UserContext`) — NO `Base` suffix.
- Adapters are mechanism-qualified (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`, `RequestUserContext`).
- Use cases are one plain concrete class per operation in its own file, each with a single `execute` method (`CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`, ...) — no separate interface; each declares only the ports its operation needs, and routes and tests depend on the concrete class (mock with `AsyncMock(spec=CreateUserUseCase)`).
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult`.
- DTOs: Pydantic models inheriting `DTOBase` (`src/application/dto_base.py`; frozen, camelCase aliases on the wire, accepts either case in), `DTO` suffix; validation rules (`EmailStr`, `min_length`, ...) live on the DTOs; return `list[UserDTO]` directly, never a wrapper DTO.
- NO per-entity API schemas or API converters: routes accept/return DTOs directly (`response_model=UserDTO`); only the generic operation envelopes in `api/schemas/operation_schema.py` remain (also inherit `DTOBase`).
- Converters are module functions, NOT classes of static methods.
- Booleans read like questions (`is_active`); no abbreviations (`repository` not `repo`).

### Documentation (single source, IDE hover)
- NO module docstrings or top-of-file comments anywhere.
- The contract is documented ONCE, on the port: Protocol classes/methods carry full Google-style docstrings. Adapters explicitly subclass their port (`class SqlAlchemyUserRepository(UserRepository):`) and inherit them — never repeat method docstrings in adapters; IDE hover resolves the port docs through the MRO.
- Adapter classes keep a short class docstring for mechanism-specific notes only; no `__init__` docstrings.
- Classes with no port — the use cases — carry their own method docstrings: they ARE the single source.
- Standalone public functions (converters, providers, guards, routes) keep their own docstrings; route docstrings become OpenAPI descriptions.

### Dependency Injection (injector + TypedBinder)
- Composition root: `AppModule.configure()` in `src/api/dependencies/providers.py` using the `TypedBinder` facade — one line per binding: `typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository, scope=request)`. A wrong implementation for a port is a pyrefly error at that line. Concrete classes (use cases): one `bind_self_typed(CreateUserUseCase, scope=request)` line per operation.
- Scopes: `singleton` (engine, stateless services) and `request` (session, repositories, transaction context, use cases). Request-scope state lives in a ContextVar; the scope is entered per request by the middleware in `main.py` and disposes its objects on exit (LIFO; `aclose()` preferred, async `close()` awaited).
- `@inject` REQUIRED on every implementation whose `__init__` takes dependencies (injector auto-wires from type hints; omitting it is a runtime `TypeError`). Construction logic lives in `@provider` methods on `AppModule`.
- Routes/guards resolve via `Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]` — a thin Depends over `app.state.injector`.
- NO graph-completeness validation: a missing binding fails at runtime on first resolution.
- Tests: bind mock instances in a `TestModule` (`binder.bind(CreateUserUseCase, to=mock)`), set `app.state.injector = Injector([TestModule()])`; `app.dependency_overrides` for plain guards.

### Session, Transactions & Repository Pattern
- Engine + `async_sessionmaker` are singleton `@provider` methods on `AppModule`; the engine is disposed in `lifespan` shutdown.
- The `AsyncSession` is a request-scoped `@provider` method — every repository and the transaction context in one request share it, and the scope teardown closes it via `aclose()`. Repositories receive the session by constructor, never via ambient state.
- Repository adapters receive the `AsyncSession` via constructor and NEVER commit or roll back. One CRUD operation per method.
- Mutations `flush()`/`execute()` and map DB exceptions to result enums (`IntegrityError`→`UNIQUE_CONSTRAINT_ERROR`; deadlock→`CONCURRENCY_ERROR`; else `FAILURE`). Reads just query. `flush()` populates `id`/server defaults via RETURNING — no `session.refresh()`.
- The use case owns the transaction boundary via the `TransactionContext` port (adapter `SqlAlchemyTransactionContext`): wrap mutations in `async with self._transaction_context.begin() as transaction:` and call `await transaction.commit()` only when every operation succeeded. Rollback-unless-committed.
- Atomic multi-repository operations: call several repositories inside ONE `begin()` block — they share the request session and succeed or fail together.

### Routes & Responses
- Routes return the response MODEL; FastAPI serialises it (camelCase). Never return `JSONResponse(model.model_dump())`.
- For result-dependent status, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, return the model. Use `HTTPException` for not-found / auth failures.
- URL shape is `/api/<entity>/<version>/<path>` (e.g. `/api/users/v1`, `/api/auth/v1/login`). `/api` is the base on the domain router's `prefix`; the `/<entity>/v1` segment rides on each `router.include_router(op.router, prefix="/<entity>/v1")` call, so the version is per-endpoint (bump one endpoint to `/<entity>/v2` without touching others). Operation files use resource-relative paths (`""` for the collection root, `/{id}` for item routes) and never repeat the entity or version. Do NOT collapse the segment onto the router's own `prefix` — FastAPI rejects including a prefix-less router that has an empty collection-root path.

### Auth
- `get_current_user` decodes the Bearer JWT, raises 401, populates the request-scoped `UserContext`, records the user id in the logging context, returns `TokenClaimsDTO`. Protect routers with `dependencies=[Depends(get_current_user)]`.
- `UserContext` port (adapter `RequestUserContext`, `request` scope): inject into use cases/services needing the caller's identity (auditing, roles/permissions). `populate()` once by the guard — a second call raises; unpopulated reads raise. Pass scalar values to repositories, never the context object.
- Log correlation (`request_id`, `user_id`) lives in context vars in `src/infrastructure/logging/log_context.py`.

### Database
- All constraints MUST have an explicit `name` (`uq_`, `fk_`, `ck_`, `ix_` prefix).
- `id`, `created_at` are DB-generated — never set in Python; `flush()` RETURNING populates them (no `session.refresh()`).
- All DB operations are async.

### Enums
- `StrEnum` (3.11+), lowercase values matching DB storage; all enums in `src/domain/enums/`.

### Code Style
- Max line length: 140 characters (`skip-magic-trailing-comma = true` — the formatter uses the full width). Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/` after every change. Run `uv run pyrefly check` to type-check.
- Always use `uv run`. URL shape: `/api/<entity>/<version>/<path>` (e.g. `/api/users/v1`) — `/api` base on the domain router, `/<entity>/v1` on each `include_router` call so the version is per-endpoint.
- **Never introduce a lint/type-check suppression** (`# noqa`, `# type: ignore`, pyrefly ignore comments, or equivalent) **without checking with the user first.** If satisfying a rule would require one, stop and present the design alternatives that avoid it instead of silently suppressing.

### Testing
- Domain: pure entity unit tests in `tests/domain/` (no mocks).
- Use case tests: `AsyncMock(spec=UserRepository)` for the repository port; `FakeTransactionContext` asserting commit-on-success / no-commit-on-failure.
- Route tests: minimal `FastAPI()` + `app.state.injector = Injector([TestModule()])` binding mock instances (`AsyncMock(spec=CreateUserUseCase)`), plus `app.dependency_overrides` for `get_current_user` — never import `src/main.py`.
- DI machinery tests live in `tests/infrastructure/di/`.
- `asyncio_mode = "auto"` is configured (no `@pytest.mark.asyncio`).

### Anti-Patterns (Never)
- Do not leave the domain anemic — invariants and state transitions belong on the entity.
- Do not wire bindings outside `AppModule.configure()`; always bind through `TypedBinder`.
- Do not omit `@inject` on implementations whose `__init__` takes dependencies — resolution fails with `TypeError`.
- Do not keep session state in a module-global `ContextVar`; inject the request-scoped session.
- Do not pass sessions to use cases.
- Do not commit or roll back inside repositories — the use case owns the boundary via `TransactionContext`.
- Do not call `transaction.commit()` after any failed result in the block.
- Do not return `JSONResponse(model.model_dump())` from routes.
- Do not make ports ABCs or suffix them `Base`; use `Protocol`.
- Do not duplicate docstrings on adapters — the port is the single documented contract.
- Do not write module docstrings or file header comments.
- Do not create classes of only static methods; use module functions.
- Do not bypass use cases — routes never call repositories directly.
- Do not add `# noqa`, `# type: ignore`, or any other lint/type suppression without checking with the user first — propose a design that avoids the violation instead.
