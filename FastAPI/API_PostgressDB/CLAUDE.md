# Claude Code — Codebase Instructions

## Mandatory: Read AGENT.md Before Every Task

Before writing, editing, or reviewing any code in this repository, read the full contents of
[AGENT.md](AGENT.md). It is the single source of truth for all architecture rules, naming
conventions, patterns, and anti-patterns. **These rules override any general defaults.**

## Architecture (Clean Architecture — 4 Layers)

```
API → Infrastructure → Application → Domain   (dependencies point inward only)
```

Domain never imports from any other layer. The composition root is a **Dishka container** —
`AppProvider` in `src/api/dependencies/providers.py` binds implementation, port, and scope in
one line per binding; the graph is validated at container creation in `main.py`.

| Layer | Location | Key Rule |
|---|---|---|
| Domain | `src/domain/` | Entities, repository ports (Protocols), enums. No external deps. |
| Application | `src/application/` | Use cases, DTOs, converter functions, service ports (Protocols). Imports Domain only. |
| Infrastructure | `src/infrastructure/` | DB models, repository/auth/logging adapters, engine + session. |
| API | `src/api/` | Routes, schemas, converters, dependency providers. Wires adapters to ports. |

## Critical Rules (Quick Reference)

### Naming
- **Ports are `typing.Protocol`s with clean names** (`UserRepository`, `PasswordHasher`, `TokenService`, `Logger`) — no `Base` suffix.
- **Adapters are mechanism-qualified** (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`).
- Use cases are plain concrete classes (`UserUseCase`, `AuthUseCase`) — no separate interface.
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult`.
- DTOs: frozen dataclasses with `DTO` suffix; use `list[UserDTO]` directly.
- API schemas: `Request`/`Response` suffix; all inherit `APIModelBase` (camelCase JSON, accepts either case in).
- Converters are **module functions**, not static-method classes.
- Booleans read like questions (`is_active`); no abbreviations (`repository` not `repo`).

### Dependency Injection (FastAPI `Depends`)
- The composition root is the Dishka `AppProvider` (`src/api/dependencies/providers.py`): one line per binding — `provide(Impl, provides=Port, scope=Scope.REQUEST)`; constructors auto-wired from type hints; graph validated at container creation in `main.py`.
- Scopes are explicit: `Scope.APP` (engine, stateless services) and `Scope.REQUEST` (session, repositories, transaction context, use cases). Resources use generator providers (`yield` + cleanup).
- Routes use `route_class=DishkaRoute` and `use_case: FromDishka[UserUseCase]`. Guards needing container objects use `@inject` + `FromDishka[...]` (only in `src/api/dependencies/`).
- **No** `injector`, **no** `@inject`, **no** `InjectorMiddleware`. Override providers in tests with `app.dependency_overrides`.

### Session, Transactions & Repositories
- The engine + `async_sessionmaker` are `Scope.APP` providers; `container.close()` in `lifespan` disposes the engine.
- The `AsyncSession` is a **REQUEST-scoped generator provider** in `AppProvider`; every repository and the transaction context in one request share it, and the scope closes it. No module-global session state, no `ContextVar` for sessions.
- Repository **adapters receive the `AsyncSession`** via constructor and **never commit or roll back**. Mutations `flush()`/`execute()` and map DB errors to result enums (`IntegrityError`→`UNIQUE_CONSTRAINT_ERROR`; deadlock→`CONCURRENCY_ERROR`; else `FAILURE`). Reads just query. `flush()` populates `id`/server defaults via RETURNING — no `session.refresh()`.
- **The use case owns the transaction boundary** via the `TransactionContext` port (adapter `SqlAlchemyTransactionContext`): wrap mutations in `async with self._transaction_context.begin() as transaction:`; call `await transaction.commit()` only when every operation succeeded. Rollback-unless-committed.
- **Atomic multi-repository operations**: call several repositories inside one `begin()` block — they share the request session and succeed or fail together.
- One CRUD operation per repository method.

### Routes & Responses
- Routes **return the response model**; FastAPI serialises it (camelCase). Never return `JSONResponse(model.model_dump())`.
- For result-dependent status, inject `response: Response`, set `response.status_code = result_status_maps.<OP>_STATUS_MAP[result]`, return the model. Use `HTTPException` for not-found / auth failures.

### Auth
- `get_current_user` decodes the Bearer JWT, raises 401, records the user id in the logging context, returns `TokenClaimsDTO`. Protect routers with `dependencies=[Depends(get_current_user)]`.
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
- Do not add an IoC container or `@inject`; use FastAPI `Depends` providers.
- Do not keep session state in a module-global `ContextVar`; inject the request-scoped session.
- Do not pass sessions to use cases.
- Do not commit or roll back inside repositories — the use case owns the boundary via `TransactionContext`.
- Do not call `transaction.commit()` after any failed result in the block.
- Do not return `JSONResponse(model.model_dump())` from routes.
- Do not make ports ABCs or suffix them `Base`; use `Protocol`.
- Do not create classes of only static methods; use module functions.
- Do not bypass use cases — routes never call repositories directly.
