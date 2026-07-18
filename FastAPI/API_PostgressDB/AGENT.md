# Agent Instructions for FastAPI Clean Architecture Template

## 1. Architecture

Dependencies flow **inward only**: API → Infrastructure → Application → Domain. Domain never imports from any other layer. `src/ports/` and `src/shared/` are dependency-free **leaves**: every layer except Domain may import them.

| Layer | Location | Contains | Depends On |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities (aggregate roots with behaviour), repository ports (Protocols), enums | Nothing |
| Ports (leaf) | `src/ports/` | Technical service ports (Protocols): `transaction_context`, `logger`, `password_hasher`, `token_service`, `user_context` | Domain (enums only) + `src/shared/` |
| Application | `src/application/` | Use cases (concrete classes), request/response contracts, converters | Domain + Ports |
| Infrastructure | `src/infrastructure/` | DB models, repository/auth/logging adapters, engine/session, DI machinery | Domain + Ports + Application |
| API | `src/api/` | Routes (accept/return the contracts), operation envelopes, **composition root** | Application + Infrastructure (only in `dependencies/`) |

The composition root is `AppModule` in `src/api/dependencies/providers.py`, built on the **injector** library with in-house machinery in `src/infrastructure/di/` (`request_scope.py`, `typed_binder.py`): a ContextVar-backed **request scope** with automatic disposal, and the **`TypedBinder`** facade, which makes every binding a one-liner — implementation, port, and scope — where a mismatched implementation is a pyrefly error at that line. The FastAPI-specific accessor `Injected[T]` lives in `src/api/dependencies/injected.py`. There is no graph-completeness validation: a missing binding surfaces as a runtime error on first resolution.

### File Organisation

Files are organised by **type** first, then **entity name** within each layer.

```
src/
├── domain/
│   ├── entities/<entity>/<entity>.py       # aggregate root: invariants + behaviour
│   ├── repositories/<entity>/<entity>_repository.py   # Protocol port (clean name)
│   └── enums/{<entity>_enum.py, operation_results.py}
├── application/
│   └── use_cases/<entity>/
│       ├── <entity>_contracts.py       # *Request / *Response models (ContractModel), validation lives here
│       ├── <entity>_converter.py       # module functions, not a class
│       └── <operation>_use_case.py     # one concrete class per operation, single execute(); no separate interface
├── ports/<port>.py                     # technical service ports (Protocols): password_hasher, token_service, logger, transaction_context, user_context
├── shared/contract_model.py            # neutral wire base: camelCase JSON + frozen; extended by the contracts and the API envelopes
├── infrastructure/
│   ├── di/{request_scope.py, typed_binder.py}   # injector extensions (framework plumbing, FastAPI-agnostic)
│   ├── repositories/<entity>/sqlalchemy_<entity>_repository.py   # adapter (mechanism-qualified name)
│   ├── auth/{bcrypt_password_hasher.py, jwt_token_service.py, request_user_context.py}
│   ├── logging/json_logger.py
│   └── database/{base.py, session.py, errors.py, sqlalchemy_transaction_context.py, models/<entity>_model.py}
│                  └── errors.py    # shared driver-error classifiers (is_deadlock) reused by every repository adapter
└── api/
    ├── middleware/            # one HTTP middleware per module, named <concern>_middleware.py; __init__.py stays empty
    │   ├── request_scope_middleware.py   # RequestScopeMiddleware: opens the DI request scope (outermost; pure ASGI class)
    │   ├── request_id_middleware.py      # request_id: binds the correlation id on the Logger, echoes X-Request-ID
    │   ├── access_log_middleware.py      # access_log: one correlated request.completed entry per request
    │   ├── exception_handler_middleware.py  # exception_handler: logs anything escaping a route, returns 500 (innermost)
    │   └── registration.py               # register(app): adds every middleware in order — outermost last
    ├── dependencies/
    │   ├── injected.py        # Injected[T] route-side accessor (FastAPI Depends)
    │   ├── providers.py       # composition root: AppModule (cross-cutting binds; calls each domain's register())
    │   ├── bindings/<domain>.py   # per-domain register(typed_binder): that domain's repository + use-case binds
    │   └── jwt_dependency.py  # get_current_user guard
    ├── routers/<entity>/<operation>_route.py   # one route module per operation, own APIRouter(), resource-relative paths ("" for collection root, "/{id}" for item) — no schemas/converters
    │              └── router.py                # imports the operation modules and aggregates them via include_router(op.router, prefix="/<entity>/v1"); /api base + tags + guard on the router; entity+version on the include (per-endpoint); __init__.py stays empty
    ├── schemas/operation_schema.py   # generic result envelopes (inherit ContractModel)
    └── result_status_maps.py  # result enum -> HTTP status + message maps
└── main.py                    # app, lifespan (configure_logging + engine dispose), calls middleware register(app), routers
```

