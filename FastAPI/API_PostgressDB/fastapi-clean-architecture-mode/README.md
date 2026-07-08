# fastapi-clean-architecture-mode

A Claude Code skill that activates **Clean Architecture** rules for the current FastAPI session. Every file Claude writes or edits will follow strict layer boundaries, dependency inversion via `typing.Protocol` ports, the repository pattern with result enums, and declarative Dishka DI discipline until the session ends.

> **Related skills**
> - [`fastapi-clean-architecture-template`](../fastapi-clean-architecture-template/) — scaffold a new project with Clean Architecture enforced from day one
> - [`fastapi-clean-architecture-review`](../fastapi-clean-architecture-review/) — audit an existing project for architecture violations

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-clean-architecture-mode
```

## Usage

```bash
/fastapi-clean-architecture-mode
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
- Use cases depend on `typing.Protocol` ports, never concrete adapters
- The Dishka `AppProvider` in `src/api/dependencies/providers.py` is the only place that wires adapters to ports (the composition root)
- One line binds implementation, port, and scope: `provide(Impl, provides=Port, scope=Scope.REQUEST)`; constructors are auto-wired from type hints and the graph is validated at container creation

**Repository pattern & unit of work**
- One CRUD operation per method — orchestration belongs in use cases, not repositories
- Mutation methods return result enums (`CreateResult`, `UpdateResult`, `DeleteResult`), never raise exceptions to use cases
- Repository adapters receive the request-scoped `AsyncSession` by constructor and never commit or roll back — there is no module-global session state
- The use case owns the transaction boundary via the `TransactionContext` port: commit only on all-success, rollback-unless-committed; repository calls spanning several repositories inside one `begin()` block are atomic

**Dependency injection (Dishka)**
- `AppProvider` declares every binding with an explicit scope (`Scope.APP` / `Scope.REQUEST`); injectable classes carry no decorators
- Routes use `route_class=DishkaRoute` and `FromDishka[UseCase]`; guards use `@inject` + `FromDishka[...]` only in `src/api/dependencies/`
- Tests bind mocks in a small test container (`setup_dishka`); `provide(..., override=True)` overrides real bindings

**Naming discipline**
- Ports are `Protocol`s with clean names (`UserRepository`); adapters are mechanism-qualified (`SqlAlchemyUserRepository`)
- DTOs: frozen dataclasses, `DTO` suffix; `list[UserDTO]` returned directly, no wrapper DTOs
- Converters are module functions; API schemas use `Request`/`Response` suffix and inherit `APIModelBase`
- Result enums: always generic (`CreateResult`, not `CreateUserResult`)

**New entity layer order**
Domain → Infrastructure → Application → API → provider wiring. Claude will follow this order and flag any attempt to skip a layer.

## When to use

Use `fastapi-clean-architecture-mode` when working in a project **without a `CLAUDE.md`**. When activated, Claude will also suggest adding `CLAUDE.md` + `AGENT.md` to make the rules permanent across all future sessions automatically.

Projects scaffolded with `/fastapi-clean-architecture-template` already include `CLAUDE.md` — Clean Architecture rules are enforced without invoking this skill.
