# fastapi-template

A Claude Code skill that scaffolds production-ready **FastAPI Clean Architecture** projects or audits existing ones for architecture compliance.

## Install

```bash
npx skills add joe-vi/templates --skill fastapi-template
```

## Usage

### Scaffold a new project

```bash
/fastapi-template scaffold my-api
```

With a custom tech stack:

```bash
/fastapi-template scaffold my-api --db mongodb --auth oauth2 --cache redis
/fastapi-template scaffold my-api --db sqlite --auth apikey --no-docker
```

### Audit an existing project

```bash
/fastapi-template review
/fastapi-template review --fix
```

---

## What gets generated

The skill creates a fully wired **4-layer Clean Architecture** project:

```
my-api/
├── src/
│   ├── domain/          # Entities, repository ABCs, result enums
│   ├── application/     # Use cases, DTOs, service ABCs
│   ├── infrastructure/  # DB models, repository impls, auth impls
│   └── api/             # FastAPI routes, Pydantic schemas
├── tests/
├── CLAUDE.md            # Architecture rules for future Claude sessions
├── AGENT.md             # Full architecture reference
├── pyproject.toml
├── docker-compose.yml
└── .env.example
```

---

## Tech stack options

| Option | Values | Default |
|--------|--------|---------|
| `--db` | `postgres`, `mongodb`, `sqlite` | `postgres` |
| `--auth` | `jwt`, `oauth2`, `apikey` | `jwt` |
| `--cache` | `none`, `redis` | `none` |
| `--no-docker` | flag | docker enabled |

The **domain**, **application**, and **API** layers are identical regardless of stack. Only `src/infrastructure/` and `src/container.py` adapt to the chosen database and auth strategy.

---

## Review mode

Running `/fastapi-template review` checks 9 rule categories against your existing codebase:

1. Import direction (domain never imports outward)
2. Naming conventions (Base suffix, DTO, Request/Response schemas)
3. Dependency injection (`@inject`, `Injected` vs `Depends`, middleware order)
4. Repository pattern (one operation per method, exception handling)
5. Database constraints (explicit names, DB-generated fields)
6. Enums (`StrEnum`, lowercase values, correct location)
7. Authentication guards (guard placement, router-level `Depends`)
8. Code style (line length, modern type annotations, async)
9. Documentation (module, class, `__init__`, and ABC docstrings)

Add `--fix` to apply fixes automatically after the report.

---

## Architecture enforced

- Dependencies point **inward only** — Domain has no external imports
- `fastapi-injector` for DI — `Injected(BaseClass)` in routes, `@inject` on every constructor
- Repositories return result enums — no exceptions propagate to use cases
- `TransactionManagerBase` for atomic multi-repository operations
- `ConnectionFactory` with `ContextVar` session sharing inside transactions
- All constraints explicitly named for safe Alembic migrations
- `CLAUDE.md` + `AGENT.md` copied into every scaffolded project so future sessions stay compliant