**Rule**: For every new entity, create `src/{layer}/{type}/{entity}/` folders across all layers. Never scatter entity files into flat shared directories.

---

## 2. Domain-Driven Design

The domain layer is the heart of the system and must never be anemic.

- **Entities are aggregate roots with behaviour.** They enforce their own invariants at construction (`__post_init__` raising `ValueError`) and expose intention-revealing state transitions (`User.activate()`, `User.deactivate()`, `User.is_active`) instead of leaving callers to mutate fields. Business rules that concern a single aggregate belong ON the entity; use cases orchestrate, they do not implement domain rules.
- **One repository port per aggregate root**, defined in the domain layer. Repositories load and persist whole aggregates; a targeted single-column update (e.g. `update_role`) is an acceptable CQRS-style command **only** when no domain rule guards the change — anything guarded by an invariant must go load → entity behaviour → persist.
- **Ubiquitous language**: names in code match the domain vocabulary (`User`, `UserRole`, `activate`, `login`) — no technical jargon leaking into the domain, no abbreviations.
- **Domain purity**: the domain layer imports nothing from other layers and no frameworks (stdlib `dataclasses`, `enum`, `typing` only). Validation of *input shape* (email format, lengths) lives on the `*Request` contracts at the boundary; validation of *invariants* lives on the entity as the last line of defence.
- **Domain tests come first**: entities are tested in complete isolation (`tests/domain/`) — no mocks, no fixtures, no I/O.
- Value objects (typed wrappers with equality-by-value) are introduced only when a concept carries rules of its own; do not wrap every scalar pre-emptively.

---

## 3. Naming Conventions

### Classes
- **Ports are `typing.Protocol`s with the clean, central name** — `UserRepository`, `PasswordHasher`, `TokenService`, `Logger`, `UserContext`. No `Base` suffix.
- **Adapters (implementations) are qualified by their mechanism** — `SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`, `RequestUserContext`.
- Use cases are one plain concrete class per operation in its own file, each with a single `execute` method (`CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`, ...) — no separate interface. Each class declares only the ports its operation needs, and routes/tests depend on the concrete class (mock with `AsyncMock(spec=CreateUserUseCase)`).
- Entities: singular nouns — `User`, `Order`.
- Status enums: singular `StrEnum` (`UserRole`, `UserStatus`).
- Operation result enums: generic and shared — `CreateResult`, `UpdateResult`, `DeleteResult`. Never entity-specific. `LoginResult` is the one permitted auth-specific enum.
- **Wire contracts are named for their role, never `DTO`.** Pydantic models inheriting `ContractModel` (frozen; camelCase on the wire, snake_case in code), living in `src/application/use_cases/<entity>/<entity>_contracts.py`:
  - `<Operation>Request` — the model FastAPI binds as the request body (`LoginRequest`, `RefreshTokenRequest`, `CreateUserRequest`). Field validation (`EmailStr`, `min_length`, ...) lives here.
  - `<Entity>Response` / `<Concept>Response` — the model a route returns (`UserResponse`, `TokenResponse`). Return `list[UserResponse]` directly; never a wrapper collection model.
  - **A model only earns the `Request`/`Response` suffix if it really is that body.** A type that never crosses the wire takes a plain domain-ish name (`TokenClaims`) and lives next to whatever produces it — `TokenClaims` sits in `src/ports/token_service.py` beside the port that returns it, which keeps Ports free of any Application import.
  - **Don't invent a model to carry a use case's arguments.** When a route assembles inputs from a path param plus a body field, pass scalars: `execute(user_id, role)`, not `execute(some_model)`. Use cases already take scalars where the input isn't a body (`GetUserUseCase.execute(user_id)`, `RefreshTokenUseCase.execute(refresh_token)`).
- **No per-entity API schemas**: routes accept and return the application contracts directly (`response_model=UserResponse`). Only the generic operation envelopes (`CreateOperationResponse`, ...) live in `src/api/schemas/operation_schema.py`.
- `ContractModel` (`src/shared/contract_model.py`): the single neutral shared-kernel base for anything crossing the API boundary — serialises to camelCase JSON (drives responses **and** the OpenAPI schema), accepts both camelCase and snake_case on input, and is frozen. Both the application contracts and the API operation envelopes extend it directly; there is no intermediate marker base. `src/shared/` imports only pydantic, so Application, Ports, and API may all depend on it without a layer violation.

### Variables & Properties
- Collections: plural; sets: `_set` suffix; dicts: `_map` suffix.
- Internal class members: `_` prefix; never access from outside the class.
- Booleans read like questions: `is_active`, `has_items`. No abbreviations (`repository` not `repo`).

---

## 4. Core Patterns

