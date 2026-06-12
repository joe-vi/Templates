# fastapi-clean-architecture-review

A Claude Code skill that audits an existing **FastAPI + Clean Architecture** project for compliance violations. Reads the project one layer at a time to keep token usage low and reports every violation with file path and line number.

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

The audit runs in 6 phases, one layer at a time. Each phase targets a specific part of the architecture:

| Phase | Scope | Clean Architecture rule protected |
|-------|-------|-----------------------------------|
| 1 | Domain | Layer must have zero external dependencies — entities, repository ports (Protocols), and enums only; no imports from any other layer |
| 2 | Application | May only import from Domain — concrete use cases, DTOs, converter functions, service ports (Protocols); no exception handling for mutations |
| 3 | Infrastructure | Repository pattern correctness — one operation per method, result enums returned (never exceptions propagated), adapters take the `AsyncSession` by constructor and never commit/roll back, DB constraints explicitly named |
| 4 | API | Routes depend on the concrete use case via `Depends` providers; guard functions isolated to `dependencies/`; schemas inherit `APIModelBase`; routes return models (no `JSONResponse(model.model_dump())`) |
| 5 | Main / Providers | FastAPI-native wiring — providers wire ports to adapters, resources created/disposed in `lifespan`, no IoC container (`injector`/`@inject`/`InjectorMiddleware`) |
| 6 | Global | Naming discipline — ports are clean-named Protocols, adapters mechanism-qualified, generic result enums (`CreateResult` not `CreateUserResult`), no abbreviations |

Results are reported as a table with file, line, rule violated, and suggested fix. Pass `--fix` to apply fixes automatically.
