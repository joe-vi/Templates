# fastapi-template

A Claude Code skill that scaffolds a production-ready **FastAPI Clean Architecture** project with your choice of database, auth strategy, and cache layer.

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

# Custom stack
/fastapi-template my-api --db mongodb --auth oauth2 --cache redis
/fastapi-template my-api --db sqlite --auth apikey --no-docker
```

## Tech stack options

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
│   ├── domain/          # Entities, repository ABCs, result enums
│   ├── application/     # Use cases, DTOs, service ABCs
│   ├── infrastructure/  # DB models, repository impls, auth impls
│   └── api/             # FastAPI routes, Pydantic schemas
├── tests/
├── CLAUDE.md            # Enforces architecture rules on every future session
├── AGENT.md
├── pyproject.toml
├── docker-compose.yml
└── .env.example
```

The **domain**, **application**, and **API** layers are identical regardless of stack. Only `src/infrastructure/` and `src/container.py` adapt to the chosen database and auth strategy.

`CLAUDE.md` is copied into every project so architecture rules are enforced automatically on every future Claude Code session — no need to invoke any skill again.