### Ports & Adapters (dependency inversion via Protocol)
- A **port** is a `typing.Protocol` defining the methods a collaborator must provide. Repository ports live in `src/domain/`, alongside the model that defines them. Technical service ports live in the dependency-free leaf `src/ports/`: they are consumed by several layers at once (use cases today, a business-logic layer later) and implemented by Infrastructure, so no single layer owns them — and Domain never imports them, which keeps the core model pure.
- An **adapter explicitly subclasses its port** (`class SqlAlchemyUserRepository(UserRepository):`). The port's method docstrings are inherited, so the contract is documented **once** and IDEs show it on hover both at call sites and inside the implementation; pyrefly checks every override against the port signature at the class itself, and `TypedBinder` enforces conformance structurally at the binding line.
- Use cases depend on ports (constructor parameters typed as the Protocol). Providers supply the concrete adapter.

### Dependency Injection (injector + TypedBinder)
- The composition root is `AppModule` in `src/api/dependencies/providers.py`. One line binds implementation, port, and scope via the typed facade:
  `typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository)` — and binding an implementation that does not satisfy the port is a **pyrefly error at that line**. Concrete classes with no port — the use cases — get one `bind_self_typed(CreateUserUseCase)` line per operation. `AppModule.configure()` declares the **cross-cutting** binds (services, session, transaction context, logger, user context) and delegates each domain's repository + use-case binds to a `register(typed_binder)` function in `src/api/dependencies/bindings/<domain>.py`. Binding modules belong to the API layer / composition root, so they may import the adapters, and they bind through `TypedBinder` — never plain tuples, which drop the static conformance check.
- **Scopes are explicit**, and chosen by *what holds request state*: `singleton` (from `injector`) for process-wide stateless objects (engine, `PasswordHasher`, `TokenService`); `request` (from `src/infrastructure/di/request_scope.py`) for objects that carry per-request state (the `AsyncSession`, `TransactionContext`, the bound `Logger`, and `UserContext`); and **transient** (no scope) for stateless orchestrators that only wire injected deps — the **use cases and repositories**. Transient repositories and use cases receive the request-scoped `AsyncSession` by injection, so every repository in one request shares one session and one unit of work.
- **Every implementation whose `__init__` takes dependencies carries `@inject`** (from `injector`) so the graph auto-wires from type hints. Omitting it fails at resolution with a `TypeError`.
- Construction that needs logic lives in `@provider` methods on `AppModule` (`provide_settings`, `provide_engine`, `provide_session_factory`, `provide_session`).
- **Disposal**: on request end the scope disposes its objects in reverse creation order — `aclose()` preferred, an async `close()` is awaited, failures are logged without blocking other teardowns. The session is closed this way. The engine (a singleton) is disposed explicitly in `main.lifespan` shutdown.
- The request scope is entered per HTTP request by `RequestScopeMiddleware` in `src/api/middleware/request_scope_middleware.py` (registered via `src/api/middleware/registration.py`, called from `main.py`). Resolving a request-scoped binding outside a scope raises a descriptive `RuntimeError`.
- Routes and guards resolve via `use_case: Injected[CreateUserUseCase]`. To the type checker `Injected` is the identity alias `type Injected[T] = T`, so the parameter's type IS the concrete class (hover, completions, and mismatch checks all see it); at runtime `Injected[X]` builds `Annotated[X, <Depends>]` via `__class_getitem__`, a thin `Depends` over `request.app.state.injector`. The class is named once — a wrong-class mismatch cannot be written.
- **No graph-completeness validation**: a forgotten binding is a runtime error on first resolution, not a startup failure. The wrong-implementation case is caught statically by `TypedBinder`.
- Tests bind mock **instances** in a `TestModule` (`binder.bind(CreateUserUseCase, to=mock_use_case)` — instance-bound, so no request scope is needed) and set `app.state.injector = Injector([TestModule()])`; `app.dependency_overrides` handles plain guards like `get_current_user`.

