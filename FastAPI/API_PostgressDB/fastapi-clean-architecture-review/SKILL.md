---
name: fastapi-clean-architecture-review
description: Audit an existing FastAPI project for Clean Architecture compliance — verifies unidirectional layer dependencies, ports-as-Protocol boundaries, repository pattern correctness, typed declarative DI wiring (injector + TypedBinder, explicit scopes, mypy-checked binding conformance), naming conventions, DB constraint rules, and documentation standards. Reports every violation with file and line number.
argument-hint: "[--fix]"
disable-model-invocation: true
metadata:
  version: "2.0.0"
---

# FastAPI Clean Architecture — Review Skill

Audits the project in the current working directory for Clean Architecture compliance, reading one layer at a time. Every violation is reported with its file, line, the architectural rule broken, and how to fix it. Pass `--fix` to apply fixes automatically after reporting.

For scaffolding a new project use `/fastapi-clean-architecture-template`. To activate rules for the current session use `/fastapi-clean-architecture-mode`.

---

## Workflow

Read and audit one layer at a time. Report findings as you go, then produce a final summary. This keeps each read batch small.

### Phase 1 — Domain layer (`src/domain/`)

Read all files in `src/domain/`.

Check:
- **Import direction**: no imports from `src/application/`, `src/infrastructure/`, or `src/api/`
- **Naming**: entity classes are singular nouns; repository ports are `typing.Protocol`s with clean names (`UserRepository`, not `UserRepositoryBase`); enums use `StrEnum` with lowercase values and live in `src/domain/enums/`; no entity-specific result enums (e.g. `CreateUserResult` is a violation)
- **Documentation**: every `.py` file has a module docstring; every class has a class docstring; port methods carry Google-style docstrings

### Phase 2 — Application layer (`src/application/`)

Read all files in `src/application/`.

Check:
- **Import direction**: no imports from `src/infrastructure/` or `src/api/`
- **Naming**: service ports are `Protocol`s with clean names (`PasswordHasher`, `TokenService`, `Logger`); use cases are plain concrete classes (no `Base` ABC); DTOs are frozen dataclasses with `DTO` suffix; no wrapper collection DTOs; return types use `list[UserDTO]` directly
- **Converters**: module-level functions, not classes of static methods
- **Repository pattern**: use cases contain no exception handling for mutations — they forward repository results as-is; no direct session or DB access; no `@inject`
- **Transactions**: mutating use-case methods wrap repository calls in `TransactionContext.begin()` and call `transaction.commit()` only on the all-success path — flag any mutation outside a transaction block and any commit after a failed result
- **Documentation**: same rules as Phase 1

### Phase 3 — Infrastructure layer (`src/infrastructure/`)

Read all files in `src/infrastructure/`.

Check:
- **Import direction**: no imports from `src/api/`
- **Naming**: adapters are mechanism-qualified (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`)
- **Repository pattern**:
  - Each method performs exactly one CRUD operation — flag any method that combines read + write
  - Mutation methods catch DB exceptions internally and return result enums; nothing propagates
  - Exception mapping: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`, deadlock (`DBAPIError.__cause__`) → `CONCURRENCY_ERROR`, all others → `FAILURE`
  - Adapters receive the `AsyncSession` by constructor injection — flag any module-global session state or `ContextVar`-based session sharing
  - Repositories never commit or roll back — flag any `session.commit()`/`session.rollback()` in a repository; the transaction boundary belongs to the use case via `TransactionContext`
- **DB constraints** (SQLAlchemy only):
  - Every `UniqueConstraint`, `ForeignKeyConstraint`, `CheckConstraint`, `Index` has an explicit `name` (`uq_`, `fk_`, `ck_`, `ix_`)
  - Constraints declared in `__table_args__` (except primary key)
  - `id`, `created_at` never set in Python code; `flush()` RETURNING populates them (flag `session.refresh()` after inserts)
  - `SQLAlchemyEnum` type defined at module level, not inline
- **Documentation**: same rules as Phase 1

### Phase 4 — API layer (`src/api/`)

Read all files in `src/api/`.

Check:
- **Naming**: schemas end with `Request` or `Response` and inherit `APIModelBase`; converters are module functions
- **DI**:
  - Composition root is `AppModule.configure()` in `src/api/dependencies/providers.py` — one `bind_typed(Port).to(Impl, scope=...)` line per binding via `TypedBinder`; flag raw `binder.bind(...)` calls for port bindings (they skip conformance checking) and any `fastapi-injector` usage
  - Every implementation whose `__init__` takes dependencies carries `@inject`; flag missing ones (runtime `TypeError`)
  - Routes depend on the concrete use case via `Annotated[UseCase, Injected(UseCase)]`
  - Guard functions live in `src/api/dependencies/`, not inside route files; `Depends(get_current_user)` declared on the `APIRouter`, not scattered in signatures
- **Responses**: routes return the response model (FastAPI serialises it to camelCase). Flag any `JSONResponse(model.model_dump())` — it bypasses `response_model` and the alias generator. Dynamic status set via `response.status_code`.
- **Code style**: lines over 80 chars (excluding `# noqa: E501`); `List[X]`, `Optional[X]`, `Dict[K,V]` instead of modern annotations; sync DB calls
- **Documentation**: same rules as Phase 1

### Phase 5 — Entry point (`src/main.py`)

Read `src/main.py` and `src/api/dependencies/`.

Check:
- **Injector**: `Injector([AppModule()])` at module level, stored on `app.state.injector`; the `request_context` middleware enters `async_request_scope()` per request; `lifespan` disposes the engine on shutdown
- **Legacy DI**: flag any `fastapi-injector` package usage (`InjectorMiddleware`, `attach_injector`) — this template uses its own `injection.py`
- **Bindings**: every port bound via `TypedBinder` with an explicit scope; the session is a request-scoped `@provider`; singletons holding connections are disposed in `lifespan`

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
| 1 | src/domain/entities/user.py | 3 | Domain imports from Infrastructure | Remove import of `SqlAlchemyUserRepository` |
...

### Layer results
- Domain:         ✅ / ⚠️ <N violations>
- Application:    ✅ / ⚠️ <N violations>
- Infrastructure: ✅ / ⚠️ <N violations>
- API:            ✅ / ⚠️ <N violations>
- Main/Providers: ✅ / ⚠️ <N violations>
- Global:         ✅ / ⚠️ <N violations>
```

If `--fix` was passed, list every change made after the table.
