# Agent Instructions for FastAPI Clean Architecture Template

## 1. Architecture

Dependencies flow **inward only**: API → Infrastructure → Application → Domain. Domain never imports from any other layer.

| Layer | Location | Contains | Depends On |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities (aggregate roots with behaviour), repository ports (Protocols), enums | Nothing |
| Application | `src/application/` | Use cases (concrete classes), DTOs, converters, service ports (Protocols) | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, repository/auth/logging adapters, engine/session, DI machinery | Domain + Application |
| API | `src/api/` | Routes (accept/return DTOs), operation envelopes, **composition root** | Application + Infrastructure (only in `dependencies/`) |

The composition root is `AppModule` in `src/api/dependencies/providers.py`, built on the **injector** library with in-house machinery in `src/infrastructure/di/` (`request_scope.py`, `typed_binder.py`): a ContextVar-backed **request scope** with automatic disposal, and the **`TypedBinder`** facade, which makes every binding a one-liner — implementation, port, and scope — where a mismatched implementation is a pyrefly error at that line. The FastAPI-specific accessor `Injected()` lives in `src/api/dependencies/injected.py`. There is no graph-completeness validation: a missing binding surfaces as a runtime error on first resolution (accepted trade-off).

### File Organisation

Files are organised by **type** first, then **entity name** within each layer.

```
src/
├── domain/
│   ├── entities/<entity>/<entity>.py       # aggregate root: invariants + behaviour
│   ├── repositories/<entity>/<entity>_repository.py   # Protocol port (clean name)
│   └── enums/{<entity>_enum.py, operation_results.py}
├── application/
│   ├── use_cases/<entity>/
│   │   ├── <entity>_dto.py
│   │   ├── <entity>_converter.py       # module functions, not a class
│   │   └── <operation>_use_case.py     # one concrete class per operation, single execute(); no separate interface
│   └── services/<service>.py           # Protocol ports (password_hasher, token_service, logger, transaction_context, user_context)
├── infrastructure/
│   ├── di/{request_scope.py, typed_binder.py}   # injector extensions (framework plumbing, FastAPI-agnostic)
│   ├── repositories/<entity>/sqlalchemy_<entity>_repository.py   # adapter (mechanism-qualified name)
│   ├── auth/{bcrypt_password_hasher.py, jwt_token_service.py, request_user_context.py}
│   ├── logging/{json_logger.py, log_context.py}
│   └── database/{base.py, session.py, sqlalchemy_transaction_context.py, models/<entity>_model.py}
└── api/
    ├── dependencies/
    │   ├── injected.py        # Injected() route-side accessor (FastAPI Depends)
    │   ├── providers.py       # composition root: AppModule (ports -> adapters, scopes)
    │   └── jwt_dependency.py  # get_current_user guard
    ├── routers/<entity>/<operation>_route.py   # one route module per operation, own APIRouter(), resource-relative paths ("" for collection root, "/{id}" for item) — no schemas/converters
    │              └── router.py                # imports the operation modules and aggregates them via include_router(op.router, prefix="/<entity>"); the resource segment lives here once, the version prefix + tags + guard on the router; __init__.py stays empty
    ├── schemas/operation_schema.py   # generic result envelopes (inherit DTOBase)
    └── result_status_maps.py  # result enum -> HTTP status + message maps
└── main.py                    # app, lifespan (engine), request_context middleware (DI scope + log vars), routers
```

**Rule**: For every new entity, create `src/{layer}/{type}/{entity}/` folders across all layers. Never scatter entity files into flat shared directories.

---

## 2. Domain-Driven Design

The domain layer is the heart of the system and must never be anemic.

