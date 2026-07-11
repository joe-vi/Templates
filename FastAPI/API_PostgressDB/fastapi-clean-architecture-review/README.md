# fastapi-clean-architecture-review

A Claude Code skill that audits an existing **FastAPI + Clean Architecture + DDD** project for compliance violations. Reads the project one layer at a time to keep token usage low and reports every violation with file path and line number.

> **Related skills**
> - [`fastapi-clean-architecture-template`](../fastapi-clean-architecture-template/) — scaffold a new project with Clean Architecture enforced
> - [`fastapi-clean-architecture-mode`](../fastapi-clean-architecture-mode/) — activate architecture rules for the current session

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-clean-architecture-review
```

## Usage

```bash
# Report violations
/fastapi-clean-architecture-review

# Report and auto-fix
/fastapi-clean-architecture-review --fix
```

## What Clean Architecture rules get checked

The audit runs in 7 phases, one layer at a time. Each phase targets a specific part of the architecture:

| Phase | Scope | Rule protected |
|-------|-------|----------------|
| 1 | Domain | Zero external dependencies; rich aggregate roots (invariants + behaviour, never anemic); repository ports (Protocols); enums only; no imports from any other layer |
| 2 | Application | May only import from Domain — concrete use cases, DTOs, converter functions, service ports (Protocols); no exception handling for mutations |
| 3 | Infrastructure | Repository pattern correctness — adapters explicitly subclass their ports, one operation per method, result enums returned (never exceptions propagated), adapters take the `AsyncSession` by constructor and never commit/roll back, DB constraints explicitly named; DI machinery in `infrastructure/di/` |
| 4 | API | Routes depend on the use case via `Injected(...)`; guard functions isolated to `dependencies/`; routes accept/return DTOs directly (`DTOBase` gives camelCase); no per-entity schemas or API converters; routes return models (no `JSONResponse(model.model_dump())`); lines ≤ 140 chars |
| 5 | Main / Providers | Typed injector wiring — `AppModule` binds every port via `TypedBinder` with an explicit scope, request scope entered by middleware, engine disposed in `lifespan`, `@inject` present on implementations |
| 6 | Tests | Domain entities tested without mocks; use cases tested against mocked ports; routes tested against a mocked use case instance in a `TestModule` |
| 7 | Global | Naming + documentation discipline — clean-named Protocol ports, mechanism-qualified adapters, generic result enums (`CreateResult` not `CreateUserResult`), no abbreviations, no module docstrings, contract docs on ports only |

Results are reported as a table with file, line, rule violated, and suggested fix. Pass `--fix` to apply fixes automatically.
