# VSCode Multi-Agent Instructions

## Mandatory: Read AGENT.md Before Every Task

Before writing, editing, or reviewing any code in this repository, read the full contents of
AGENT.md. It is the single source of truth for all architecture rules, naming conventions,
patterns, and anti-patterns. **These rules override any general defaults.**

## Architecture (Clean Architecture — 4 Layers)

Dependency direction: Domain → Application → Infrastructure → API (inward only).

- Domain (`src/domain/`): Entities, repository ABCs, enums. No external deps.
- Application (`src/application/`): Use cases, DTOs, converters, service ABCs. Imports Domain only.
- Infrastructure (`src/infrastructure/`): DB models, repository impls, auth impls.
- API (`src/api/`): Routes, schemas, API converters. Imports Application ABCs only.
- DI Container (`src/container.py`): `Binder.bind()` wiring.

## Critical Rules (Quick Reference)

### Naming
- All ABC/interface classes MUST end with `Base` (e.g., `UserRepositoryBase`, `UserUseCaseBase`)
- Operation result enums are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult`
- DTOs: frozen dataclasses with `DTO` suffix; use `list[UserDTO]` directly, never a wrapper DTO class
- API schemas: `Request` suffix for inputs, `Response` suffix for outputs; all inherit from `APIModelBase` (`src/api/schemas/base_schema.py`)
- `APIModelBase`: camelCase JSON serialisation, accepts snake_case or camelCase on input
- Booleans read like questions: `is_active`, `has_items` — never bare nouns
- No abbreviations: `repository` not `repo`, `connection` not `conn`

### Dependency Injection (`fastapi-injector`)
- Every injectable `__init__` MUST have `@inject` from `injector` — omitting causes `TypeError`
- `InjectorMiddleware` MUST be added BEFORE `attach_injector()` in `main.py`
- Routes use `Injected(BaseClass)` for use case/service DI — never `Depends()` for these
- `Depends()` is only permitted in `src/api/dependencies/` for cross-cutting guards

### Repository Pattern
- One CRUD operation per repository method — no combined read+write in one method
- Mutation methods catch all DB exceptions internally and return result enums
- Repositories inject `ConnectionFactoryBase`; use cases inject `TransactionManagerBase` for atomic ops

### Database
- All constraints MUST have an explicit `name` parameter (`uq_`, `fk_`, `ck_`, `ix_` prefix)
- `id`, `created_at`, `updated_at` are DB-generated — never set them in Python code
- Call `session.refresh()` after every insert/update
- All DB operations are async; use `async with self._connection_factory.get_session()`

### Enums
- Use `StrEnum` (Python 3.11+); lowercase values matching DB storage
- All enums live in `src/domain/enums/`

### Code Style
- Max line length: 140 characters
- Run `ruff check src/ --fix && ruff format src/` after every code change
- Always use `uv run` — never access `.venv` directly
- API prefix: `/api/v1`

### Testing
- Use case tests: `AsyncMock(spec=RepositoryBase)` to mock the repository
- Route tests: minimal `FastAPI()` + `TestModule` — never import `src/main.py` or `src/container.py`
- No `@pytest.mark.asyncio` needed (`asyncio_mode = "auto"` is configured)

### Anti-Patterns (Never)
- Do not pass sessions to repository constructors
- Do not inject `ConnectionFactoryBase` into use cases
- Do not use `Depends()` for use case or service injection in routes
- Do not bypass use cases — routes never call repositories directly
- Do not use `singleton` scope for repositories or use cases
- Do not scatter entity files into flat shared directories
