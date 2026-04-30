# fastapi-review

A Claude Code skill that audits an existing **FastAPI Clean Architecture** project for rule violations. Reads the project layer by layer to keep token usage low and reports every violation with file path and line number.

> **Related skills**
> - [`fastapi-template`](../fastapi-template/) — scaffold a new project
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

## What gets checked

The audit runs in 6 phases, one layer at a time:

| Phase | Scope | Key checks |
|-------|-------|------------|
| 1 | Domain | Import direction, entity/enum naming, ABC `Base` suffix, documentation |
| 2 | Application | Import direction, DTO naming, no exception handling in use cases |
| 3 | Infrastructure | Repository pattern, DB constraint naming, `@inject`, session handling |
| 4 | API | Schema naming, `Injected` vs `Depends`, guard placement, code style |
| 5 | Container + Main | Middleware order, missing bindings, singleton scope misuse |
| 6 | Global | Boolean naming, abbreviations, vague variable names |

Results are reported as a table with file, line, rule violated, and suggested fix. Pass `--fix` to apply fixes automatically.
