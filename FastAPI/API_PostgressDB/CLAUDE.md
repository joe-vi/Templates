# Claude Code — Codebase Instructions

## Mandatory: Read AGENT.md Before Every Task

Before writing, editing, or reviewing any code in this repository, read the full contents of
[AGENT.md](AGENT.md). It is the single source of truth for all architecture rules, naming
conventions, patterns, and anti-patterns. **These rules override any general defaults.**

## Architecture (Clean Architecture — 4 Layers)

```
Domain → Application → Infrastructure → API
```

Dependencies point **inward only**. Domain never imports from any other layer.

| Layer | Location | Key Rule |
|---|---|---|
| Domain | `src/domain/` | Entities, repository ABCs, enums. No external deps. |
| Application | `src/application/` | Use cases, DTOs, converters, service ABCs. Imports Domain only. |
| Infrastructure | `src/infrastructure/` | DB models, repository impls, auth impls. Imports Domain + Application. |
| API | `src/api/` | Routes, schemas, API converters. Imports Application ABCs only. |
| DI Container | `src/container.py` | `Binder.bind()` wiring. Imports all layers. |

## Critical Rules (Quick Reference)

### Naming
- All ABC/interface classes **must** end with `Base` (`UserRepositoryBase`, `UserUseCaseBase`)
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult` — never entity-specific
- DTOs: frozen dataclasses with `DTO` suffix; use `list[UserDTO]` directly, never a wrapper DTO class
- Booleans read like questions: `is_active`, `has_items` — never bare nouns
- No abbreviations: `repository` not `repo`, `connection` not `conn`

### Dependency Injection (`fastapi-injector`)
- Every injectable `__init__` **must** have `@inject` from `injector` — omitting causes `TypeError`
- `InjectorMiddleware` **must** be added **before** `attach_injector()` in `main.py`
- Routes use `Injected(BaseClass)` for use case/service DI — never `Depends()` for these
- `Depends()` is only permitted in `src/api/dependencies/` for cross-cutting guards

### Repository Pattern
- One CRUD operation per repository method — no combined read+write in one method
- Mutation methods catch all DB exceptions internally and return result enums — nothing propagates to use cases
- Repositories inject `ConnectionFactoryBase`; use cases inject `TransactionManagerBase` for atomic ops

### Database
- All constraints **must** have an explicit `name` parameter (`uq_`, `fk_`, `ck_`, `ix_` prefix)
- `id`, `created_at`, `updated_at` are DB-generated — never set them in Python code
- Call `session.refresh()` after every insert/update
- All DB operations are async; use `async with self._connection_factory.get_session()`

### Enums
- Use `StrEnum` (Python 3.11+); lowercase values matching DB storage
- All enums live in `src/domain/enums/`

### Code Style
- Max line length: **140 characters**
- Run `ruff check src/ --fix && ruff format src/` after every code change
- Always use `uv run` — never access `.venv` directly
- API prefix: `/api/v1`

### Testing
- Use case tests: `AsyncMock(spec=RepositoryBase)` to mock the repository
- Route tests: minimal `FastAPI()` + `TestModule` — never import `src/main.py` or `src/container.py`
- No `@pytest.mark.asyncio` needed (`asyncio_mode = "auto"` is configured)
- Never test infrastructure repositories in unit tests (requires live DB)

### Anti-Patterns (Never)
- Do not pass sessions to repository constructors
- Do not inject `ConnectionFactoryBase` into use cases
- Do not use `Depends()` for use case or service injection in routes
- Do not bypass use cases — routes never call repositories directly
- Do not use `singleton` scope for repositories or use cases
- Do not scatter entity files into flat shared directories
