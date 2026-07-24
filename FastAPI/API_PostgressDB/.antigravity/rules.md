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
missing binding fails at runtime on first resolution.

- Domain (`src/domain/`): Entities (aggregate roots with invariants + behaviour), repository ports (Protocols), enums. No external deps.
- Ports (`src/ports/`): technical service ports (Protocols) — `transaction_context`, `logger`, `password_hasher`, `token_service`, `user_context` — plus any type a port returns (`TokenClaims`). A leaf importing only Domain enums and `src/shared/`; every layer except Domain may import it.
- Application (`src/application/`): Use cases (concrete classes), request/response contracts, converter functions. Imports Domain + Ports.
- Infrastructure (`src/infrastructure/`): DB models, repository/auth/logging adapters, engine + session, DI machinery (`di/`).
- API (`src/api/`): Routes, operation envelopes, composition root. Wires adapters to ports in `dependencies/`.

## Critical Rules (Quick Reference)

### Domain-Driven Design
- Entities are aggregate roots with behaviour — invariants enforced in `__post_init__` (raise `ValueError`), state transitions via intention-revealing methods (`User.activate()`, `User.deactivate()`, `User.is_active`). NEVER an anemic domain: business rules for one aggregate live ON the entity; use cases orchestrate only.
- One repository port per aggregate root, defined in Domain. A targeted single-column update (e.g. `update_role`) is acceptable ONLY when no domain rule guards the change; otherwise load → entity behaviour → persist.
- Ubiquitous language everywhere; Domain imports nothing but stdlib (`dataclasses`, `enum`, `typing`).
- `*Request` validation guards input shape at the boundary; entity invariants are the last line of defence.
- Domain entities get pure unit tests in `tests/domain/` — no mocks, no I/O.