- **Entities are aggregate roots with behaviour.** They enforce their own invariants at construction (`__post_init__` raising `ValueError`) and expose intention-revealing state transitions (`User.activate()`, `User.deactivate()`, `User.is_active`) instead of leaving callers to mutate fields. Business rules that concern a single aggregate belong ON the entity; use cases orchestrate, they do not implement domain rules.
- **One repository port per aggregate root**, defined in the domain layer. Repositories load and persist whole aggregates; a targeted single-column update (e.g. `update_role`) is an acceptable CQRS-style command **only** when no domain rule guards the change — anything guarded by an invariant must go load → entity behaviour → persist.
- **Ubiquitous language**: names in code match the domain vocabulary (`User`, `UserRole`, `activate`, `login`) — no technical jargon leaking into the domain, no abbreviations.
- **Domain purity**: the domain layer imports nothing from other layers and no frameworks (stdlib `dataclasses`, `enum`, `typing` only). Validation of *input shape* (email format, lengths) lives on the DTOs at the boundary; validation of *invariants* lives on the entity as the last line of defence.
- **Domain tests come first**: entities are tested in complete isolation (`tests/domain/`) — no mocks, no fixtures, no I/O.
- Value objects (typed wrappers with equality-by-value) are introduced only when a concept carries rules of its own; do not wrap every scalar pre-emptively.

---

## 3. Naming Conventions

### Classes
- **Ports are `typing.Protocol`s with the clean, central name** — `UserRepository`, `PasswordHasher`, `TokenService`, `Logger`, `UserContext`. No `Base` suffix.
- **Adapters (implementations) are qualified by their mechanism** — `SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`, `RequestUserContext`.
- Use cases are one plain concrete class per operation in its own file, each with a single `execute` method (`CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`, ...) — no separate interface; there is only ever one implementation, each class declares only the ports its operation needs, and routes/tests depend on the concrete class (mock with `AsyncMock(spec=CreateUserUseCase)`).
- Entities: singular nouns — `User`, `Order`.
- Status enums: singular `StrEnum` (`UserRole`, `UserStatus`).
- Operation result enums: generic and shared — `CreateResult`, `UpdateResult`, `DeleteResult`. Never entity-specific. `LoginResult` is the one permitted auth-specific enum.
- DTOs: Pydantic models inheriting `DTOBase` (frozen; camelCase on the wire, snake_case in code) with `DTO` suffix; they are the API request/response bodies, so field validation (`EmailStr`, `min_length`, ...) lives on them. Return `list[UserDTO]` directly; never a wrapper collection DTO.
- **No per-entity API schemas**: routes accept and return the application DTOs directly (`response_model=UserDTO`). Only the generic operation envelopes (`CreateOperationResponse`, ...) live in `src/api/schemas/operation_schema.py`, and they inherit `DTOBase` too.
- `DTOBase` (`src/application/dto_base.py`): the base for every DTO and envelope — serialises to camelCase JSON (drives responses **and** the OpenAPI schema), accepts both camelCase and snake_case on input, and is frozen.

### Variables & Properties
- Collections: plural; sets: `_set` suffix; dicts: `_map` suffix.
- Internal class members: `_` prefix; never access from outside the class.
- Booleans read like questions: `is_active`, `has_items`. No abbreviations (`repository` not `repo`).

---

## 4. Core Patterns

### Ports & Adapters (dependency inversion via Protocol)
- A **port** is a `typing.Protocol` defining the methods a collaborator must provide. It lives where it is *consumed*: repository ports in `src/domain/`, service ports in `src/application/services/`.
- An **adapter explicitly subclasses its port** (`class SqlAlchemyUserRepository(UserRepository):`). This is deliberate: the port's method docstrings are inherited, so the contract is documented **once** and IDEs show it on hover both at call sites and inside the implementation; pyrefly additionally checks every override against the port signature at the class itself. Conformance is still enforced structurally at the binding line by `TypedBinder`.
- Use cases depend on ports (constructor parameters typed as the Protocol). Providers supply the concrete adapter.

