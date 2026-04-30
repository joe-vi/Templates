---
name: fastapi-clean-architecture-mode
description: Activate Clean Architecture rules for the current FastAPI session — enforces unidirectional layer dependencies, repository pattern with result enums, dependency inversion via fastapi-injector, and all naming conventions on every file written or edited until the session ends.
when_to_use: When working in a FastAPI project that has no CLAUDE.md and you want Clean Architecture rules — strict layer boundaries, dependency inversion, repository pattern, DI discipline — enforced for this session without scaffolding or running a full audit.
mode: true
disable-model-invocation: true
version: "1.0.0"
---

# FastAPI Clean Architecture — Mode Skill

Activates all Clean Architecture rules for the current FastAPI session. Everything Claude writes or edits from this point will follow the 4-layer structure, dependency direction, repository pattern, and naming discipline defined in AGENT.md.

For scaffolding a new project use `/fastapi-clean-architecture-template`. To audit an existing project use `/fastapi-clean-architecture-review`.

---

## On activation

1. Confirm: "FastAPI Clean Architecture mode is active. All architecture rules are now enforced for this session."
2. If the project has no `CLAUDE.md`, suggest at the end: "Add `CLAUDE.md` + `AGENT.md` from `FastAPI/API_PostgressDB/` in `joe-vi/templates` to enforce these rules automatically on every future session."
3. Apply the rules below to every file written or edited from this point.

---

## Rules

### Clean Architecture layer boundaries (enforce on every file)

```
Domain → Application → Infrastructure → API
```

- Domain (`src/domain/`): no imports from any other layer
- Application (`src/application/`): imports Domain only
- Infrastructure (`src/infrastructure/`): imports Domain + Application
- API (`src/api/`): imports Application ABCs only
- `container.py`: only file that imports all layers

### Naming (flag before writing)

- ABCs must end with `Base` — `UserRepositoryBase`, `UserUseCaseBase`
- DTOs: frozen dataclasses, `DTO` suffix; return `list[UserDTO]` directly, never a wrapper DTO
- API schemas: `Request` (input) / `Response` (output) suffix; must inherit `APIModelBase`
- Enums: `StrEnum`, lowercase values, live in `src/domain/enums/`
- Result enums: always generic — `CreateResult`, `UpdateResult`, `DeleteResult`; never entity-specific
- Booleans: `is_active`, `has_items`, `can_update` — never bare nouns
- No abbreviations: `repository` not `repo`, `connection` not `conn`

### Dependency injection

- Every injectable `__init__` must have `@inject` from `injector`
- Routes use `Injected(BaseClass)` for use cases/services — never `Depends()` for these
- `Depends()` only in `src/api/dependencies/` and `dependencies=[...]` on `APIRouter`
- `main.py` order: `InjectorMiddleware` → `attach_injector()` → `include_router()`
- `singleton` scope only for `ConnectionFactory` and external service clients

### Repository pattern

- One CRUD operation per method — never combine read + write
- Mutation methods catch all DB exceptions internally and return result enums
- Exception mapping: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`; `DeadlockDetectedError` → `CONCURRENCY_ERROR`; others → `FAILURE`
- Inject `ConnectionFactoryBase`; open session with `async with self._connection_factory.get_session()`
- Never accept a session parameter

### Database (SQLAlchemy)

- Never set `id`, `created_at`, or `updated_at` in Python
- Call `session.refresh()` after every insert/update
- Every constraint has an explicit `name`: `uq_`, `fk_`, `ck_`, `ix_`
- Declare constraints in `__table_args__`

### Adding a new entity — layer order

1. Domain: enum → entity → repository ABC
2. Infrastructure: DB model → repository implementation
3. Application: DTO → converter → use case ABC → use case implementation
4. API: schema → API converter → routes
5. Wire: `binder.bind()` pairs in `container.py`; include router in `main.py`

### After every change

Remind the user: `uv run ruff check src/ --fix && uv run ruff format src/`
