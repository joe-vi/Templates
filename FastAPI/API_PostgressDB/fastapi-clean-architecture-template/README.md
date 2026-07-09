# fastapi-clean-architecture-template

A Claude Code skill that scaffolds a **FastAPI + Clean Architecture** project. The tech stack is configurable; the architecture is not — strict 4-layer structure, unidirectional dependencies, ports-and-adapters, the repository pattern, and result-enum error handling are enforced on every scaffold.

> **Related skills**
> - [`fastapi-clean-architecture-review`](../fastapi-clean-architecture-review/) — audit an existing project for architecture violations
> - [`fastapi-clean-architecture-mode`](../fastapi-clean-architecture-mode/) — activate architecture rules for the current session

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-clean-architecture-template
```

## Usage

```bash
# Default stack (PostgreSQL, JWT, no cache, Docker)
/fastapi-clean-architecture-template my-api

# Custom stack — architecture stays the same, only infrastructure changes
/fastapi-clean-architecture-template my-api --db mongodb --auth oauth2 --cache redis
/fastapi-clean-architecture-template my-api --db sqlite --auth apikey --no-docker
```

## Clean Architecture enforced

Every project is structured around four layers with **dependencies pointing inward only**:

```
API  →  Infrastructure  →  Application  →  Domain
```

| Layer | Location | Responsibility | Can import from |
|-------|----------|----------------|-----------------|
| Domain | `src/domain/` | Entities, repository ports (Protocols), result enums | Nothing |
| Application | `src/application/` | Use cases, DTOs, converter functions, service ports (Protocols) | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, repository/auth adapters, engine + session | Domain + Application |
| API | `src/api/` | Routes, Pydantic schemas, converters, dependency providers | Application + Infrastructure (in `dependencies/`) |

Key architectural patterns enforced on every scaffold regardless of tech stack:

- **Repository pattern** — one CRUD operation per method; mutation methods return result enums (`CreateResult`, `UpdateResult`, `DeleteResult`), never raise exceptions to use cases; repositories never commit — the use case owns the transaction boundary
- **Unit of work** — mutating use cases wrap repository calls in `TransactionContext.begin()` and commit only on all-success; multi-repository operations inside one block are atomic (rollback-unless-committed)
- **Ports & adapters** — use cases depend on `typing.Protocol` ports; adapters (mechanism-qualified, e.g. `SqlAlchemyUserRepository`) structurally satisfy them; `AppModule` in `src/api/dependencies/providers.py` wires them via the typed binder
- **Typed declarative DI (injector + TypedBinder)** — one line binds implementation, port, and scope; a mismatched implementation is a mypy error at the binding line; constructors auto-wired via `@inject`
- **Request-scoped sessions** — one `AsyncSession` per request (request-scoped provider, disposed automatically on request end), shared by every adapter in that request
- **Strict naming** — ports are clean-named Protocols, adapters mechanism-qualified, DTOs end with `DTO`, schemas with `Request`/`Response`; operation result enums are always generic (`CreateResult`, not `CreateUserResult`)
- **Responses** — routes return the response model and let FastAPI serialise it (camelCase); they never hand-build `JSONResponse`
- **DB-generated fields** — `id`, `created_at` are never set in Python; all constraints are explicitly named for safe migrations

## Tech stack options

The only things that change between stacks are `src/infrastructure/` adapters and the bindings in `AppModule` (`src/api/dependencies/providers.py`). All other layers are identical.

| Flag | Values | Default |
|------|--------|---------|
| `--db` | `postgres`, `mongodb`, `sqlite` | `postgres` |
| `--auth` | `jwt`, `oauth2`, `apikey` | `jwt` |
| `--cache` | `none`, `redis` | `none` |
| `--no-docker` | flag | docker enabled |

## What gets generated

```
my-api/
├── src/
│   ├── domain/          # Entities, repository ports (Protocols), result enums — no external deps
│   ├── application/     # Use cases, DTOs, service ports (Protocols) — imports Domain only
│   ├── infrastructure/  # DB models, repository/auth adapters, engine + session — stack-specific
│   └── api/             # FastAPI routes, schemas, dependency providers
├── tests/
├── CLAUDE.md            # Enforces all architecture rules on every future session automatically
├── AGENT.md             # Full architecture reference for developers
├── pyproject.toml
├── docker-compose.yml
└── .env.example
```

`CLAUDE.md` and `AGENT.md` are copied into every project so the architecture rules are enforced automatically on every future Claude Code session — no skill invocation needed after scaffolding.
