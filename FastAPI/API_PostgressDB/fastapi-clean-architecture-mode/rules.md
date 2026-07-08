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

The composition root is a **Dishka container**: `AppProvider` in
`src/api/dependencies/providers.py` declares implementation, port, and scope in
one line per binding; the graph is validated at container creation in `main.py`.

## Naming

- Ports are `typing.Protocol`s with the clean name — `UserRepository`, `PasswordHasher`, `TokenService`, `Logger`. No `Base` suffix.
- Adapters are mechanism-qualified — `SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`.
- Use cases are plain concrete classes (`UserUseCase`, `AuthUseCase`) — no separate interface.
- DTOs: frozen dataclasses, `DTO` suffix; return `list[UserDTO]` directly, never a wrapper DTO.
- API schemas: `Request` / `Response` suffix; all inherit `APIModelBase`.
- Converters: module-level functions, never classes of static methods.
- Enums: `StrEnum`, lowercase values, all in `src/domain/enums/`.
- Result enums: always generic — `CreateResult`, `UpdateResult`, `DeleteResult`; never entity-specific.
- Booleans: `is_active`, `has_items`, `can_update` — never bare nouns. No abbreviations.

## Ports & adapters (dependency inversion via Protocol)

- A port is a `typing.Protocol` defining required methods; it lives where it is consumed (repository ports in Domain, service ports in `src/application/services/`).
- An adapter is a plain class that structurally satisfies the port — it does not import or subclass it.
- Use cases take ports as constructor parameters; providers supply the concrete adapter.

## Dependency injection (Dishka)

- Wire everything in `AppProvider` (`src/api/dependencies/providers.py`) — one line per binding: `provide(Impl, provides=Port, scope=Scope.REQUEST)`.
- Explicit scopes: `Scope.APP` (engine, stateless services), `Scope.REQUEST` (session, repositories, transaction context, use cases). Constructors auto-wired from type hints; injectable classes carry no decorators.
- Container built in `main.py`: `make_async_container(AppProvider(), FastapiProvider())` + `setup_dishka(container, app)`; graph validated at creation.
- Routes: `route_class=DishkaRoute` + `use_case: FromDishka[UserUseCase]`. Guards needing container objects use `@inject` + `FromDishka[...]` (only in `src/api/dependencies/`).
- Tests: bind mocks in a test container (`make_async_container(TestProvider())` + `setup_dishka`); `app.dependency_overrides` for plain guards; `provide(..., override=True)` to replace real bindings.

## Session, transactions & repository pattern

- The engine + `async_sessionmaker` are `Scope.APP` providers; `container.close()` in `lifespan` disposes the engine.
- The `AsyncSession` is a `Scope.REQUEST` generator provider — every repository and the transaction context in one request share it, and the scope closes it. No module-global session state, no `ContextVar` for sessions.
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

1. Domain: enum → entity → repository **Protocol** port.
2. Infrastructure: DB model → `sqlalchemy_<entity>_repository.py` adapter (takes `AsyncSession`).
3. Application: DTO → converter functions → concrete use case (inject `TransactionContext` for mutations; commit only on success).
4. API: schema → converter functions → routes (return models); add providers in `dependencies/providers.py`; include router in `main.py`.

## After every change

Remind the user: `uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/`
