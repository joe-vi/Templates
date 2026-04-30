# fastapi-template

A Claude Code skill that scaffolds a **FastAPI + Clean Architecture** project. The tech stack is configurable; the architecture is not — strict 4-layer structure, unidirectional dependencies, repository pattern, and result-enum error handling are enforced on every scaffold.

> **Related skills**
> - [`fastapi-review`](../fastapi-review/) — audit an existing project for architecture violations
> - [`fastapi-mode`](../fastapi-mode/) — activate architecture rules for the current session

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-template
```

## Usage

```bash
# Default stack (PostgreSQL, JWT, no cache, Docker)
/fastapi-template my-api

# Custom stack — architecture stays the same, only infrastructure changes
/fastapi-template my-api --db mongodb --auth oauth2 --cache redis
/fastapi-template my-api --db sqlite --auth apikey --no-docker
```

## Clean Architecture enforced

Every project is structured around four layers with **dependencies pointing inward only**:

```
API  →  Infrastructure  →  Application  →  Domain
```

| Layer | Location | Responsibility | Can import from |
|-------|----------|----------------|-----------------|
| Domain | `src/domain/` | Entities, repository interfaces (ABCs), result enums | Nothing |
| Application | `src/application/` | Use cases, DTOs, service interfaces | Domain only |
| Infrastructure | `src/infrastructure/` | DB models, repository implementations, auth | Domain + Application |
| API | `src/api/` | Routes, Pydantic schemas, request/response converters | Application ABCs only |

Key architectural patterns enforced on every scaffold regardless of tech stack:

- **Repository pattern** — one CRUD operation per method; mutation methods return result enums (`CreateResult`, `UpdateResult`, `DeleteResult`), never raise exceptions to use cases
- **Dependency inversion** — all use cases and routes depend on ABCs, never concrete implementations; `container.py` is the only place that wires base classes to implementations
- **Explicit DI** — `fastapi-injector` with `@inject` on every constructor; `Injected(BaseClass)` in routes, never `Depends()` for use cases
- **Strict naming** — ABCs end with `Base`, DTOs with `DTO`, schemas with `Request`/`Response`; operation result enums are always generic (`CreateResult`, not `CreateUserResult`)
- **DB-generated fields** — `id`, `created_at`, `updated_at` are never set in Python; all constraints are explicitly named for safe migrations

## Tech stack options

The only things that change between stacks are `src/infrastructure/` implementations and `src/container.py` bindings. All other layers are identical.

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
│   ├── domain/          # Entities, repository ABCs, result enums — no external deps
│   ├── application/     # Use cases, DTOs, service ABCs — imports Domain only
│   ├── infrastructure/  # DB models, repository impls, auth — stack-specific
│   └── api/             # FastAPI routes, Pydantic schemas — imports Application ABCs
├── tests/
├── CLAUDE.md            # Enforces all architecture rules on every future session automatically
├── AGENT.md             # Full architecture reference for developers
├── pyproject.toml
├── docker-compose.yml
└── .env.example
```

`CLAUDE.md` and `AGENT.md` are copied into every project so the architecture rules are enforced automatically on every future Claude Code session — no skill invocation needed after scaffolding.
