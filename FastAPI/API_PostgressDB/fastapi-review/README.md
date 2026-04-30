# fastapi-review

A Claude Code skill that audits an existing **FastAPI + Clean Architecture** project for compliance violations. Reads the project one layer at a time to keep token usage low and reports every violation with file path and line number.

> **Related skills**
> - [`fastapi-template`](../fastapi-template/) — scaffold a new project with Clean Architecture enforced
> - [`fastapi-mode`](../fastapi-mode/) — activate architecture rules for the current session

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-review
```

## Usage

```bash
# Report violations
/fastapi-review

# Report and auto-fix
/fastapi-review --fix
```

## What Clean Architecture rules get checked

The audit runs in 6 phases, one layer at a time. Each phase targets a specific part of the architecture:

| Phase | Scope | Clean Architecture rule protected |
|-------|-------|-----------------------------------|
| 1 | Domain | Layer must have zero external dependencies — entities, ABCs, and enums only; no imports from any other layer |
| 2 | Application | May only import from Domain — use case ABCs, DTOs, converters, service ABCs; no exception handling for mutations |
| 3 | Infrastructure | Repository pattern correctness — one operation per method, result enums returned (never exceptions propagated), DB constraints explicitly named |
| 4 | API | Routes depend on Application ABCs only — `Injected(BaseClass)` not `Depends()`, guard functions isolated to `dependencies/`, schemas inherit `APIModelBase` |
| 5 | Container + Main | DI wiring completeness — every Base/implementation pair bound, `InjectorMiddleware` before `attach_injector()`, singleton scope only on appropriate types |
| 6 | Global | Naming discipline — `Base` suffix on ABCs, `DTO` suffix on DTOs, generic result enums (`CreateResult` not `CreateUserResult`), no abbreviations |

Results are reported as a table with file, line, rule violated, and suggested fix. Pass `--fix` to apply fixes automatically.
