# fastapi-mode

A Claude Code skill that activates **Clean Architecture** rules for the current FastAPI session. Every file Claude writes or edits will follow strict layer boundaries, dependency inversion, repository pattern with result enums, and DI discipline until the session ends.

> **Related skills**
> - [`fastapi-template`](../fastapi-template/) — scaffold a new project with Clean Architecture enforced from day one
> - [`fastapi-review`](../fastapi-review/) — audit an existing project for architecture violations

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-mode
```

## Usage

```bash
/fastapi-mode
```

Rules are active for the rest of the session.

## Clean Architecture principles enforced

This skill keeps the following architectural invariants active throughout the session:

**Layer dependency direction — the core rule**
```
API  →  Infrastructure  →  Application  →  Domain
```
Domain has zero external dependencies. Every other layer may only import from the layer(s) inward of it. Violations are flagged before any code is written.

**Abstraction boundaries**
- All use cases and routes depend on ABCs (interfaces), never concrete implementations
- `container.py` is the only place that binds base classes to implementations
- New concrete classes are never instantiated manually — the injector resolves the full chain

**Repository pattern**
- One CRUD operation per method — orchestration belongs in use cases, not repositories
- Mutation methods return result enums (`CreateResult`, `UpdateResult`, `DeleteResult`), never raise exceptions to use cases
- Each repository method opens its own session — sessions are never passed as arguments

**Dependency injection**
- `@inject` on every injectable constructor
- Routes use `Injected(BaseClass)`, never `Depends()` for use cases or services
- `InjectorMiddleware` added before `attach_injector()` in `main.py`

**Naming discipline**
- ABCs: `Base` suffix (`UserRepositoryBase`, `UserUseCaseBase`)
- DTOs: frozen dataclasses, `DTO` suffix; `list[UserDTO]` returned directly, no wrapper DTOs
- API schemas: `Request` / `Response` suffix, all inherit `APIModelBase`
- Result enums: always generic (`CreateResult`, not `CreateUserResult`)

**New entity layer order**
Domain → Infrastructure → Application → API → container wiring. Claude will follow this order and flag any attempt to skip a layer.

## When to use

Use `fastapi-mode` when working in a project **without a `CLAUDE.md`**. When activated, Claude will also suggest adding `CLAUDE.md` + `AGENT.md` to make the rules permanent across all future sessions automatically.

Projects scaffolded with `/fastapi-template` already include `CLAUDE.md` — Clean Architecture rules are enforced without invoking this skill.
