---
name: fastapi-review
description: Audit an existing FastAPI Clean Architecture project for rule violations across import direction, naming, DI, repository pattern, DB constraints, enums, auth guards, code style, and documentation. Reports violations with file and line numbers.
argument-hint: "[--fix]"
when_to_use: When you want to check whether an existing FastAPI project follows clean architecture rules, or after making significant changes to verify compliance.
disable-model-invocation: true
version: "1.0.0"
---

# FastAPI Review Skill

Audits the project in the current working directory layer by layer. Pass `--fix` to apply fixes automatically after reporting.

For scaffolding a new project use `/fastapi-template`. To activate rules for the current session use `/fastapi-mode`.

---

## Workflow

Read and audit one layer at a time. Report findings as you go, then produce a final summary. This keeps each read batch small.

### Phase 1 — Domain layer (`src/domain/`)

Read all files in `src/domain/`.

Check:
- **Import direction**: no imports from `src/application/`, `src/infrastructure/`, or `src/api/`
- **Naming**: entity classes are singular nouns; repository interfaces end with `Base`; enums use `StrEnum` with lowercase values and live in `src/domain/enums/`; no entity-specific result enums (e.g. `CreateUserResult` is a violation)
- **Documentation**: every `.py` file has a module docstring; every class has a class docstring; every `__init__` has a docstring; public ABC methods have Google-style docstrings

### Phase 2 — Application layer (`src/application/`)

Read all files in `src/application/`.

Check:
- **Import direction**: no imports from `src/infrastructure/` or `src/api/`
- **Naming**: use case ABCs end with `Base`; DTOs are frozen dataclasses with `DTO` suffix; no wrapper collection DTOs (e.g. `UserListDTO` is a violation); return types use `list[UserDTO]` directly
- **DI**: injectable `__init__` methods have `@inject`
- **Repository pattern**: use cases contain no exception handling for mutations — they forward repository results as-is; no direct session or DB access
- **Documentation**: same rules as Phase 1

### Phase 3 — Infrastructure layer (`src/infrastructure/`)

Read all files in `src/infrastructure/`.

Check:
- **Import direction**: no imports from `src/api/`
- **Repository pattern**:
  - Each method performs exactly one CRUD operation — flag any method that combines read + write
  - Mutation methods catch all exceptions internally and return result enums; nothing propagates
  - Exception mapping: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`, `DeadlockDetectedError` → `CONCURRENCY_ERROR`, all others → `FAILURE`
  - No session parameters in repository constructors or method signatures — repos inject `ConnectionFactoryBase`
  - Every method uses `async with self._connection_factory.get_session()`
- **DB constraints** (SQLAlchemy only):
  - Every `UniqueConstraint`, `ForeignKeyConstraint`, `CheckConstraint`, `Index` has an explicit `name`
  - Naming pattern: `uq_`, `fk_`, `ck_`, `ix_`
  - Constraints declared in `__table_args__`, not as column-level shorthand (except primary key)
  - `id`, `created_at`, `updated_at` never set in Python code
  - `session.refresh()` called after every insert and update
  - `SQLAlchemyEnum` type defined at module level, not inline
- **DI**: `@inject` on every injectable `__init__`; `singleton` scope only on `ConnectionFactory` and external service clients — never on repos
- **Documentation**: same rules as Phase 1

### Phase 4 — API layer (`src/api/`)

Read all files in `src/api/`.

Check:
- **Import direction**: no imports from `src/infrastructure/`
- **Naming**: schemas end with `Request` or `Response` and inherit `APIModelBase`; no bare schema classes
- **DI**:
  - Routes use `Injected(BaseClass)` for use cases and services — flag any `Depends()` used for this purpose
  - `Depends()` only permitted in `src/api/dependencies/` and in `dependencies=[...]` on `APIRouter`
  - Guard functions defined inside route files (should be in `src/api/dependencies/`)
  - `Depends(get_current_user)` in individual route signatures instead of on `APIRouter`
- **Code style**: lines over 80 chars (excluding `# noqa: E501`); `List[X]`, `Optional[X]`, `Dict[K,V]` instead of modern annotations; sync DB calls
- **Documentation**: same rules as Phase 1

### Phase 5 — Container and entry point (`src/container.py`, `src/main.py`)

Read both files.

Check:
- **`main.py` middleware order**: `InjectorMiddleware` added before `attach_injector()`; `attach_injector()` called before `include_router()`
- **`container.py`**: every Base/implementation pair that exists in the codebase has a `binder.bind()` entry; no manual instantiation of injectable classes
- **Singleton scope**: only `ConnectionFactory` and external service clients — flag repos or use cases bound as singleton

### Phase 6 — Global checks

- **Boolean naming**: scan all files for boolean fields/variables not prefixed with `is_`, `has_`, or `can_`
- **Abbreviations**: flag `repo`, `conn`, `svc`, `mgr`, `cfg` anywhere in identifiers
- **Single-letter or vague names**: `g`, `dto`, `result`, `data` as variable names

---

## Report format

```
## Architecture Review — <project-name>

### Violations: <N>

| # | File | Line | Rule | Fix |
|---|------|------|------|-----|
| 1 | src/domain/entities/user.py | 3 | Domain imports from Infrastructure | Remove import of `UserRepository` |
...

### Layer results
- Domain:         ✅ / ⚠️ <N violations>
- Application:    ✅ / ⚠️ <N violations>
- Infrastructure: ✅ / ⚠️ <N violations>
- API:            ✅ / ⚠️ <N violations>
- Container/Main: ✅ / ⚠️ <N violations>
- Global:         ✅ / ⚠️ <N violations>
```

If `--fix` was passed, list every change made after the table.
