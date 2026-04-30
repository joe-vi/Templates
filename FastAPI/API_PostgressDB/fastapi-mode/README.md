# fastapi-mode

A Claude Code skill that activates **FastAPI Clean Architecture** rules for the current session. Every file Claude writes or edits will follow the 4-layer architecture, naming conventions, DI patterns, and repository rules until the session ends.

> **Related skills**
> - [`fastapi-template`](../fastapi-template/) — scaffold a new project
> - [`fastapi-review`](../fastapi-review/) — audit an existing project for violations

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-mode
```

## Usage

```bash
/fastapi-mode
```

That's it. Rules are active for the rest of the session.

## What it enforces

- Layer boundaries — Domain never imports outward; API never imports Infrastructure
- Naming — `Base` suffix on ABCs, `DTO` suffix on DTOs, `Request`/`Response` on schemas
- DI — `@inject` on every constructor, `Injected` not `Depends` in routes, correct middleware order
- Repository pattern — one operation per method, result enums instead of exceptions
- DB constraints — explicit names, DB-generated fields, `session.refresh()` after mutations
- New entity layer order — Domain → Infrastructure → Application → API → container wiring

## When to use

Use `fastapi-mode` when working in a project **without a `CLAUDE.md`**. When activated, Claude will also suggest adding `CLAUDE.md` + `AGENT.md` to make the rules permanent across all future sessions.

Projects scaffolded with `/fastapi-template` already include `CLAUDE.md` — rules are enforced automatically without invoking this skill.
