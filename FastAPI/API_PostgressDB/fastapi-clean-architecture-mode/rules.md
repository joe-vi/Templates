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
| API | `src/api/` | Application ABCs only |
| `container.py` | root | All layers |

## Naming

- ABCs: `Base` suffix — `UserRepositoryBase`, `UserUseCaseBase`
- DTOs: frozen dataclasses, `DTO` suffix; return `list[UserDTO]` directly, never a wrapper DTO
- API schemas: `Request` / `Response` suffix; all inherit `APIModelBase`
- Enums: `StrEnum`, lowercase values, all in `src/domain/enums/`
- Result enums: always generic — `CreateResult`, `UpdateResult`, `DeleteResult`; never entity-specific
- Booleans: `is_active`, `has_items`, `can_update` — never bare nouns
- No abbreviations: `repository` not `repo`, `connection` not `conn`

## Dependency injection

- Every injectable `__init__` must have `@inject` from `injector`
- Routes use `Injected(BaseClass)` for use cases/services — never `Depends()` for these
- `Depends()` only in `src/api/dependencies/` and `dependencies=[...]` on `APIRouter`
- `main.py` order: `InjectorMiddleware` → `attach_injector()` → `include_router()`
- `singleton` scope only for `ConnectionFactory` and external service clients

## Repository pattern

- One CRUD operation per method — never combine read + write
- Mutation methods catch all DB exceptions internally and return result enums — nothing propagates
- Exception mapping: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`; `DeadlockDetectedError` → `CONCURRENCY_ERROR`; others → `FAILURE`
- Inject `ConnectionFactoryBase`; open session with `async with self._connection_factory.get_session()`
- Never accept a session parameter

## Database (SQLAlchemy)

- Never set `id`, `created_at`, or `updated_at` in Python
- Call `session.refresh()` after every insert/update
- Every constraint has an explicit `name`: `uq_`, `fk_`, `ck_`, `ix_`
- Declare constraints in `__table_args__`

## Adding a new entity — layer order

1. Domain: enum → entity → repository ABC
2. Infrastructure: DB model → repository implementation
3. Application: DTO → converter → use case ABC → use case implementation
4. API: schema → API converter → routes
5. Wire: `binder.bind()` pairs in `container.py`; include router in `main.py`

## After every change

Remind the user: `uv run ruff check src/ --fix && uv run ruff format src/`
