# FastAPI Clean Architecture — Rules

## Layer boundaries

```
API  →  Infrastructure  →  Application  →  Domain
```

| Layer | Location | Can import from |
|-------|----------|-----------------|
| Domain | `src/domain/` | Nothing |
| Application | `src/application/` | Domain only |
| Infrastructure | `src/infrastructure/` | Domain + Application |
| API | `src/api/` | Application + Infrastructure (adapters wired only in `dependencies/`) |

The composition root is `AppModule` in `src/api/dependencies/providers.py`,
built on `injector` plus the in-house DI machinery in `src/infrastructure/di/`
(`request_scope.py`, `typed_binder.py`) and the FastAPI accessor
`src/api/dependencies/injected.py`: one line binds implementation, port, and
scope, and a mismatched implementation is a pyrefly error at that line. No
graph-completeness validation — a missing binding fails at runtime on first
resolution.

## Domain-Driven Design

- Entities are aggregate roots with behaviour: invariants enforced in `__post_init__` (raise `ValueError`), state transitions via intention-revealing methods (`User.activate()`, `User.deactivate()`, `User.is_active`). Never an anemic domain — business rules for one aggregate live on the entity; use cases orchestrate only.
- One repository port per aggregate root, defined in Domain. A targeted single-column update is acceptable only when no domain rule guards the change; otherwise load → entity behaviour → persist.
- Ubiquitous language everywhere. Domain imports only stdlib (`dataclasses`, `enum`, `typing`).
- DTO validation guards input shape at the boundary; entity invariants are the last line of defence.
- Domain entities get pure unit tests (`tests/domain/`) — no mocks, no I/O.

## Naming

- Ports are `typing.Protocol`s with the clean name — `UserRepository`, `PasswordHasher`, `TokenService`, `Logger`, `UserContext`. No `Base` suffix.
- Adapters are mechanism-qualified — `SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`, `RequestUserContext`.
- Use cases are one plain concrete class per operation in its own file, each with a single `execute` method (`CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`, ...) — no separate interface; each declares only the ports its operation needs, and routes and tests depend on the concrete class.
- DTOs: Pydantic models inheriting `DTOBase` (frozen, camelCase aliases on the wire), `DTO` suffix; validation lives on the DTOs; return `list[UserDTO]` directly, never a wrapper DTO.
- No per-entity API schemas or API converters: routes accept/return DTOs directly; only the generic operation envelopes remain in `api/schemas/` (also `DTOBase`).
- Converters: module-level functions, never classes of static methods.
- Enums: `StrEnum`, lowercase values, all in `src/domain/enums/`.
- Result enums: always generic — `CreateResult`, `UpdateResult`, `DeleteResult`; never entity-specific.
- Booleans: `is_active`, `has_items`, `can_update` — never bare nouns. No abbreviations.

## Documentation (single source, IDE hover)

- No module docstrings or top-of-file comments anywhere.
- The contract is documented once, on the port: Protocol classes/methods carry **concise** docstrings — a one-line summary plus `Args`/`Returns`/`Raises` only, never implementation details, rationale, or usage examples. Adapters explicitly subclass their port (`class SqlAlchemyUserRepository(UserRepository):`) and inherit them — never repeat method docstrings in adapters; IDE hover resolves the port docs through the MRO.
- Adapter classes keep a short class docstring for mechanism-specific notes only; no `__init__` docstrings.
- Classes with no port — the use cases — carry their own method docstrings: they are the single source.
- Standalone public functions (converters, providers, guards, routes) keep their own docstrings; route docstrings become OpenAPI descriptions.

## Ports & adapters (dependency inversion via Protocol)

- A port is a `typing.Protocol` defining required methods; it lives where it is consumed (repository ports in Domain, service ports in `src/application/services/`).
- An adapter **explicitly subclasses its port** — inheriting the documented contract and giving pyrefly override checking at the class itself. Conformance is additionally checked at the binding line by `TypedBinder`.
- Use cases take ports as constructor parameters; providers supply the concrete adapter.