### Dependency Injection (injector + TypedBinder)
- The composition root is `AppModule` in `src/api/dependencies/providers.py`. One line binds implementation, port, and scope via the typed facade:
  `typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository, scope=request)` — and binding an implementation that does not satisfy the port is a **pyrefly error at that line**. Concrete classes with no port — the use cases — get one `bind_self_typed(CreateUserUseCase, scope=request)` line per operation.
- **Scopes are explicit**: `singleton` (from `injector`) for process-wide objects (engine, `PasswordHasher`, `TokenService`, `Logger`); `request` (from `src/infrastructure/di/request_scope.py`) for per-request objects (session, repositories, transaction context, use cases). Everything in one request shares the same instances; the request scope's state lives in a `ContextVar`, isolated per request under asyncio.
- **Every implementation whose `__init__` takes dependencies carries `@inject`** (from `injector`) so the graph auto-wires from type hints. Omitting it fails at resolution with a `TypeError`.
- Construction that needs logic lives in `@provider` methods on `AppModule` (`provide_settings`, `provide_engine`, `provide_session_factory`, `provide_session`).
- **Disposal**: on request end the scope disposes its objects in reverse creation order — `aclose()` preferred, an async `close()` is awaited, failures are logged without blocking other teardowns. The session is closed this way. The engine (a singleton) is disposed explicitly in `main.lifespan` shutdown.
- The request scope is entered per HTTP request by the `request_context` middleware in `main.py`. Resolving a request-scoped binding outside a scope raises a descriptive `RuntimeError`.
- Routes and guards resolve via `Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]` — a thin `Depends` over `request.app.state.injector`.
- **No graph-completeness validation**: a forgotten binding is a runtime error on first resolution, not a startup failure. This is an accepted trade-off; the wrong-implementation case is still caught statically by `TypedBinder`.
- Tests bind mock **instances** in a `TestModule` (`binder.bind(CreateUserUseCase, to=mock_use_case)` — instance-bound, so no request scope is needed) and set `app.state.injector = Injector([TestModule()])`; `app.dependency_overrides` handles plain guards like `get_current_user`.

