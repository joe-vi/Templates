---
name: fastapi-clean-architecture-review
description: Audit an existing FastAPI project for Clean Architecture + DDD compliance — verifies unidirectional layer dependencies, rich (non-anemic) domain entities, ports-as-Protocol boundaries with single-source documentation, repository pattern correctness, typed declarative DI wiring (injector + TypedBinder, explicit scopes, pyrefly-checked binding conformance), naming conventions, DB constraint rules, and documentation standards. Reports every violation with file and line number.
argument-hint: "[--fix]"
disable-model-invocation: true
metadata:
  version: "3.0.0"
---

# FastAPI Clean Architecture — Review Skill

Audits the project in the current working directory for Clean Architecture + DDD compliance, reading one layer at a time. Every violation is reported with its file, line, the architectural rule broken, and how to fix it. Pass `--fix` to apply fixes automatically after reporting.

For scaffolding a new project use `/fastapi-clean-architecture-template`. To activate rules for the current session use `/fastapi-clean-architecture-mode`.

---

## Documentation rules (applied in every phase)

- **No module docstrings and no top-of-file comments** — flag any file that has them.
- **The contract is documented once, on the port**: Protocol classes and methods carry full Google-style docstrings; adapters **explicitly subclass their port** and inherit them. Flag duplicated method docstrings on adapters, and flag adapters that do not subclass their port. Classes with no port — the use cases — carry their own method docstrings.
- Implementation classes may keep a short class docstring with mechanism-specific notes only; `__init__` methods carry no docstrings.
- Standalone public functions (converters, providers, guards, routes) carry their own docstrings.

## Workflow

Read and audit one layer at a time. Report findings as you go, then produce a final summary. This keeps each read batch small.

### Phase 1 — Domain layer (`src/domain/`)

Read all files in `src/domain/`.

Check:
- **Import direction**: no imports from `src/application/`, `src/infrastructure/`, or `src/api/`; stdlib only (`dataclasses`, `enum`, `typing`)
- **DDD richness**: entities are aggregate roots with behaviour — invariants enforced in `__post_init__` (raising `ValueError`) and intention-revealing state transitions (e.g. `activate()`/`deactivate()`, `is_active`). Flag anemic entities (bare field bags) and domain rules implemented in use cases that belong on the entity
- **Naming**: entity classes are singular nouns; repository ports are `typing.Protocol`s with clean names (`UserRepository`, not `UserRepositoryBase`); one repository port per aggregate root; enums use `StrEnum` with lowercase values and live in `src/domain/enums/`; no entity-specific result enums (e.g. `CreateUserResult` is a violation)
- **Documentation**: port methods carry Google-style docstrings (the single source); see documentation rules above

### Phase 2 — Application layer (`src/application/`)

Read all files in `src/application/`.

Check:
- **Import direction**: no imports from `src/infrastructure/` or `src/api/`
- **Use cases**: one plain concrete class per operation in its own file, each with a single `execute` method (`CreateUserUseCase`) — no separate ABC or Protocol interface; each declares only the ports its operation needs
- **Naming**: service ports are `Protocol`s with clean names (`PasswordHasher`, `TokenService`, `Logger`); DTOs are frozen Pydantic models inheriting `DTOBase` with `DTO` suffix; no wrapper collection DTOs; return types use `list[UserDTO]` directly
- **Converters**: module-level functions, not classes of static methods
- **Repository pattern**: use cases contain no exception handling for mutations — they forward repository results as-is; no direct session or DB access
- **Transactions**: mutating use-case methods wrap repository calls in `TransactionContext.begin()` and call `transaction.commit()` only on the all-success path — flag any mutation outside a transaction block and any commit after a failed result
- **Documentation**: use case methods carry their own Google-style docstrings (no port to inherit from)

### Phase 3 — Infrastructure layer (`src/infrastructure/`)

Read all files in `src/infrastructure/`.

Check:
- **Import direction**: no imports from `src/api/`
- **Naming**: adapters are mechanism-qualified (`SqlAlchemyUserRepository`, `BcryptPasswordHasher`, `JwtTokenService`, `JsonLogger`) and explicitly subclass their ports
- **DI machinery**: the injector extensions (`request_scope.py`, `typed_binder.py`) live in `src/infrastructure/di/` — flag them living inside `src/api/`
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
- **Documentation**: adapters inherit port docs; see documentation rules above

### Phase 4 — API layer (`src/api/`)

Read all files in `src/api/`.

Check:
- **Naming**: DTOs inherit `DTOBase` and double as request/response bodies (no per-entity `Request`/`Response` schemas, no API converters); the entity↔DTO converters are module functions
- **DI**:
  - Composition root is `AppModule.configure()` in `src/api/dependencies/providers.py` — one `bind_typed(Port).to(Impl, scope=...)` line per binding via `TypedBinder`; flag raw `binder.bind(...)` calls for port bindings (they skip conformance checking) and any `fastapi-injector` usage
  - Every implementation whose `__init__` takes dependencies carries `@inject`; flag missing ones (runtime `TypeError`)
  - Each route module covers one operation, depends on its use case via `Annotated[CreateUserUseCase, Injected(CreateUserUseCase)]`, and attaches directly to the shared `APIRouter` defined once in the entity's `router.py` (prefix, tags, guard declared there); `__init__.py` stays empty
  - Guard functions live in `src/api/dependencies/`, not inside route files; `Depends(get_current_user)` declared on the `APIRouter`, not scattered in signatures
- **Responses**: routes return the response model (FastAPI serialises it to camelCase). Flag any `JSONResponse(model.model_dump())` — it bypasses `response_model` and the alias generator. Dynamic status set via `response.status_code`.
- **Code style**: lines over 140 chars; `List[X]`, `Optional[X]`, `Dict[K,V]` instead of modern annotations; sync DB calls
- **Documentation**: route docstrings describe endpoint behaviour (they become OpenAPI descriptions), not injected parameters

### Phase 5 — Entry point (`src/main.py`)

Read `src/main.py` and `src/api/dependencies/`.

Check:
- **Injector**: `Injector([AppModule()])` at module level, stored on `app.state.injector`; the `request_context` middleware enters `async_request_scope()` per request; `lifespan` disposes the engine on shutdown
- **Legacy DI**: flag any `fastapi-injector` package usage (`InjectorMiddleware`, `attach_injector`) — this template uses its own `src/infrastructure/di/` machinery plus `injected.py`
- **Bindings**: every port bound via `TypedBinder` with an explicit scope; the session is a request-scoped `@provider`; singletons holding connections are disposed in `lifespan`

### Phase 6 — Tests (`tests/`)

Check:
- Domain entities have pure unit tests in `tests/domain/` (no mocks, no I/O)
- Use case tests mock the ports (`AsyncMock(spec=UserRepository)`) and assert transaction boundaries via a fake `TransactionContext`
- Route tests bind a mock use case instance in a `TestModule` on `app.state.injector` — flag tests importing `src/main.py`

### Phase 7 — Global checks

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
- Tests:          ✅ / ⚠️ <N violations>
- Global:         ✅ / ⚠️ <N violations>
```

If `--fix` was passed, list every change made after the table.