## Dependency injection (injector + TypedBinder)

- Wire via `TypedBinder` — one line per binding: `typed_binder.bind_typed(UserRepository).to(SqlAlchemyUserRepository)`, concrete classes (use cases) get one `bind_self_typed(CreateUserUseCase)` line per operation. A wrong implementation is a pyrefly error (never plain tuples — they drop the check). `AppModule.configure()` holds the cross-cutting binds and calls each domain's `register(typed_binder)` in `src/api/dependencies/bindings/<domain>.py` (API layer, never `src/application/`).
- Explicit scopes: `singleton` (engine, stateless services), `request` (session, transaction context, logger, user context), **transient** (no scope) for stateless orchestrators — use cases and repositories, which receive the request-scoped session by injection. Request-scope state lives in a ContextVar; entered per request by the `request_context` middleware in `src/api/middleware.py`; disposes objects on exit (LIFO, `aclose()` preferred, async `close()` awaited).
- `@inject` required on every implementation whose `__init__` takes dependencies. Construction logic lives in `@provider` methods on `AppModule`.
- Routes/guards: `Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]` — a thin Depends over `app.state.injector`.
- No graph-completeness validation: a missing binding fails at runtime on first resolution.
- Tests: bind mock instances in a `TestModule`, set `app.state.injector = Injector([TestModule()])`; `app.dependency_overrides` for plain guards.

## Session, transactions & repository pattern

- The engine + `async_sessionmaker` are singleton `@provider` methods on `AppModule`; the engine is disposed in `lifespan` shutdown.
- The `AsyncSession` is a request-scoped `@provider` method — every repository and the transaction context in one request share it, and the scope teardown closes it via `aclose()`. Repositories receive the session by constructor, never via ambient state.
- Repository adapters receive the `AsyncSession` by constructor and never commit or roll back. One CRUD operation per method.
- Mutations `flush()`/`execute()` and map DB exceptions to result enums: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`; `DBAPIError` whose `__cause__` is a deadlock → `CONCURRENCY_ERROR`; others → `FAILURE`. Read methods just query. `flush()` populates `id`/server defaults via RETURNING — no `session.refresh()`.
- The use case owns the transaction boundary via the `TransactionContext` port (adapter `SqlAlchemyTransactionContext`): wrap mutations in `async with self._transaction_context.begin() as transaction:` and call `await transaction.commit()` only when every operation succeeded. Rollback-unless-committed.
- Atomic multi-repository operations: call several repositories inside one `begin()` block — they share the request session and succeed or fail together.

## Routes & responses

- Routes return the response **model**; FastAPI serialises it (camelCase via `response_model`). Never return `JSONResponse(model.model_dump())`.
- For result-dependent status, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, and return the model. Use `HTTPException` for read-not-found and auth failures.

## Database (SQLAlchemy)

- Never set `id` or `created_at` in Python; `flush()` RETURNING populates them (no `session.refresh()`).
- Every constraint has an explicit `name`: `uq_`, `fk_`, `ck_`, `ix_`. Declare constraints in `__table_args__`.

## Adding a new entity — layer order

1. Domain: enum → aggregate root (invariants + behaviour) → repository **Protocol** port.
2. Infrastructure: DB model → `sqlalchemy_<entity>_repository.py` adapter (subclasses the port, takes `AsyncSession`).
3. Application: DTO → converter functions → concrete use case (inject `TransactionContext` for mutations; commit only on success).
4. API: routes depending on the use case (return models); add the domain's `register()` in `dependencies/bindings/<entity>.py` (repository + use cases, transient) called from `providers.py`; include router in `main.py`.
5. Tests: entity tests (no mocks), use case tests (mock ports), route tests (bind a mock use case instance in a `TestModule`).

## Code style

Max line length: 140 characters (`skip-magic-trailing-comma = true`).

Never add `# noqa`, `# type: ignore`, or any other lint/type suppression without checking with the user first — propose a design that avoids the violation instead.

## After every change

Remind the user: `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/`