### Naming
- Ports are `typing.Protocol`s with clean names (`UserRepository`, `PasswordHasher`, `TokenService`, `Logger`, `UserContext`) — NO `Base` suffix.
- Adapters are mechanism-qualified (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`, `RequestUserContext`).
- Use cases are one plain concrete class per operation in its own file, each with a single `execute` method (`CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`, ...) — no separate interface; each declares only the ports its operation needs, and routes and tests depend on the concrete class (mock with `AsyncMock(spec=CreateUserUseCase)`).
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult`.
- **NEVER name a model `DTO`.** Wire models are named for their role and live in `src/application/use_cases/<entity>/<entity>_contracts.py`, inheriting `ContractModel` (`src/shared/contract_model.py`) directly — it carries frozen + camelCase-on-the-wire + either-case-in. There is no intermediate marker base.
  - `<Operation>Request` — what FastAPI binds as the body (`LoginRequest`, `CreateUserRequest`); validation (`EmailStr`, `min_length`, ...) lives here.
  - `<Entity>Response` — what a route returns (`UserResponse`, `TokenResponse`); return `list[UserResponse]` directly, never a wrapper.
  - Only use the suffix if the model IS that body. Non-wire types get plain names (`TokenClaims`) and live beside whatever produces them — `TokenClaims` sits in `src/ports/token_service.py`, so Ports never imports Application.
  - No model just to group a use case's arguments: pass scalars (`execute(user_id, role)`), as `GetUserUseCase.execute(user_id)` already does.
- NO per-entity API schemas or API converters: routes accept/return the contracts directly (`response_model=UserResponse`). The only API-layer schemas are the generic operation envelopes in `api/schemas/operation_schema.py` (they inherit `ContractModel` too).
- Converters are module functions, NOT classes of static methods; names state the direction (`to_response`, `to_response_list`, `to_entity`).
- Booleans read like questions (`is_active`); no abbreviations (`repository` not `repo`).

### Documentation (single source, IDE hover)
- NO module docstrings or top-of-file comments anywhere.
- The contract is documented ONCE, on the port: Protocol classes/methods carry **concise** docstrings — a one-line summary plus `Args`/`Returns`/`Raises` only, never implementation details, rationale, or usage examples. Adapters explicitly subclass their port (`class SqlAlchemyUserRepository(UserRepository):`) and inherit them — never repeat method docstrings in adapters; IDE hover resolves the port docs through the MRO.
- Adapter classes keep a short class docstring for mechanism-specific notes only; no `__init__` docstrings.
- Classes with no port — the use cases — carry their own method docstrings: they ARE the single source.
- Standalone public functions (converters, providers, guards, routes) keep their own docstrings; route docstrings become OpenAPI descriptions.

### Dependency Injection (injector + TypedBinder)
- Composition root: `AppModule.configure()` in `src/api/dependencies/providers.py` using the `TypedBinder` facade — one line per binding: `typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository)`. A wrong implementation for a port is a pyrefly error at that line. Concrete classes (use cases): one `bind_self_typed(CreateUserUseCase)` line per operation. `AppModule.configure()` holds the cross-cutting binds and delegates each domain's repository + use-case binds to a `register(typed_binder)` function in `src/api/dependencies/bindings/<domain>.py` (API layer, so it may import the adapters; bind through `TypedBinder` — never plain tuples, which drop the static check).
- Scopes chosen by what holds request state: `singleton` (engine, `async_sessionmaker`, stateless services), `request` (the write unit of work `SqlAlchemyTransactionContext`, logger, user context), and **transient** (no scope) for stateless orchestrators — use cases, repositories, and the `ConnectionFactory` adapter. The transaction context is request-scoped and bound to **both** itself and the `TransactionContext` port via two `@request @provider` methods returning the same instance, so a use case's `begin()` and a repository's `write()` nest on one write session. There is **no** request-scoped `AsyncSession`. The scope is entered per request by `RequestScopeMiddleware` (`src/api/middleware/request_scope_middleware.py`) and disposes its objects on exit (LIFO; `aclose()` preferred, async `close()` awaited); it spans background tasks and streaming bodies too.
- `@inject` REQUIRED on every implementation whose `__init__` takes dependencies (injector auto-wires from type hints; omitting it is a runtime `TypeError`). Construction logic lives in `@provider` methods on `AppModule`.
- Routes/guards resolve via `Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]` — a thin Depends over `app.state.injector`.
- NO graph-completeness validation: a missing binding fails at runtime on first resolution.
- Tests: bind mock instances in a `TestModule` (`binder.bind(CreateUserUseCase, to=mock)`), set `app.state.injector = Injector([TestModule()])`; `app.dependency_overrides` for plain guards.

### Session, Transactions & Repository Pattern
- Engine + `async_sessionmaker` are singleton `@provider` methods on `AppModule`; the engine is disposed in `lifespan` shutdown. There is **no** request-scoped `AsyncSession`.
- **Repositories get sessions through a `ConnectionFactory`** (`src/infrastructure/database/connection_factory.py`; adapter `SqlAlchemyConnectionFactory`) — an infrastructure-internal seam (not a hexagonal port; it exposes an `AsyncSession` directly and is consumed only by repositories). `read()` yields a fresh short-lived session, closed on block exit (connection returned immediately). `write()` yields the request write unit of work owned by `SqlAlchemyTransactionContext`, opening or (same task) joining it.
- **The write unit of work is owned by `SqlAlchemyTransactionContext`**, injected with the `async_sessionmaker` (not a session). The active unit lives in a per-task `contextvars.ContextVar[_WriteUnit | None]` (session + `rolled_back` flag). Outermost `begin()`: create session, `await session.begin()`, **auto-commit on clean exit**, rollback on escaping exception, always `close()`. Nested `begin()` (same task) **joins** the unit; a DB error there rolls the **whole** unit back and marks it dead; a further `begin()` on a dead unit **raises** (fail-fast — no write runs on an aborted transaction, no phantom success).
- Repository adapters inject `ConnectionFactory`, wrap reads in `read()` and writes in `write()`, and NEVER commit or roll back. Put the `try`/`except` **outside** the `write()` block so the context rolls the unit back before the error is translated. One CRUD operation per method.
- Mutations `flush()`/`execute()` and map DB exceptions to result enums (`IntegrityError`→`UNIQUE_CONSTRAINT_ERROR`; deadlock→`CONCURRENCY_ERROR`; else `FAILURE`). Reads just query. `flush()` populates `id`/server defaults via RETURNING — no `session.refresh()`.
- **No `commit()`.** `Transaction` has no `commit()`; the outermost `begin()` commits on a clean exit. A **single** repository write self-commits, so a **single-write use case drops the transaction context** and calls the repository directly. A use case opens `begin()` **only** for **multi-write** atomicity; an early `return` inside `begin()` now commits unless you rolled back first. On a benign non-success result (raises no exception), `await transaction.rollback()` before returning to abort the unit.
- **Reads happen before the write unit, never inside it.** A repository read runs on its own short-lived `read()` session, so a `begin()` block holds **only writes** — do all loading first, then open `begin()`. Never call a repository read inside a `begin()` block (it checks out a second pooled connection while the write connection is held). A single persist self-commits and needs no `begin()`.
- Atomic multi-repository operations: do the reads first, then call the several repository writes inside ONE `begin()` block — they share the unit's session and commit together on clean exit or roll back together on the first failure.

### Routes & Responses
- Routes return the response MODEL; FastAPI serialises it (camelCase). Never return `JSONResponse(model.model_dump())`.
- For result-dependent status, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, return the model. Use `HTTPException` for not-found / auth failures.
- URL shape is `/api/<entity>/<version>/<path>` (e.g. `/api/users/v1`, `/api/auth/v1/login`). `/api` is the base on the domain router's `prefix`; the `/<entity>/v1` segment rides on each `router.include_router(op.router, prefix="/<entity>/v1")` call, so the version is per-endpoint (bump one endpoint to `/<entity>/v2` without touching others). Operation files use resource-relative paths (`""` for the collection root, `/{id}` for item routes) and never repeat the entity or version. Do NOT collapse the segment onto the router's own `prefix` — FastAPI rejects including a prefix-less router that has an empty collection-root path.

### Error Handling
- Failures are reported in ONE place: the `exception_handler` middleware (`src/api/middleware/exception_handler_middleware.py`), registered first so it is innermost. It catches anything escaping a route, logs it as `request.unhandled_exception` through the request-scoped `Logger` (traceback, `method`, `path`, `request_id`, `user_id`), and returns `500 {"detail": "Internal Server Error"}`. The body stays opaque — detail belongs in the correlated log. Because it sits inside `access_log` and `request_id`, a failed request still gets its `request.completed` entry and `X-Request-ID` header.
- **Use `try`/`except` ONLY when the `except`/`finally` block does real work the middleware cannot** — work specific to that call site, which either *translates* the failure into the layer's vocabulary or *undoes* something. Legitimate: repositories mapping `IntegrityError`/`DBAPIError` to result enums; `SqlAlchemyTransactionContext.begin` rolling back then re-raising; `JwtTokenService.decode_token` returning `None` on `InvalidTokenError`; the request-scope teardown logging a failed `aclose()` so the rest still run.
- Never catch merely to report: a block that only logs and re-raises, wraps the exception, or hand-builds a 500 duplicates the middleware — delete it and let the exception propagate. Same for `except: raise` and a `finally` that adds nothing.
- Never catch to produce an `HTTPException`. Routes raise `HTTPException` for outcomes they *expect* and detect themselves (not-found, auth failure), never as a translation of a caught unexpected exception.
- Never catch `Exception` to continue with a default unless that default is a real result (a result enum, `None` from a decode) — swallowing an error behind a plausible success hides it from the log and the caller.
- No `try` needed for rollback in a use case: leaving a `begin()` block by exception already rolls back, and the exception continues to the middleware.
- **A `BackgroundTasks` callable is the one place that MUST catch for itself.** It runs after the response is sent, so its exception escapes `exception_handler` entirely (re-raised past a `dispatch` that already returned), reaching uvicorn as a bare `Exception in ASGI application` with NO `request_id`/`user_id`. Wrap the task body and log through the injected `Logger` — it is the only reporter that task gets.

### Middleware
- One concern per module in `src/api/middleware/<concern>_middleware.py`; `register(app)` in `registration.py` is the ONLY place middlewares are added and owns the ordering. Starlette runs the most recently registered first, so the outermost is registered LAST.
- Order (innermost → outermost): `exception_handler`, `access_log`, `request_id`, `RequestScopeMiddleware`. Any middleware resolving a request-scoped binding must be registered BEFORE `RequestScopeMiddleware`.
- Default shape is a `BaseHTTPMiddleware` dispatch function (`async def <concern>(request, call_next)`, added via `app.middleware("http")(...)`).
- **`RequestScopeMiddleware` is deliberately a pure ASGI class** (`__call__(self, scope, receive, send)`, added via `app.add_middleware(...)`). **NEVER convert it to a dispatch function**: `call_next` returns when the response *starts*, so the scope would dispose its request-scoped collaborators (the write unit of work, the `Logger`, the `UserContext`) while `BackgroundTasks` and streaming bodies still run — silently, since anyio's context copy still resolves the same disposed instances. Regression tests: `tests/api/middleware/test_request_scope_middleware.py`.
- `BackgroundTasks` and streaming bodies run INSIDE the request scope. Their own DB work is a new unit of work needing its own `write()`/`begin()` block; genuinely separate units of work belong in a task queue.
- **Reads no longer pin the pooled connection.** `ConnectionFactory.read()` closes its session on block exit, so a `SELECT`'s autobegun transaction ends and the connection returns to the pool immediately — the old read-route background-task trap is largely dissolved and reads need no `begin()` wrapper. A write still commits (freeing the connection) before a background task starts, so the task inherits a clean session.

### Auth
- `get_current_user` decodes the Bearer JWT, raises 401, populates the request-scoped `UserContext`, returns `TokenClaims` (from `src/ports/token_service.py`). Protect routers with `dependencies=[Depends(get_current_user)]`. (The bound logger reads `user_id` from `UserContext`; the guard touches no logging state.)
- `UserContext` port (adapter `RequestUserContext`, `request` scope): inject into use cases/services needing the caller's identity (auditing, roles/permissions). `populate()` once by the guard — a second call raises. Reads never raise: `user_id`/`role` return `None` when unauthenticated; only guarded routes guarantee non-`None`, so check the value you use rather than a separate flag. Pass scalar values to repositories, never the context object.
- Logging is a **bound logger**: `JsonLogger` is request-scoped; the `request_id` middleware (`src/api/middleware/request_id_middleware.py`) mints (or accepts an inbound `X-Request-ID`) and calls `bind_request_id` once (raises on a second call), echoing it back as the `X-Request-ID` response header, and `user_id` is read from the injected `UserContext`.
- **One format for the whole process**: `configure_logging()` (from `main.lifespan`) installs the JSON handler on the **root** logger — app, uvicorn, and third-party records all propagate into it, each tagged with a `logger` field. Root at `WARNING`, `app` at `settings.log_level`. `uvicorn.access` is disabled; the `access_log` middleware (`src/api/middleware/access_log_middleware.py`) emits the correlated `request.completed` entry instead, carrying `method`, `path`, `status_code`, `duration_ms`, `request_id`, and `user_id`. It sits just outside `exception_handler`, so every request — failures included — produces exactly one entry.

### Database
- All constraints MUST have an explicit `name` (`uq_`, `fk_`, `ck_`, `ix_` prefix).
- **Driver-error classification is shared, not per-repository.** How a `DBAPIError` is recognised (unwrapping `__cause__` to an `asyncpg` error type) is identical for every aggregate, so it lives once in `src/infrastructure/database/errors.py` (`is_deadlock`) and every adapter imports it. Only the mapping to a result enum is per-method (the enum differs). Never re-implement the `isinstance(exc.__cause__, ...)` check in an adapter — add the next classifier to that module.
- `id`, `created_at` are DB-generated — never set in Python; `flush()` RETURNING populates them (no `session.refresh()`).
- All DB operations are async.

### Enums
- `StrEnum` (3.11+), lowercase values matching DB storage; all enums in `src/domain/enums/`.

### Code Style
- Max line length: 140 characters (`skip-magic-trailing-comma = true` — the formatter uses the full width). Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/` after every change. Run `uv run pyrefly check` to type-check.
- Always use `uv run`. URL shape: `/api/<entity>/<version>/<path>` (e.g. `/api/users/v1`) — `/api` base on the domain router, `/<entity>/v1` on each `include_router` call so the version is per-endpoint.
- **Never introduce a lint/type-check suppression** (`# noqa`, `# type: ignore`, pyrefly ignore comments, or equivalent) **without checking with the user first.** If satisfying a rule would require one, stop and present the design alternatives that avoid it instead of silently suppressing.
- **One level of abstraction per method.** A method reads as a sequence of named steps; each nameable sub-goal inside it (building a value, classifying an error, checking a precondition) is extracted into a helper named for that sub-goal — a module-level `_` function when the logic is pure (`_to_entity`, `_is_deadlock`), a `_`-prefixed method when it needs `self`. The trigger is a nameable sub-goal, not a line count: if you could write a comment above a block saying what it accomplishes, that comment is the helper's name. Helpers take no docstrings. Don't extract a single expression its variable already names — the test is whether the caller reads better with the block gone.

### Testing
- Domain: pure entity unit tests in `tests/domain/` (no mocks).
- Use case tests: `AsyncMock(spec=UserRepository)` for the repository port. A single-write use case has no transaction context — assert the repository result is forwarded. A multi-write use case gives its test a small local `FakeTransactionContext` (commit-on-clean-exit, rollback on exception or `rollback()`) — assert **not rolled back on success / rolled back on failure** (there is no `commit()`). The template ships no multi-write use case, so it carries no such fake; unit-of-work behaviour is integration-tested over a real `SqlAlchemyConnectionFactory` on aiosqlite (incl. the poisoned-unit fail-fast).
- Route tests: minimal `FastAPI()` + `app.state.injector = Injector([TestModule()])` binding mock instances (`AsyncMock(spec=CreateUserUseCase)`), plus `app.dependency_overrides` for `get_current_user` — never import `src/main.py`.
- DI machinery tests live in `tests/infrastructure/di/`.
- Architecture fitness test: `tests/architecture/test_layer_dependencies.py` parses every `src/` module's imports (AST) and fails on any inward-only dependency breach or any third-party import in Domain/Ports (Application must not import `sqlalchemy`/`fastapi`) — the executable clean-architecture guardrail; extend its rule tables for a new layer or allowed edge.
- `asyncio_mode = "auto"` is configured (no `@pytest.mark.asyncio`).

### Anti-Patterns (Never)
- Do not leave the domain anemic — invariants and state transitions belong on the entity.
- Do not wire bindings outside the composition root (`AppModule.configure()` or the per-domain `register()` functions in `src/api/dependencies/bindings/` it calls); always bind through `TypedBinder` (never plain tuples). Keep binding modules in the API layer — never in `src/application/`.
- Do not omit `@inject` on implementations whose `__init__` takes dependencies — resolution fails with `TypeError`.
- Do not keep session state in a **module-global** `ContextVar`; repositories get sessions through the injected `ConnectionFactory` (the transaction context's per-task `ContextVar` is an instance member of the request-scoped adapter, not module-global).
- Do not pass an `AsyncSession` to a use case or a repository constructor; repositories get sessions through the injected `ConnectionFactory`.
- Do not commit or roll back inside repositories — the transaction context owns the boundary (auto-commit on clean exit).
- Do not re-implement driver-error classification per repository — import `is_deadlock` from `src/infrastructure/database/errors.py`.
- Do not call `commit()` from a use case — there is none; the outermost `begin()` commits on clean exit. Abort with `await transaction.rollback()` or by letting an exception propagate.
- Do not return `JSONResponse(model.model_dump())` from routes.
- Do not write a `try`/`except` whose block only logs, re-raises, wraps, or hand-builds a 500 — the `exception_handler` middleware does that once for every route. Catch only to translate a failure (to a result enum, to `None`) or to undo work (rollback), never to swallow an error behind a fake success. Exception: a `BackgroundTasks` callable must catch and log for itself.
- Do not rewrite `RequestScopeMiddleware` as a `BaseHTTPMiddleware` dispatch function — the scope would dispose its request-scoped collaborators (the write unit of work, the `Logger`, the `UserContext`) under background tasks and streaming bodies, which still resolve the same disposed instances.
- Do not make ports ABCs or suffix them `Base`; use `Protocol`.
- Do not duplicate docstrings on adapters — the port is the single documented contract.
- Do not write module docstrings or file header comments.
- Do not create classes of only static methods; use module functions.
- Do not pack every step of an operation into one method — extract each nameable sub-goal into a helper.
- Do not bypass use cases — routes never call repositories directly.
- Do not use `DTO` in any name; do not suffix a model `Request`/`Response` unless it is that HTTP body, and do not invent a model to carry a use case's arguments — pass scalars.
- Do not let `src/ports/` import from Application — a type a port returns belongs beside the port.
- Do not add `# noqa`, `# type: ignore`, or any other lint/type suppression without checking with the user first — propose a design that avoids the violation instead.