### Database session & transactions (unit of work)
- The engine and `async_sessionmaker` are **singleton `@provider` methods** on `AppModule`; the engine is disposed in `main.lifespan` shutdown.
- The `AsyncSession` is a **request-scoped `@provider` method**, so every repository adapter **and the transaction context** in one request share the same session, and the request-scope teardown closes it via `aclose()`. Repositories receive the session **by constructor** — transactional behaviour is never decided by ambient state (the scope's `ContextVar` is only the DI instance cache).
- Repository **adapters receive the `AsyncSession`** by constructor injection. They **never commit or roll back**. Mutations `flush()` (inserts) or `execute()` (update/delete) so DB errors surface in the repository and are mapped to result enums; reads just query.
  - `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`
  - `DBAPIError` for which `is_deadlock(exc)` holds → `CONCURRENCY_ERROR`; otherwise `FAILURE`
  - any other `Exception` → `FAILURE`
- **Driver-error classification is shared, not per-repository.** *How* a `DBAPIError` is recognised (unwrapping `__cause__` to an `asyncpg` error type) is a fact about the driver, identical for every aggregate, so it lives once in `src/infrastructure/database/errors.py` (`is_deadlock`) and every adapter imports it. Only the *mapping* to a result enum is per-method, because the enum differs (`CreateResult` / `UpdateResult` / `DeleteResult`). Never re-implement the `isinstance(exc.__cause__, ...)` check in an adapter; add the next classifier (e.g. `is_unique_violation`) to that module instead.
- **The use case owns the transaction boundary** via the `TransactionContext` port (`src/ports/transaction_context.py`; adapter `SqlAlchemyTransactionContext` in `src/infrastructure/database/`). Every mutating use case wraps its repository calls in `async with self._transaction_context.begin() as transaction:` inside `execute` and calls `await transaction.commit()` only when every operation reported success.
- Semantics are **rollback unless committed**: leaving the `begin()` block without commit — by early return on a failure result or by an exception — rolls back everything performed inside it. Committing a partially-failed unit of work is structurally impossible.
- **Atomic multi-repository operations**: call any number of repositories inside one `begin()` block; they share the request session, so they all succeed or all fail. If any call returns a non-success result, return without committing — every earlier operation rolls back.
- `flush()` populates `id` and server defaults via RETURNING, so the new entity id is available inside the block before commit. Do not call `session.refresh()` after inserts.
- Uncommitted work is discarded when the request ends — forgetting to commit fails safe (nothing is silently persisted).
- **`BackgroundTasks` and streaming bodies share the request's session.** The scope spans them (see §4 Middleware), so they resolve the same `AsyncSession` the route used, and it is closed only once they finish. A background task's own DB work is a *new* transaction and must own its own `begin()` block; anything that is genuinely a separate unit of work belongs in a task queue, not in `BackgroundTasks`.
- **A background task on a *read* route pins a pool connection for its whole duration.** SQLAlchemy **autobegins** a transaction on the first statement of any kind — a `SELECT` included — and only `commit()`, `rollback()`, or closing the session ends it. `TransactionContext.begin()` does not *start* transactions (it never calls `session.begin()`); it *ends* them, by rolling back unless committed. So:
  - A **write** route is safe: its `begin()` block commits, ending the transaction and returning the connection to the pool *before* the background task starts. The background task then inherits a clean session and autobegins its own transaction.
  - A **read** route (`GetUserUseCase` and friends) uses no `begin()` block, so its autobegun transaction is ended only by the session closing — which now happens after the background work. The connection stays checked out for the task's whole duration even if it touches no database at all, and with `pool_size` 5 + `max_overflow` 10 there are only 15; concurrent callers then queue behind it.
  - **If you add a background task to a read route, wrap that read in a `begin()` block.** It commits nothing and rolls back on exit, releasing the connection immediately. This is the one case that needs it — do not wrap reads by default (§"Reads just query" stands).

### Converters
- Converters are **module-level functions**, not classes of static methods. `user_converter.to_response(...)`, `to_response_list(...)`, `to_entity(...)`, etc. — the name states the direction, matching the contract it produces.

### Authentication & current user
- `get_current_user` (in `src/api/dependencies/jwt_dependency.py`) decodes the Bearer JWT, raises 401 on failure, populates the request-scoped `UserContext`, and returns `TokenClaims` (from `src/ports/token_service.py`). (The bound logger reads `user_id` from that `UserContext`, so the guard does not touch any logging state.)
- Protect a whole router with `dependencies=[Depends(get_current_user)]` on the `APIRouter`. A route handler that needs the claims directly declares `claims: TokenClaims = Depends(get_current_user)`.
- **Request-scoped user context**: the `UserContext` port (`src/ports/user_context.py`; adapter `RequestUserContext`, bound at `request` scope) holds the caller's identity for the request. Inject it into use cases or services that need the caller — auditing, ownership checks, roles/permissions — instead of threading claims through every signature. `populate()` is called exactly once by the guard (a second call raises `RuntimeError`). **Reads never raise**: `user_id` and `role` return `None` on an unauthenticated request, so the context is safe to read from unguarded routes and from middleware that runs for every request. Only guarded routes guarantee non-`None` values — a caller that needs the identity checks the value it actually uses for `None`, rather than a separate flag. Read scalar values from it and pass those to repositories — never pass the context object itself to a repository.
- Request correlation for logs is a **bound logger**: `JsonLogger` is request-scoped, and the `request_id` middleware (`src/api/middleware/request_id_middleware.py`) binds the request's correlation id onto it via `bind_request_id` — minted, or taken from an inbound `X-Request-ID` header, and echoed back as the `X-Request-ID` response header. `bind_request_id` raises on a second call (a request is bound once); log emission never raises when unbound (the field is simply omitted). `user_id` is read from the injected request-scoped `UserContext` (only when populated). No ambient `ContextVar`s.
- **One log format for the whole process**: `configure_logging()` (from `main.lifespan`) installs the JSON handler on the **root** logger, so application, uvicorn, and third-party records all propagate into one machine-parseable stream; each entry carries a `logger` field naming its source. Root sits at `WARNING` and the `app` logger at `settings.log_level`, so third-party chatter stays out at `DEBUG`. Uvicorn's `uvicorn`/`uvicorn.error` loggers have their own handlers cleared and propagation restored; `uvicorn.access` is disabled outright — it runs outside the DI request scope and so cannot carry correlation fields.
- **Access logging is the app's job**: the `access_log` middleware (`src/api/middleware/access_log_middleware.py`) emits one `request.completed` entry per request through the request-scoped `Logger`, carrying `method`, `path`, `status_code`, `duration_ms`, the bound `request_id`, and — on guarded routes — `user_id`. It runs after the correlation id is bound and after the route's guard has populated the `UserContext`. It sits outside `exception_handler`, which converts a route failure into a 500 response before it gets there, so **every** request produces exactly one access entry — failures included.

### Routes & responses
- Routes return the **response model object**; FastAPI serialises it (camelCase, via `response_model`). **Never** return a hand-built `JSONResponse(model.model_dump())` — that bypasses `response_model` and the alias generator.
- For operations whose status varies by result enum, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, and return the response model. Use `HTTPException` for read-not-found and auth failures.
- **URL shape is `/api/<entity>/<version>/<path>`** (e.g. `/api/users/v1`, `/api/users/v1/{id}`, `/api/auth/v1/login`). `/api` is the shared base, on each domain router's own `prefix`. The `/<entity>/<version>` segment (e.g. `/users/v1`) rides on each `router.include_router(op.router, prefix="/<entity>/v1")` call in `router.py` — **the version is per-endpoint**, so one endpoint can move to `/<entity>/v2` (add its operation module and include it with `prefix="/<entity>/v2"`) without touching the others. Operation files use resource-relative paths (`""` for the collection root, `/{id}` for item routes) and never repeat the entity or version. Do **not** collapse the segment onto the router's own `prefix`: FastAPI rejects including a prefix-less operation router that has an empty (`""`) collection-root path (`FastAPIError: Prefix and path cannot be both empty`), so it must ride on the `include_router` prefix.

### Middleware
- **One concern per module**, in `src/api/middleware/<concern>_middleware.py`, named for the concern (`request_scope`, `request_id`, `access_log`, `exception_handler`). Never bundle two concerns into one middleware — the DI scope, the correlation id, the access entry, and the exception net are separate modules. `__init__.py` stays empty.
- **Default to a `BaseHTTPMiddleware` dispatch function** — `async def <concern>(request, call_next)`, registered with `app.middleware("http")(<concern>)`. `request_id`, `access_log`, and `exception_handler` are all this shape.
- **`RequestScopeMiddleware` is deliberately the exception: a pure ASGI class** (`__call__(self, scope, receive, send)`, registered with `app.add_middleware(...)`). **Do not "tidy" it into a dispatch function** — that silently reintroduces a resource leak. `BaseHTTPMiddleware.call_next` returns as soon as the response *starts*, so the scope would dispose the session while `BackgroundTasks` and streaming response bodies are still running. It fails silently rather than loudly: anyio copies the context when it spawns the downstream task, so those callers still resolve the *same, already-disposed* instances — and a closed `AsyncSession` transparently re-opens on next use, checking out a connection nobody ever returns to the pool. A pure ASGI middleware wraps the raw `await self._app(...)`, which does not return until background work has finished. Regression tests live in `tests/api/middleware/test_request_scope_middleware.py`.
- **`register(app)` in `src/api/middleware/registration.py` is the only place middlewares are added**, and it owns the ordering. `main.py` calls it once (`middleware_registration.register(app)`) and never adds middleware itself — the same way `AppModule.configure()` is the only place bindings are declared.
- **Starlette runs the most recently registered middleware first, so the outermost middleware is registered last.** `register()` therefore reads bottom-up: `RequestScopeMiddleware` is added last so it wraps `request_id`, which resolves the request-scoped `Logger` and needs the scope already open. Get this backwards and the first request fails with `RuntimeError: ... resolved outside a request scope`. Any new middleware that resolves a request-scoped binding must be registered **before** it in that function. `exception_handler` is added first of all, making it innermost, with `access_log` just outside it: each reads state the ones outside it have to populate first, and the 500 that `exception_handler` returns travels back out through `access_log` (which records it) and `request_id` (which stamps the header on it).

### Error handling

Failures are reported in **one** place. `src/api/middleware/exception_handler_middleware.py` is the net under every route: it catches anything escaping a handler, logs it through the request-scoped `Logger` as `request.unhandled_exception` (traceback, `method`, `path`, plus the bound `request_id` and `user_id`), and returns `500 {"detail": "Internal Server Error"}`. The body is deliberately opaque — the detail belongs in the correlated log, not in the response.

- **A `try`/`except` earns its place only when the `except`/`finally` block does real work** — work that is specific to the call site and that the middleware could not do. Legitimate handlers either **translate** a failure into the vocabulary of their layer or **undo** something:
  - repository adapters map `IntegrityError` / `DBAPIError` to `UNIQUE_CONSTRAINT_ERROR` / `CONCURRENCY_ERROR` / `FAILURE`;
  - `SqlAlchemyTransactionContext.begin` rolls back, then re-raises;
  - `JwtTokenService.decode_token` turns an `InvalidTokenError` into `None`;
  - the request-scope teardown logs a failing `aclose()` so the remaining disposals still run.
- **Never catch merely to report.** A block that only logs and re-raises, wraps the exception in another exception, or hand-builds a 500 duplicates the middleware — delete it and let the exception propagate. Same for `except: raise` and for a `finally` that does nothing the scope teardown or the `begin()` block already guarantees.
- **Don't catch to produce an `HTTPException`.** Routes raise `HTTPException` for outcomes they *expect* and detect themselves (not-found, auth failure) — never as a translation of a caught unexpected exception.
- **Never catch `Exception` to keep going with a default value** unless that default is a real result of the operation (a result enum, `None` from a decode). Swallowing an error to return a plausible-looking success hides the failure from the log and from the caller.
- Rollback needs no `try` at the use case: leaving a `begin()` block by exception already rolls back, and the exception continues to the middleware.
- **The one place that must catch for itself is a `BackgroundTasks` callable.** `exception_handler` cannot help it: the task runs after the response was sent, so its exception is re-raised past the `dispatch` function that already returned, escapes to uvicorn, and is logged as a bare `Exception in ASGI application` with **no `request_id` and no `user_id`** — the request scope still disposes correctly, but the correlation is gone. So a background task wraps its own body and logs the failure through the injected `Logger`. That is a translating handler, not a reporting one: it is the only reporter that task will ever get.

---

## 5. Enums

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

## 6. Database

### DB-Generated Values
Never set these in Python code:
- **`id`**: `autoincrement=True`. Entity holds `id: int | None = None` before insert; `session.flush()` populates it via RETURNING.
- **`created_at`**: `server_default=func.now()`. Entity field is `datetime | None = None`; populated by the same flush RETURNING. Never call `session.refresh()` after inserts.

### Database Constraints
- Every constraint **must** have an explicit `name` so Alembic can manage it. Declare constraints in `__table_args__`.

| Constraint | Naming pattern | Example |
|---|---|---|
| Unique | `uq_{table}_{column(s)}` | `uq_users_username` |
| Foreign key | `fk_{table}_{column}` | `fk_orders_user_id` |
| Check | `ck_{table}_{description}` | `ck_orders_amount_positive` |
| Index | `ix_{table}_{column(s)}` | `ix_orders_status` |

---

## 7. External Services

- Port (`Protocol`) lives in `src/ports/<service>.py`. Use cases depend only on the port.
- Adapter lives in `src/infrastructure/<service>/`, mechanism-qualified name, explicitly subclassing the port.
- Wire it with one `bind_typed(...).to(..., scope=singleton)` line in `AppModule`. Request-scoped resources are disposed automatically by the scope teardown (`close()`/`aclose()`); singleton resources holding connections must be disposed in `main.lifespan` shutdown (see the database engine).
- To switch providers: write a new adapter and change one binding line. The use case is untouched.

---

## 8. Adding a New Entity

1. **Domain**: enums in `src/domain/enums/<entity>_enum.py`; entity dataclass (invariants + behaviour) in `src/domain/entities/<entity>/`; repository **Protocol** in `src/domain/repositories/<entity>/<entity>_repository.py`.
2. **Infrastructure**: ORM model in `src/infrastructure/database/models/<entity>_model.py` (re-export from `models/__init__.py`); adapter `sqlalchemy_<entity>_repository.py` subclassing the port and taking an `AsyncSession`.
3. **Application**: `ContractModel` request/response contracts (with validation) in `<entity>_contracts.py`, converter **functions**, one concrete use case class per operation (single `execute` method) in `src/application/use_cases/<entity>/`. Mutating use cases inject `TransactionContext` and wrap repository calls in a `begin()` block, committing only on success.
4. **API**: one route module per operation accepting and returning the contracts directly (`use_case: Injected[<Operation>UseCase]`, `response_model=<Entity>Response`), each with its own `APIRouter()` and **resource-relative paths** (`""` for the collection root, `/{id}` for item routes — neither the `/<entity>` nor the version is repeated in the operation files); `router.py` (with `prefix="/api"`, tags, and guard) imports every operation module and aggregates them with `router.include_router(op.router, prefix="/<entity>/v1")`, giving URLs `/api/<entity>/v1/...` with the version per-endpoint; add a `src/api/dependencies/bindings/<entity>.py` with a `register(typed_binder)` that binds the repository (transient) and each use case (`bind_self_typed`, transient), and call it from `AppModule.configure()`; include the router from `router.py` in `main.py`. No per-entity schemas or API converters.
5. **Tests**: domain entity tests (no mocks), use case tests (mock the ports), route tests (bind a mock use case instance in a `TestModule`).

---

## 9. Testing

Tests live in `tests/` and mirror `src/`.

### Domain Tests
- Entities are tested in complete isolation — construction invariants, state transitions, derived properties. No mocks, no I/O.

### Use Case Tests
- Mock collaborators with `AsyncMock(spec=UserRepository)` / `MagicMock(spec=PasswordHasher)` — `spec` against the Protocol surfaces the real method names.
- Provide a `FakeTransactionContext` (a tiny async-context-manager fake yielding a fake transaction — Protocols make this trivial) and assert that `commit` was called on success and **not** called on failure.
- `asyncio_mode = "auto"` is configured; no `@pytest.mark.asyncio` needed.

### Route Tests
- Create a minimal `FastAPI()`, include only the router under test. **Never import `src/main.py`.**
- Bind a mock instance of the use case in a `TestModule`; override plain FastAPI guards with `app.dependency_overrides`:
  ```python
  mock_use_case = AsyncMock(spec=CreateUserUseCase)

  class TestModule(Module):
      def configure(self, binder: Binder) -> None:
          binder.bind(CreateUserUseCase, to=mock_use_case)  # instance-bound: no scope needed

  app.state.injector = Injector([TestModule()])
  app.dependency_overrides[get_current_user] = lambda: TokenClaims(user_id=1, role=UserRole.ADMIN)
  ```
- Use `httpx.AsyncClient` with `ASGITransport`.

| Layer | File | Test? |
|-------|------|-------|
| Domain | `<entity>.py` | Yes — pure unit tests, no mocks |
| Application | `<operation>_use_case.py` | Yes — one test module per use case, mock the repository/service ports |
| Application | `<entity>_converter.py` | Yes |
| API | `<operation>_route.py` | Yes — one test module per route, bind mock use case instances in a `TestModule` |
| Infrastructure | repository adapter | No — needs a live DB (integration only) |
| Infrastructure | `SqlAlchemyTransactionContext` | Yes — integration test against in-memory SQLite (aiosqlite) proving commit/rollback atomicity |
| Infrastructure | `di/` (request scope, typed binder) | Yes — unit tests in `tests/infrastructure/di/` |

---

## 10. Documentation & Code Style

- **No module docstrings or top-of-file comments** — file location and names carry that information.
- **The contract is documented once, on the port**: Protocol classes and their methods carry **concise** docstrings. Adapters **explicitly subclass the port and inherit them** — never repeat a method docstring in an adapter; IDE hover and `help()` resolve the port docs through the MRO.
- **Docstrings are lean**: a one-line summary, then `Args`/`Returns`/`Raises` sections where applicable — nothing else. Never describe *how* the code works or *why* (no implementation details, rationale, or usage examples); the summary says *what* it does.
- Adapter classes keep a short class docstring stating only mechanism-specific facts (e.g. "backed by PyJWT"). No `__init__` docstrings — constructor parameters are self-describing via type hints.
- Classes with no port — the use cases — carry their own method docstrings: they are the single source for their contract.
- Standalone public functions (converters, providers, guards, routes) carry their own docstrings — they have no port to inherit from. Route docstrings become OpenAPI descriptions: describe endpoint behaviour, not injected parameters.
- Inline comments only for constraints the code cannot express (e.g. why `flush()` instead of `commit()`).
- Max line length: **140 characters** (`skip-magic-trailing-comma = true`, so the formatter uses the full width). Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/` after every change. Run `uv run pyrefly check` to type-check.
- Always use `uv run`. Modern type annotations (`list[X]`, `X | None`). All DB I/O is async. URL shape: `/api/<entity>/<version>/<path>` (e.g. `/api/users/v1`) — `/api` base on the domain router, `/<entity>/v1` on each `include_router` call so the version is per-endpoint.
- **Never introduce a lint/type-check suppression** (`# noqa`, `# type: ignore`, pyrefly ignore comments, or equivalent) **without checking with the user first.** If satisfying a rule would require one, stop and present the design alternatives that avoid it instead of silently suppressing.

### Method Composition (one level of abstraction per method)

A method body states **what** its operation does, as a sequence of named steps; the mechanics of each step live in a helper. When a block inside a method pursues a **sub-goal** — building a value, classifying an error, checking a precondition, assembling a payload, disposing a collection — extract it into a helper named for that sub-goal and call it. The caller then reads as prose and the helper holds the detail.

- **The trigger is a nameable sub-goal, not a line count.** If you could write a comment above a block saying what it accomplishes ("map the DB error to a result", "dispose every cached instance"), that comment is the helper's name and the block is its body: extract it and drop the comment. A short method can still be doing two jobs, and a long one that is genuinely a flat sequence of guards is fine.
- **A method never mixes levels.** Orchestrating steps *and* inlining the mechanics of one of them is the violation — hoist the mechanics out so every call in the body sits at the same altitude.
- **Prefer a module-level `_` function when the logic is pure** (no instance state) — `_to_entity`, `_is_deadlock` in the repository adapters. Use a `_`-prefixed method when it needs `self`.
- **Helpers take no docstrings**; the name is the contract. The public method keeps its docstring (§10's single-source rule is unchanged) and describes the operation, never the helpers.
- **Do not extract for its own sake.** A helper wrapping a single expression that its variable already names adds a hop without adding meaning. The test is whether the *caller* reads better with the block gone — if not, leave it inline.

---

## 11. Anti-Patterns

- Don't leave the domain anemic — invariants and state transitions belong on the entity, not scattered across use cases.
- Don't wire bindings outside the composition root — `AppModule.configure()` or the per-domain `register(typed_binder)` functions in `src/api/dependencies/bindings/` that it calls — and always through `TypedBinder` so conformance is checked (never plain `(port, adapter)` tuples, which drop the static check). Binding modules stay in the API layer; never put them in `src/application/` (that would make Application import Infrastructure adapters).
- Don't omit `@inject` on an implementation whose `__init__` takes dependencies — resolution fails with `TypeError` at runtime.
- Don't keep session (or other control-flow) state in a module-global `ContextVar`. Inject the request-scoped `AsyncSession`.
- Don't pass the `AsyncSession` to use cases, or sessions to repository constructors as constants — adapters get the request session via the provider.
- Don't commit or roll back inside repositories — the use case owns the boundary via `TransactionContext`.
- Don't call `transaction.commit()` unless every repository call in the block returned success.
- Don't call `session.refresh()` after inserts — `flush()` RETURNING already populates `id` and server defaults.
- Don't return `JSONResponse(model.model_dump())` from routes — return the model and let FastAPI serialise it; set `response.status_code` for dynamic codes.
- Don't write a `try`/`except` whose block only logs, re-raises, wraps, or hand-builds a 500 — the `exception_handler` middleware already does that once for every route. Catch only to translate a failure (to a result enum, to `None`) or to undo work (rollback), and never to swallow an error behind a fake success. The exception is a `BackgroundTasks` callable, which must catch and log for itself — no middleware can report it.
- Don't rewrite `RequestScopeMiddleware` as a `BaseHTTPMiddleware` dispatch function — `call_next` returns when the response starts, so the scope would dispose the session under background tasks and streaming bodies, silently leaking a connection per call.
- Don't make ports ABCs — use `typing.Protocol`; don't suffix ports with `Base`.
- Don't duplicate docstrings on adapters — the port is the single documented contract.
- Don't write module docstrings or file header comments.
- Don't create classes of only `@staticmethod`s — use module functions.
- Don't pack every step of an operation into one method — each nameable sub-goal becomes a helper, so the method reads as named steps at one level of abstraction.
- Don't bypass use cases — routes never call repositories directly.
- Don't let Domain import from Infrastructure or API.
- Don't create entity-specific result enums or wrapper collection responses.
- Don't name anything `DTO` — a wire model is a `*Request` or a `*Response`; a non-wire type gets a plain name (`TokenClaims`).
- Don't suffix a model `Request`/`Response` unless it really is that HTTP body; don't invent a model just to group a use case's arguments — pass scalars.
- Don't let `src/ports/` import from Application — a type a port returns belongs beside the port.
- Don't scatter entity files into flat shared directories.
- Don't add `# noqa`, `# type: ignore`, or any other lint/type suppression without checking with the user first — propose a design that avoids the violation instead.

---

## 12. Keeping Quick-Reference Files in Sync

`AGENT.md` is the single source of truth. The quick-reference files below mirror its critical rules and must be updated together: [.clinerules](.clinerules), [.cursorrules](.cursorrules), [.windsurfrules](.windsurfrules), [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md), [.antigravity/rules.md](.antigravity/rules.md), [.github/copilot-instructions.md](.github/copilot-instructions.md).