### Database session & transactions (unit of work)
- The engine and `async_sessionmaker` are **singleton `@provider` methods** on `AppModule`; the engine is disposed in `main.lifespan` shutdown.
- The `AsyncSession` is a **request-scoped `@provider` method**, so every repository adapter **and the transaction context** in one request share the same session, and the request-scope teardown closes it via `aclose()`. Repositories receive the session **by constructor** — transactional behaviour is never decided by ambient state (the scope's `ContextVar` is only the DI instance cache).
- Repository **adapters receive the `AsyncSession`** by constructor injection. They **never commit or roll back**. Mutations `flush()` (inserts) or `execute()` (update/delete) so DB errors surface in the repository and are mapped to result enums; reads just query.
  - `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`
  - `DBAPIError` whose `__cause__` is `asyncpg…DeadlockDetectedError` → `CONCURRENCY_ERROR`; otherwise `FAILURE`
  - any other `Exception` → `FAILURE`
- **The use case owns the transaction boundary** via the `TransactionContext` port (`src/application/services/transaction_context.py`; adapter `SqlAlchemyTransactionContext` in `src/infrastructure/database/`). Every mutating use case wraps its repository calls in `async with self._transaction_context.begin() as transaction:` inside `execute` and calls `await transaction.commit()` only when every operation reported success.
- Semantics are **rollback unless committed**: leaving the `begin()` block without commit — by early return on a failure result or by an exception — rolls back everything performed inside it. Committing a partially-failed unit of work is structurally impossible.
- **Atomic multi-repository operations**: call any number of repositories inside one `begin()` block; they share the request session, so they all succeed or all fail. If any call returns a non-success result, return without committing — every earlier operation rolls back.
- `flush()` populates `id` and server defaults via RETURNING, so the new entity id is available inside the block before commit. Do not call `session.refresh()` after inserts.
- Uncommitted work is discarded when the request ends — forgetting to commit fails safe (nothing is silently persisted).

### Converters
- Converters are **module-level functions**, not classes of static methods. `user_converter.to_dto(...)`, `to_entity(...)`, etc.

### Authentication & current user
- `get_current_user` (in `src/api/dependencies/jwt_dependency.py`) decodes the Bearer JWT, raises 401 on failure, populates the request-scoped `UserContext`, records the user id in the logging context, and returns a `TokenClaimsDTO`.
- Protect a whole router with `dependencies=[Depends(get_current_user)]` on the `APIRouter`. A route handler that needs the claims directly declares `claims: TokenClaimsDTO = Depends(get_current_user)`.
- **Request-scoped user context**: the `UserContext` port (`src/application/services/user_context.py`; adapter `RequestUserContext`, bound at `request` scope) holds the caller's identity for the request. Inject it into use cases or services that need the caller — auditing, ownership checks, roles/permissions — instead of threading claims through every signature. `populate()` is called exactly once by the guard (a second call raises `RuntimeError`); reading it unpopulated raises `RuntimeError`, so it is only valid on guarded routes. Read scalar values from it and pass those to repositories — never pass the context object itself to a repository.
- Request correlation for logs (`request_id`, `user_id`) is carried in context variables in `src/infrastructure/logging/log_context.py` — set by the `request_context` middleware and the guard. Context variables are appropriate here because they carry cross-cutting observability metadata, not control-flow or transactional state.

### Routes & responses
- Routes return the **response model object**; FastAPI serialises it (camelCase, via `response_model`). **Never** return a hand-built `JSONResponse(model.model_dump())` — that bypasses `response_model` and the alias generator.
- For operations whose status varies by result enum, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, and return the response model. Use `HTTPException` for read-not-found and auth failures.
- **The `/<entity>` resource segment is declared once**, on the `router.include_router(op.router, prefix="/<entity>")` call in `router.py` — never repeated in the operation files, which use resource-relative paths (`""` for the collection root, `/{id}` for item routes). Do **not** try to collapse it onto the router's own `prefix` (e.g. `prefix="/api/v1/<entity>"`): FastAPI rejects including a prefix-less operation router that has an empty (`""`) collection-root path (`FastAPIError: Prefix and path cannot be both empty`), so the segment must ride on the `include_router` prefix.

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

- Port (`Protocol`) lives in `src/application/services/<service>.py`. Use cases depend only on the port.
- Adapter lives in `src/infrastructure/<service>/`, mechanism-qualified name, explicitly subclassing the port.
- Wire it with one `bind_typed(...).to(..., scope=singleton)` line in `AppModule`. Request-scoped resources are disposed automatically by the scope teardown (`close()`/`aclose()`); singleton resources holding connections must be disposed in `main.lifespan` shutdown (see the database engine).
- To switch providers: write a new adapter and change one binding line. The use case is untouched.

---

## 8. Adding a New Entity

1. **Domain**: enums in `src/domain/enums/<entity>_enum.py`; entity dataclass (invariants + behaviour) in `src/domain/entities/<entity>/`; repository **Protocol** in `src/domain/repositories/<entity>/<entity>_repository.py`.
2. **Infrastructure**: ORM model in `src/infrastructure/database/models/<entity>_model.py` (re-export from `models/__init__.py`); adapter `sqlalchemy_<entity>_repository.py` subclassing the port and taking an `AsyncSession`.
3. **Application**: `DTOBase` DTOs (with validation), converter **functions**, one concrete use case class per operation (single `execute` method) in `src/application/use_cases/<entity>/`. Mutating use cases inject `TransactionContext` and wrap repository calls in a `begin()` block, committing only on success.
4. **API**: one route module per operation accepting and returning the DTOs directly (`Annotated[<Operation>UseCase, Injected(<Operation>UseCase)]`, `response_model=<Entity>DTO`), each with its own `APIRouter()` and **resource-relative paths** (`""` for the collection root, `/{id}` for item routes — the `/<entity>` segment is NOT repeated in the operation files); `router.py` imports every operation module and aggregates them with `router.include_router(op.router, prefix="/<entity>")`, so the resource segment is declared once there (version prefix `/api/v1`, tags, and guard live on the router itself); add one `bind_typed(...).to(...)` line per port and one `bind_self_typed(...)` line per use case to `AppModule.configure()`; include the router from `router.py` in `main.py`. No per-entity schemas or API converters.
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
  app.dependency_overrides[get_current_user] = lambda: TokenClaimsDTO(user_id=1, role=UserRole.ADMIN)
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
- **The contract is documented once, on the port**: Protocol classes and their methods carry full Google-style docstrings. Adapters **explicitly subclass the port and inherit them** — never repeat a method docstring in an adapter; IDE hover and `help()` resolve the port docs through the MRO.
- Adapter classes keep a short class docstring stating only mechanism-specific facts (e.g. "backed by PyJWT"). No `__init__` docstrings — constructor parameters are self-describing via type hints.
- Classes with no port — the use cases — carry their own method docstrings: they are the single source for their contract.
- Standalone public functions (converters, providers, guards, routes) carry their own docstrings — they have no port to inherit from. Route docstrings become OpenAPI descriptions: describe endpoint behaviour, not injected parameters.
- Inline comments only for constraints the code cannot express (e.g. why `flush()` instead of `commit()`).
- Max line length: **140 characters** (`skip-magic-trailing-comma = true`, so the formatter uses the full width). Run `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/` after every change. Run `uv run pyrefly check` to type-check.
- Always use `uv run`. Modern type annotations (`list[X]`, `X | None`). All DB I/O is async. API prefix: `/api/v1`.
- **Never introduce a lint/type-check suppression** (`# noqa`, `# type: ignore`, pyrefly ignore comments, or equivalent) **without checking with the user first.** If satisfying a rule would require one, stop and present the design alternatives that avoid it instead of silently suppressing.

---

## 11. Anti-Patterns

- Don't leave the domain anemic — invariants and state transitions belong on the entity, not scattered across use cases.
- Don't wire bindings anywhere except `AppModule.configure()`, and always through `TypedBinder` so conformance is checked.
- Don't omit `@inject` on an implementation whose `__init__` takes dependencies — resolution fails with `TypeError` at runtime.
- Don't keep session (or other control-flow) state in a module-global `ContextVar`. Inject the request-scoped `AsyncSession`.
- Don't pass the `AsyncSession` to use cases, or sessions to repository constructors as constants — adapters get the request session via the provider.
- Don't commit or roll back inside repositories — the use case owns the boundary via `TransactionContext`.
- Don't call `transaction.commit()` unless every repository call in the block returned success.
- Don't call `session.refresh()` after inserts — `flush()` RETURNING already populates `id` and server defaults.
- Don't return `JSONResponse(model.model_dump())` from routes — return the model and let FastAPI serialise it; set `response.status_code` for dynamic codes.
- Don't make ports ABCs — use `typing.Protocol`; don't suffix ports with `Base`.
- Don't duplicate docstrings on adapters — the port is the single documented contract.
- Don't write module docstrings or file header comments.
- Don't create classes of only `@staticmethod`s — use module functions.
- Don't bypass use cases — routes never call repositories directly.
- Don't let Domain import from Infrastructure or API.
- Don't create entity-specific result enums or wrapper collection DTOs.
- Don't scatter entity files into flat shared directories.
- Don't add `# noqa`, `# type: ignore`, or any other lint/type suppression without checking with the user first — propose a design that avoids the violation instead.

---

## 12. Keeping Quick-Reference Files in Sync

`AGENT.md` is the single source of truth. The quick-reference files below mirror its critical rules and must be updated together: [.clinerules](.clinerules), [.cursorrules](.cursorrules), [.windsurfrules](.windsurfrules), [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md), [.antigravity/rules.md](.antigravity/rules.md), [.github/copilot-instructions.md](.github/copilot-instructions.md).
