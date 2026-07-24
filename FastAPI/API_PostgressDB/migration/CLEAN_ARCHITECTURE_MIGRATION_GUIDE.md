# Clean Architecture Migration Guide — FastAPI + PostgreSQL

Instructions and guidelines for converting an existing FastAPI codebase into the
Clean Architecture + DDD layout of this template. This file is **reference material**, not a
prompt. The executable instruction that consumes it is [MIGRATION_PROMPT.md](MIGRATION_PROMPT.md).

The template this describes is the source of truth for every pattern below. Where this guide says
"copy verbatim", copy the bytes from the template repository — do not retype or improve.

---

## 0. Scope and ground rules

**What migration means here:** every file of the source project ends up in one of three states —
*moved and rewritten* into a layer directory, *replaced* by a chassis file from the template, or
*deleted* with its behaviour accounted for elsewhere. Nothing is left in the old location. A
migration that leaves `app/` or `api/` alongside `src/` is not finished.

**Behaviour is preserved.** Every route the source project served must still be served after
migration, at its new URL. Every business rule must still be enforced. Migration is restructuring,
not redesign: do not add features, do not drop endpoints, do not "fix" business logic in passing.
Record any rule you cannot place cleanly and raise it instead of silently changing it.

**The four gates.** Work is not done until all four pass:

```bash
uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/
uv run pyrefly check
uv run pytest
uv run pre-commit run --all-files
```

**Never suppress.** No `# noqa`, no `# type: ignore`, no pyrefly ignore comments to make a gate
pass. If a rule can only be satisfied with a suppression, stop and present the design alternatives.
The one pre-existing exception in the template is `alembic/env.py`'s `# noqa: F401` on the model
import — that import exists for its side effect (registering ORM models with `Base.metadata`) and
is copied as-is.

---

## 1. Target architecture

Four layers. Dependencies flow **inward only**: API → Infrastructure → Application → Domain.
Domain imports nothing but the standard library. `src/ports/` and `src/shared/` are dependency-free
**leaves** that every layer except Domain may import.

| Layer | Location | Contains | May import |
|-------|----------|----------|------------|
| Domain | `src/domain/` | Entities (aggregate roots with invariants + behaviour), repository ports (Protocols), enums | stdlib only (`dataclasses`, `enum`, `typing`) |
| Ports (leaf) | `src/ports/` | Technical service ports (Protocols) + any type a port returns (`TokenClaims`) | Domain enums + `src/shared/` |
| Application | `src/application/` | Use cases (concrete classes), request/response contracts, converter functions | Domain + Ports |
| Infrastructure | `src/infrastructure/` | ORM models, repository/auth/logging adapters, engine + session, DI machinery | Domain + Ports + Application |
| API | `src/api/` | Routes, operation envelopes, composition root, middleware | Application + Infrastructure (adapters only inside `dependencies/`) |

The composition root is `AppModule` in `src/api/dependencies/providers.py`, built on the `injector`
library plus in-house machinery in `src/infrastructure/di/`. One line binds implementation, port,
and scope; a mismatched implementation is a pyrefly error at that line. There is **no
graph-completeness validation** — a missing binding fails at runtime on first resolution, so the
smoke test in §13 is not optional.

---

## 2. Target file tree

This is the complete shape of the destination. `<entity>` is the singular, lowercase aggregate name
(`user`, `order`, `invoice`). Every entity gets a folder in each layer that concerns it — never
scatter entity files into flat shared directories.

```
.
├── .env                      # local, gitignored
├── .env.example              # every setting, with safe defaults
├── .dockerignore
├── .pre-commit-config.yaml   # §10.2
├── AGENT.md                  # architecture source of truth for the migrated repo (§12)
├── CLAUDE.md                 # quick-reference mirror of AGENT.md
├── Dockerfile
├── README.md
├── alembic.ini
├── alembic/
│   ├── env.py                # async env, imports Base + models package
│   ├── script.py.mako
│   └── versions/<rev>_<slug>.py
├── docker-compose.yml
├── pyproject.toml            # deps + ruff + pyrefly + pytest config (§10.1)
├── src/
│   ├── main.py               # app, lifespan (configure_logging + engine dispose), middleware register, routers
│   ├── config/
│   │   └── settings.py       # Settings(BaseSettings) + get_settings() lru_cache
│   ├── domain/
│   │   ├── entities/<entity>/<entity>.py            # aggregate root: invariants + behaviour
│   │   ├── repositories/<entity>/<entity>_repository.py  # Protocol port, clean name
│   │   └── enums/
│   │       ├── <entity>_enum.py                     # per-entity StrEnums
│   │       └── operation_results.py                 # CreateResult / UpdateResult / DeleteResult (+ domain results)
│   ├── ports/
│   │   ├── logger.py
│   │   ├── password_hasher.py
│   │   ├── token_service.py                         # TokenService + TokenClaims
│   │   ├── transaction_context.py                   # TransactionContext + Transaction
│   │   ├── user_context.py
│   │   └── <service>.py                             # one file per external-service port you add
│   ├── shared/
│   │   └── contract_model.py                        # ContractModel: frozen + camelCase wire base
│   ├── application/
│   │   └── use_cases/<entity>/
│   │       ├── <entity>_contracts.py                # *Request / *Response models; validation lives here
│   │       ├── <entity>_converter.py                # module functions: to_response, to_response_list, to_entity
│   │       └── <operation>_use_case.py              # one concrete class per operation, single execute()
│   ├── infrastructure/
│   │   ├── di/
│   │   │   ├── request_scope.py                     # ContextVar request scope + disposal
│   │   │   └── typed_binder.py                      # TypedBinder facade
│   │   ├── database/
│   │   │   ├── base.py                              # DeclarativeBase
│   │   │   ├── session.py                           # create_engine / create_session_factory
│   │   │   ├── errors.py                            # shared driver-error classifiers (is_deadlock)
│   │   │   ├── connection_factory.py                # ConnectionFactory seam: read() (short-lived) / write() (unit of work)
│   │   │   ├── sqlalchemy_connection_factory.py     # ConnectionFactory adapter (transient)
│   │   │   ├── sqlalchemy_transaction_context.py    # owns the write session per begin(); auto-commit on clean exit; fail-fast
│   │   │   └── models/
│   │   │       ├── __init__.py                      # re-export every model (Alembic autogenerate needs it)
│   │   │       └── <entity>_model.py
│   │   ├── repositories/<entity>/sqlalchemy_<entity>_repository.py
│   │   ├── auth/
│   │   │   ├── bcrypt_password_hasher.py
│   │   │   ├── jwt_token_service.py
│   │   │   └── request_user_context.py
│   │   └── logging/json_logger.py
│   └── api/
│       ├── result_status_maps.py                    # result enum -> HTTP status + message maps
│       ├── schemas/operation_schema.py              # generic Create/Update/DeleteOperationResponse
│       ├── middleware/
│       │   ├── request_scope_middleware.py          # RequestScopeMiddleware — pure ASGI class (outermost)
│       │   ├── request_id_middleware.py             # request_id — binds correlation id, echoes X-Request-ID
│       │   ├── access_log_middleware.py             # access_log — one request.completed entry per request
│       │   ├── exception_handler_middleware.py      # exception_handler — logs escapees, returns 500 (innermost)
│       │   └── registration.py                      # register(app): the ONLY place middleware is added
│       ├── dependencies/
│       │   ├── injected.py                          # Injected() FastAPI accessor
│       │   ├── providers.py                         # composition root: AppModule
│       │   ├── jwt_dependency.py                    # get_current_user guard
│       │   └── bindings/<domain>.py                 # register(typed_binder) per domain
│       └── routers/<entity>/
│           ├── router.py                            # /api prefix, tags, guard; include_router per operation
│           └── <operation>_route.py                 # one module per operation, own APIRouter()
└── tests/                                           # mirrors src/ exactly
    ├── domain/entities/<entity>/test_<entity>.py
    ├── application/use_cases/<entity>/{conftest.py, test_<operation>_use_case.py, test_<entity>_converter.py}
    ├── api/routers/<entity>/{conftest.py, test_<operation>_route.py}
    ├── api/middleware/test_*.py
    ├── infrastructure/{di,auth,database}/test_*.py
    └── architecture/test_layer_dependencies.py       # AST fitness test: inward-only deps + Domain/Ports purity (chassis)
```

Every package directory carries an `__init__.py`. They stay **empty** — no re-exports, no
convenience imports — with the single exception of `src/infrastructure/database/models/__init__.py`,
which re-exports each model module so `Base.metadata` is populated for Alembic autogenerate.

---

## 3. The chassis — files copied verbatim

These files are entity-agnostic. They are the template's machinery and are **copied byte-for-byte**
from the template repository into the target project. Do not adapt, rename, or "improve" them; do
not merge the source project's equivalents into them. If the source project has an equivalent
(its own `get_db`, its own logging setup, its own error handler), the chassis file **replaces** it
and the old one is deleted.

| Path | Role | Notes |
|------|------|-------|
| `src/shared/contract_model.py` | `ContractModel` wire base | frozen, camelCase out, either case in |
| `src/ports/logger.py` | `Logger` port | |
| `src/ports/password_hasher.py` | `PasswordHasher` port | drop only if the project has no auth |
| `src/ports/token_service.py` | `TokenService` + `TokenClaims` | drop only if the project has no auth |
| `src/ports/transaction_context.py` | `TransactionContext` + `Transaction` | **never** drop |
| `src/ports/user_context.py` | `UserContext` port | drop only if the project has no auth |
| `src/infrastructure/di/request_scope.py` | ContextVar request scope + LIFO disposal | **never** modify |
| `src/infrastructure/di/typed_binder.py` | `TypedBinder` static-checked binding facade | **never** modify |
| `src/infrastructure/database/base.py` | `DeclarativeBase` | |
| `src/infrastructure/database/session.py` | `create_engine` / `create_session_factory` | |
| `src/infrastructure/database/errors.py` | `is_deadlock` and future classifiers | extend here, never per-repository |
| `src/infrastructure/database/connection_factory.py` | `ConnectionFactory` seam (`read()` / `write()`) | **never** drop; repositories inject this, not `AsyncSession` |
| `src/infrastructure/database/sqlalchemy_connection_factory.py` | `ConnectionFactory` adapter | bound transient |
| `src/infrastructure/database/sqlalchemy_transaction_context.py` | write unit of work: owns its session per `begin()`, auto-commit on clean exit, fail-fast on a poisoned unit | |
| `src/infrastructure/logging/json_logger.py` | `configure_logging` + `JsonLogger` | |
| `src/infrastructure/auth/bcrypt_password_hasher.py` | `PasswordHasher` adapter | |
| `src/infrastructure/auth/jwt_token_service.py` | `TokenService` adapter | |
| `src/infrastructure/auth/request_user_context.py` | `UserContext` adapter | |
| `src/api/dependencies/injected.py` | `Injected()` accessor | |
| `src/api/dependencies/jwt_dependency.py` | `get_current_user` guard | |
| `src/api/middleware/request_scope_middleware.py` | pure ASGI scope middleware | **never** convert to dispatch (§9.4) |
| `src/api/middleware/request_id_middleware.py` | correlation id | |
| `src/api/middleware/access_log_middleware.py` | `request.completed` entry | |
| `src/api/middleware/exception_handler_middleware.py` | single failure reporter | |
| `src/api/middleware/registration.py` | ordering owner | extend only when adding a middleware |
| `src/api/schemas/operation_schema.py` | generic result envelopes | |
| `tests/architecture/test_layer_dependencies.py` | AST fitness test for the layer rules | copy verbatim; extend its rule tables only for a genuinely new layer or allowed edge |
| `src/api/result_status_maps.py` | result → status/message maps | extend for new result enums |
| `alembic/env.py`, `alembic/script.py.mako`, `alembic.ini` | async migrations | edit `sqlalchemy.url` only |
| `Dockerfile`, `docker-compose.yml`, `.dockerignore` | container setup | edit DB name/ports only |

Four chassis files are *seeded* verbatim and then **extended** as the migration proceeds:
`providers.py` (add cross-cutting binds and `@provider` methods), `registration.py` (only if a new
middleware is genuinely needed), `result_status_maps.py` (map any new result enum), and
`operation_results.py` (add domain-specific result enums like `LoginResult`).

---

## 4. Naming rules

These are not stylistic preferences — the review gates check them.

**Ports** are `typing.Protocol`s with clean, mechanism-free names: `UserRepository`,
`PasswordHasher`, `TokenService`, `Logger`, `UserContext`. Never an ABC. Never a `Base` suffix,
never an `I` prefix.

**Adapters** are mechanism-qualified and explicitly subclass their port so IDE hover resolves the
port's docstrings through the MRO: `SqlAlchemyUserRepository(UserRepository)`,
`BcryptPasswordHasher(PasswordHasher)`, `JwtTokenService(TokenService)`, `JsonLogger(Logger)`,
`RequestUserContext(UserContext)`.

**Use cases** are one plain concrete class per operation, in its own file, with a single `execute`
method: `CreateUserUseCase`, `GetUserUseCase`, `LoginUseCase`. No interface, no base class, no
`Service` suffix, no god-class holding five operations. Each declares only the ports its operation
needs. Routes and tests depend on the concrete class (`AsyncMock(spec=CreateUserUseCase)`).

**Wire models** are named for their role and live in
`src/application/use_cases/<entity>/<entity>_contracts.py`, inheriting `ContractModel` directly:

- `<Operation>Request` — **only** if the model IS the FastAPI request body (`CreateUserRequest`,
  `LoginRequest`). Validation (`EmailStr`, `min_length`, `Field(...)`) lives here.
- `<Entity>Response` — **only** if the model IS what a route returns (`UserResponse`,
  `TokenResponse`). Return `list[UserResponse]` directly, never a wrapper object.
- Non-wire types get plain names and live beside whatever produces them: `TokenClaims` sits in
  `src/ports/token_service.py`, which is why Ports never imports Application.

**Never name anything `DTO`.** Not `UserDTO`, not `dto.py`, not a `dtos/` package. **Never invent a
model just to group a use case's arguments** — pass scalars: `execute(user_id, role)`.

**Converters** are module-level functions, never classes of static methods. Names state direction:
`to_response`, `to_response_list`, `to_entity`.

**Result enums** are generic and shared: `CreateResult`, `UpdateResult`, `DeleteResult` in
`src/domain/enums/operation_results.py`. Add a domain-specific one (e.g. `LoginResult`) only when
the outcomes genuinely differ.

**Booleans read like questions** (`is_active`, `is_persisted`, `is_committed`). **No
abbreviations**: `repository` not `repo`, `request` not `req`, `configuration` not `cfg`.

---

## 5. Inventory and mapping

Before moving a single file, produce a complete inventory of the source project: every Python
module, its responsibility, and its destination. Nothing gets migrated by intuition mid-flight.

Common FastAPI layouts map as follows. The left column is what you are likely to find; the right is
where each piece lands. Most source files **split** across several destinations — that is the point
of the exercise.

| Source (typical) | Destination |
|---|---|
| `app/main.py` | `src/main.py` — app, lifespan, `middleware_registration.register(app)`, `include_router` per domain |
| `app/core/config.py`, `settings.py` | `src/config/settings.py` — `Settings(BaseSettings)` + `get_settings()` |
| `app/database.py`, `app/db/session.py` (engine, `SessionLocal`) | `src/infrastructure/database/session.py` + `@provider` methods on `AppModule` |
| `get_db()` generator + `Depends(get_db)` in every route | **Deleted.** The session is a `request`-scoped `@provider`; repositories receive it by constructor |
| `app/models/*.py` (SQLAlchemy) | **Splits**: persistence mapping → `src/infrastructure/database/models/<entity>_model.py`; business fields + rules → `src/domain/entities/<entity>/<entity>.py` |
| `app/schemas/*.py` (Pydantic) | `src/application/use_cases/<entity>/<entity>_contracts.py`; ORM-mode read models become `<Entity>Response`; `orm_mode`/`from_attributes` is **replaced** by an explicit converter function |
| `app/crud/*.py`, `app/repositories/*.py` | **Splits**: `UserRepository` Protocol → `src/domain/repositories/<entity>/`; implementation → `src/infrastructure/repositories/<entity>/sqlalchemy_<entity>_repository.py` |
| `app/services/*.py` (multi-method service classes) | One `<Operation>UseCase` class per public method, `src/application/use_cases/<entity>/<operation>_use_case.py` |
| `app/api/v1/endpoints/<entity>.py` (all routes in one module) | One module per operation: `src/api/routers/<entity>/<operation>_route.py`, aggregated by `router.py` |
| `app/api/deps.py` `get_current_user` | `src/api/dependencies/jwt_dependency.py` (chassis) |
| `app/core/security.py` (hashing, JWT) | Ports `src/ports/password_hasher.py`, `src/ports/token_service.py` + adapters in `src/infrastructure/auth/` (chassis) |
| Custom exception classes + `@app.exception_handler` | Deleted in favour of `exception_handler_middleware`, **unless** they carry an expected outcome — that becomes a result enum value (§9) |
| `logging.basicConfig`, custom logger module | `src/infrastructure/logging/json_logger.py` (chassis) |
| `@app.middleware("http")` blocks in `main.py` | `src/api/middleware/<concern>_middleware.py` + registered in `registration.py` |
| `app/utils/*.py` | Case by case: pure, dependency-free helpers used by the domain → onto the entity or a domain module; pure wire helpers → `src/shared/`; anything doing I/O → an adapter behind a new port |
| `app/tasks.py`, celery-style helpers | If they must run in-request: `BackgroundTasks` (mind §9.5 and §9.6). If they are genuinely separate units of work: a task queue, out of scope — raise it |
| `app/constants.py` string/int constants | Domain vocabulary → `StrEnum` in `src/domain/enums/`; technical constants → module-private `_CONSTANT` beside their user |
| `tests/*` | Mirror of `src/` under `tests/` (§11) |
| `requirements.txt` | `pyproject.toml` dependencies, managed with `uv` (§10.1) |
| `alembic/` | `alembic/` — keep the version history, replace `env.py` with the chassis version |

**Recording the inventory.** Write the table to `migration/INVENTORY.md` in the target repo before
Phase 1 and keep it updated: source path, destination path(s), status, notes. It is the checklist
that proves nothing was missed, and it is deleted once the migration is verified.

**Judgement calls to raise, not guess:** a "service" whose methods are really one operation each vs.
one cohesive operation; a model with no aggregate root (pure lookup table); logic that belongs to
two aggregates at once; anything touching money, permissions, or audit trails where the current
behaviour looks accidental. Ask; do not decide silently.

---

## 6. Migration procedure

Work **inward-out**: Domain first, then Ports, Application, Infrastructure, API. Each phase ends
with the four gates green. Do not begin a phase with the previous phase's gates red, and do not
migrate two entities in parallel — finish one end-to-end so the pattern is proven, then repeat.

**Phase 0 — Baseline.** Read `AGENT.md` (this template's) end to end. Capture the source project's
current behaviour: run its test suite and record the result; list every route
(`[route.path for route in app.routes]`) with its methods and status codes; note the DB schema. This
list is the acceptance criterion for §13. If the source has no tests, say so explicitly — the
migration then rests on the route inventory and the smoke test alone, which is worth flagging to
the user before starting.

**Phase 1 — Scaffold.** Create the target tree (§2) with empty `__init__.py` files. Copy the
chassis (§3) verbatim. Write `pyproject.toml`, `.pre-commit-config.yaml`, `.env.example`,
`Dockerfile`, `docker-compose.yml` (§10). Run `uv sync` and `uv run pre-commit install`. Gates green
on an empty project.

**Phase 2 — Domain.** For each aggregate: enums → entity (invariants + behaviour) → repository
port. Write the pure entity unit tests now (`tests/domain/`, no mocks). Domain imports nothing but
stdlib — if you reach for SQLAlchemy or Pydantic here, the code does not belong in Domain.

**Phase 3 — Infrastructure (persistence).** ORM model per entity + re-export in
`models/__init__.py`; repository adapter subclassing the port. Then Alembic: keep the source
project's existing version history if the schema is unchanged; if constraint names had to change to
satisfy the naming rule (§10.5), generate a migration that renames them — never edit a migration
that has already run in an environment you do not control.

**Phase 4 — Application.** Contracts, converters, one use case per operation (single-write use cases
have no transaction context; multi-write use cases inject `TransactionContext`). Use case tests with
`AsyncMock(spec=<Port>)` (and a `FakeTransactionContext` only for a multi-write use case).

**Phase 5 — API.** Route module per operation, `router.py` per entity, `bindings/<entity>.py`,
register in `AppModule.configure()`, include in `main.py`. Route tests.

**Phase 6 — Cross-cutting.** Any external service the source project used (email, S3, cache, HTTP
client) becomes a port + adapter (§8).

**Phase 7 — Delete.** Remove the source tree (`app/`, `api/`, old `tests/`, `requirements.txt`,
stray `test_*.py` at root). Grep for orphans: `get_db`, `SessionLocal`, `DTO`, `Depends(get_db)`,
`orm_mode`, `from_attributes`, `basicConfig`, the old package name. Zero hits.

**Phase 8 — Docs.** Write `AGENT.md` for the migrated repo (§12) and its quick-reference mirrors.

**Phase 9 — Verify.** §13, all of it, including the live smoke test.

---

## 7. Layer recipes

Each recipe below is the shape to write. `<Entity>`/`<entity>` are placeholders. Read the
template's `user` and `auth` implementations alongside these — they are the worked example.

### 7.1 Enums — `src/domain/enums/<entity>_enum.py`

`StrEnum` (3.11+), lowercase values matching what the DB stores. All enums live in
`src/domain/enums/`, never beside a model or a route.

```python
from enum import StrEnum


class OrderStatus(StrEnum):
    """Lifecycle status of an order."""

    DRAFT = "draft"
    PLACED = "placed"
    CANCELLED = "cancelled"
```

### 7.2 Entity — `src/domain/entities/<entity>/<entity>.py`

The aggregate root. Invariants enforced in `__post_init__` (raise `ValueError`); state transitions
via intention-revealing methods; predicates as properties. **Never anemic** — if a rule concerns one
aggregate, it lives here, not in a use case.

```python
from dataclasses import dataclass, field
from datetime import datetime

from src.domain.enums import order_enum


@dataclass
class Order:
    """Aggregate root representing a customer order."""

    id: int | None
    customer_id: int
    total_amount: int
    status: order_enum.OrderStatus = field(default=order_enum.OrderStatus.DRAFT)
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """Validate the order amount.

        Raises:
            ValueError: If the total amount is negative.
        """
        if self.total_amount < 0:
            raise ValueError("Order invariant violated: total_amount must not be negative")

    @property
    def is_persisted(self) -> bool:
        """Whether this entity has been stored (id assigned by the database)."""
        return self.id is not None

    @property
    def is_cancellable(self) -> bool:
        """Whether this order may still be cancelled."""
        return self.status is order_enum.OrderStatus.PLACED

    def cancel(self) -> None:
        """Transition the order to ``CANCELLED``.

        Raises:
            ValueError: If the order is not in a cancellable state.
        """
        if not self.is_cancellable:
            raise ValueError(f"Order invariant violated: cannot cancel an order in state {self.status}")
        self.status = order_enum.OrderStatus.CANCELLED
```

**Migrating from a SQLAlchemy model:** the entity is *not* the model. Copy the business fields;
leave `Mapped[...]`, `mapped_column`, `relationship`, and `__tablename__` behind in the ORM model.
`id` and `created_at` are `| None` because the DB assigns them.

### 7.3 Repository port — `src/domain/repositories/<entity>/<entity>_repository.py`

One port per aggregate root, defined in Domain. This is where the contract is documented **once**:
concise docstrings — one-line summary plus `Args`/`Returns`/`Raises`. No implementation details, no
rationale, no usage examples. One CRUD operation per method.

```python
from typing import Protocol

from src.domain.entities.order.order import Order
from src.domain.enums import operation_results


class OrderRepository(Protocol):
    """Persistence port for the ``Order`` aggregate."""

    async def create(self, order: Order) -> tuple[operation_results.CreateResult, int | None]:
        """Persist a new order aggregate.

        Args:
            order: The unpersisted order entity (``id`` must be None).

        Returns:
            A tuple of (result, id): the newly created order id on success,
            None on any failure result.
        """
        ...

    async def get_by_id(self, order_id: int) -> Order | None:
        """Load an order by its unique identifier.

        Args:
            order_id: The unique identifier of the order to load.

        Returns:
            The Order entity if found, None otherwise.
        """
        ...
```

A targeted single-column update (`update_role`) is acceptable **only** when no domain rule guards
the change. Anything guarded by an invariant goes load → entity behaviour → persist.

### 7.4 ORM model — `src/infrastructure/database/models/<entity>_model.py`

All constraints carry an explicit `name` with the right prefix (`uq_`, `fk_`, `ck_`, `ix_`).
`id` and `created_at` are DB-generated — never set them in Python.

```python
from datetime import datetime

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums import order_enum
from src.infrastructure.database import base as database_base

order_status_enum = SQLAlchemyEnum(order_enum.OrderStatus, name="order_status")


class OrderModel(database_base.Base):
    """ORM model for the orders table."""

    __tablename__ = "orders"
    __table_args__ = (UniqueConstraint("reference", name="uq_orders_reference"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id", name="fk_orders_customer_id"), nullable=False)
    total_amount: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[order_enum.OrderStatus] = mapped_column(order_status_enum, nullable=False, default=order_enum.OrderStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
```

Then re-export it so Alembic sees it:

```python
# src/infrastructure/database/models/__init__.py
from src.infrastructure.database.models import order_model, user_model

__all__ = ["order_model", "user_model"]
```

### 7.5 Repository adapter — `src/infrastructure/repositories/<entity>/sqlalchemy_<entity>_repository.py`

Injects the `ConnectionFactory` by constructor (never an `AsyncSession`, never ambient state).
**Never commits or rolls back** — the transaction context owns the boundary. Wrap **reads** in
`async with self._connections.read() as session:` (a fresh short-lived session) and **writes** in
`async with self._connections.write() as session:` (the request write unit of work). Mutations
`flush()`/`execute()` and map driver exceptions to result enums; reads just query. `flush()`
populates `id` and server defaults via RETURNING, so `session.refresh()` is never needed. Put the
`try`/`except` **outside** the `write()` block, so the context rolls the unit back and marks it dead
*before* the repository translates the error to a result enum. The `_to_entity` mapping is a
module-level function, not a method. Docstrings are **not** repeated — they are inherited from the port.

```python
from typing import Any, cast

from injector import inject
from sqlalchemy import CursorResult, delete, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError

from src.domain.entities.order.order import Order
from src.domain.enums import operation_results
from src.domain.repositories.order.order_repository import OrderRepository
from src.infrastructure.database.connection_factory import ConnectionFactory
from src.infrastructure.database.errors import is_deadlock
from src.infrastructure.database.models import order_model


def _to_entity(model: order_model.OrderModel) -> Order:
    return Order(
        id=model.id,
        customer_id=model.customer_id,
        total_amount=model.total_amount,
        status=model.status,
        created_at=model.created_at,
    )


class SqlAlchemyOrderRepository(OrderRepository):
    """``OrderRepository`` adapter backed by SQLAlchemy and PostgreSQL."""

    @inject
    def __init__(self, connections: ConnectionFactory) -> None:
        self._connections = connections

    async def create(self, order: Order) -> tuple[operation_results.CreateResult, int | None]:
        model = order_model.OrderModel(customer_id=order.customer_id, total_amount=order.total_amount, status=order.status)
        try:
            async with self._connections.write() as session:
                session.add(model)
                await session.flush()  # INSERT + RETURNING populates id/server defaults; does not end the tx
                return (operation_results.CreateResult.SUCCESS, model.id)
        except IntegrityError:
            return (operation_results.CreateResult.UNIQUE_CONSTRAINT_ERROR, None)
        except DBAPIError as exc:
            return (operation_results.CreateResult.CONCURRENCY_ERROR if is_deadlock(exc) else operation_results.CreateResult.FAILURE, None)
        except Exception:
            return (operation_results.CreateResult.FAILURE, None)

    async def get_by_id(self, order_id: int) -> Order | None:
        async with self._connections.read() as session:
            query_result = await session.execute(select(order_model.OrderModel).where(order_model.OrderModel.id == order_id))
            model = query_result.scalar_one_or_none()
            return _to_entity(model) if model is not None else None
```

The exception mapping is fixed: `IntegrityError` → `UNIQUE_CONSTRAINT_ERROR`; `DBAPIError` +
`is_deadlock(exc)` → `CONCURRENCY_ERROR`; anything else → `FAILURE`. **Never re-implement the
`isinstance(exc.__cause__, ...)` check in an adapter** — add the next classifier to
`src/infrastructure/database/errors.py` and import it. A **single** repository write self-commits (its
`write()` scope is the outermost `begin()`); the use case only opens `transaction_context.begin()` to
make **several** writes atomic (§7.8).

For `UPDATE`/`DELETE`, `rowcount` needs the documented cast (SQLAlchemy's static return type is
`Result`, which lacks it; the runtime type is `CursorResult`) — copy that pattern from
`SqlAlchemyUserRepository` exactly rather than reaching for a suppression.

### 7.6 Contracts — `src/application/use_cases/<entity>/<entity>_contracts.py`

Inherit `ContractModel` directly (it carries frozen + camelCase-on-the-wire + either-case-in). There
is no intermediate marker base. Validation lives here — it is the boundary guard; entity invariants
are the last line of defence, not the first.

```python
from datetime import datetime

from pydantic import Field

from src.domain.enums import order_enum
from src.shared.contract_model import ContractModel


class CreateOrderRequest(ContractModel):
    """Request body for creating an order."""

    customer_id: int = Field(gt=0, description="Id of the customer placing the order")
    total_amount: int = Field(ge=0, description="Order total in minor currency units")


class OrderResponse(ContractModel):
    """Response body representing a persisted order."""

    id: int
    customer_id: int
    total_amount: int
    status: order_enum.OrderStatus
    created_at: datetime
```

### 7.7 Converter — `src/application/use_cases/<entity>/<entity>_converter.py`

Module functions. Not a class. Not static methods. These functions carry their own docstrings —
they have no port, so they are the single source.

```python
from src.application.use_cases.order import order_contracts
from src.domain.entities.order.order import Order


def to_response(order: Order) -> order_contracts.OrderResponse:
    """Convert a persisted domain order entity to a response model.

    Args:
        order: The domain entity to convert; must be persisted (id and
            created_at populated).

    Returns:
        An OrderResponse populated with the entity's data.

    Raises:
        ValueError: If the entity has not been persisted.
    """
    if order.id is None or order.created_at is None:
        raise ValueError("Cannot convert an unpersisted Order to an OrderResponse")

    return order_contracts.OrderResponse(
        id=order.id, customer_id=order.customer_id, total_amount=order.total_amount, status=order.status, created_at=order.created_at
    )


def to_response_list(orders: list[Order]) -> list[order_contracts.OrderResponse]:
    """Convert a list of persisted domain order entities to response models.

    Args:
        orders: The domain entities to convert.

    Returns:
        A list of OrderResponses, in the same order.
    """
    return [to_response(order) for order in orders]


def to_entity(create_order_request: order_contracts.CreateOrderRequest) -> Order:
    """Build an unpersisted domain order entity from a creation request.

    Args:
        create_order_request: The request data for the new order.

    Returns:
        A new Order entity with id set to None.
    """
    return Order(id=None, customer_id=create_order_request.customer_id, total_amount=create_order_request.total_amount)
```

### 7.8 Use cases — `src/application/use_cases/<entity>/<operation>_use_case.py`

One class, one file, one `execute`. `@inject` on `__init__`. Declare only the ports this operation
needs. Use cases carry their own method docstrings — they have no port, so they ARE the single
source. They **orchestrate**; they never implement a domain rule that belongs on the entity.

**Single-write operation** — no transaction context at all; the repository's `write()` scope is the
outermost `begin()`, so it self-commits on success and rolls back on a DB error:

```python
from injector import inject

from src.application.use_cases.order import order_contracts, order_converter
from src.domain.enums import operation_results
from src.domain.repositories.order.order_repository import OrderRepository


class CreateOrderUseCase:
    """Creates a new order."""

    @inject
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def execute(self, create_order_request: order_contracts.CreateOrderRequest) -> tuple[operation_results.CreateResult, int | None]:
        """Create a new order.

        Args:
            create_order_request: The validated data for the new order.

        Returns:
            A tuple of (result, id): the new order id on success, None on any
            failure result.
        """
        order = order_converter.to_entity(create_order_request)
        return await self._repository.create(order)
```

**Read operation** — no transaction context, no `begin()` block:

```python
class GetOrderUseCase:
    """Retrieves a single order."""

    @inject
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    async def execute(self, order_id: int) -> order_contracts.OrderResponse | None:
        """Return the order with the given id.

        Args:
            order_id: The unique identifier of the order.

        Returns:
            The OrderResponse if found, None otherwise.
        """
        order = await self._repository.get_by_id(order_id)

        if order is None:
            return None

        return order_converter.to_response(order)
```

**Load → behave → persist** (a change guarded by a domain rule) — the rule stays on the entity.
**Read first, outside the write unit; only writes go inside `begin()`.** A repository read runs on
its own short-lived session (§7.5), so it never joins the write transaction — do the loading (and any
decision it drives) before opening `begin()`, and never call a repository read inside a `begin()`
block (it would check out a second pooled connection while the write connection is held). Here the
persist is a single write, so it self-commits and needs no `begin()` at all:

```python
    async def execute(self, order_id: int) -> operation_results.UpdateResult:
        """Cancel the order with the given id.

        Args:
            order_id: The unique identifier of the order to cancel.

        Returns:
            An UpdateResult describing the outcome.
        """
        order = await self._repository.get_by_id(order_id)  # read first — outside any write unit
        if order is None:
            return operation_results.UpdateResult.NOT_FOUND

        order.cancel()  # the rule lives on the entity

        return await self._repository.update(order)  # a single write self-commits
```

**Atomic multi-repository operations:** do every **read** first, then call the several repository
**writes** inside ONE `begin()` block — never a read inside it. The writes share the unit's session
and so commit together on a clean exit or roll back together on the first failure (a DB error rolls
the unit back automatically; call `await transaction.rollback()` for a benign non-success result).
Because an early `return` inside `begin()` now **commits**, roll back explicitly before returning on a
benign non-success result. Never open two blocks to fake atomicity. **Do not pass sessions to use
cases**, ever.

**Method composition — one level of abstraction per method.** An `execute` reads as a sequence of
named steps. Each nameable sub-goal inside it (building a value, classifying an error, checking a
precondition) is extracted into a helper named for that sub-goal: a module-level `_` function when
the logic is pure, a `_`-prefixed method when it needs `self`. The trigger is a nameable sub-goal,
not a line count — if you could write a comment above a block saying what it accomplishes, that
comment is the helper's name. Helpers take no docstrings. Do not extract a single expression its
variable already names.

### 7.9 Routes — `src/api/routers/<entity>/<operation>_route.py`

One module per operation, its own `APIRouter()`, **resource-relative path** (`""` for the collection
root, `/{id}` for item routes). The entity and version never appear in an operation file. Routes
accept and return the **contracts directly** — there are no per-entity API schemas and no API-layer
converters. Route docstrings become the OpenAPI description.

**Result-dependent status** — inject `response: Response`, set the status from the map, return the
model:

```python
from typing import Annotated

from fastapi import APIRouter, Response, status

from src.api import result_status_maps
from src.api.dependencies.injected import Injected
from src.api.schemas import operation_schema
from src.application.use_cases.order import order_contracts
from src.application.use_cases.order.create_order_use_case import CreateOrderUseCase

router = APIRouter()

UseCaseDep = Annotated[CreateOrderUseCase, Injected(CreateOrderUseCase)]


@router.post(
    "",
    response_model=operation_schema.CreateOperationResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {"description": "Order created successfully"},
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_409_CONFLICT: {"description": "Unique constraint violation or concurrency conflict"},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Unexpected failure"},
    },
)
async def create_order(
    create_order_request: order_contracts.CreateOrderRequest, response: Response, use_case: UseCaseDep
) -> operation_schema.CreateOperationResponse:
    """Create a new order."""
    result, entity_id = await use_case.execute(create_order_request)
    response.status_code = result_status_maps.CREATE_STATUS_MAP[result]
    return operation_schema.CreateOperationResponse(result=result, message=result_status_maps.CREATE_MESSAGE_MAP[result], id=entity_id)
```

**Expected not-found / auth failure** — `HTTPException`, raised by the route itself:

```python
@router.get(
    "/{order_id}",
    response_model=order_contracts.OrderResponse,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Missing or invalid JWT token"},
        status.HTTP_404_NOT_FOUND: {"description": "Order not found"},
    },
)
async def get_order(order_id: int, use_case: UseCaseDep) -> order_contracts.OrderResponse:
    """Get an order by its unique identifier.

    Raises:
        HTTPException: 404 if the order is not found.
    """
    found_order = await use_case.execute(order_id)

    if found_order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id {order_id} not found")

    return found_order
```

**Never** `return JSONResponse(model.model_dump())` — return the model and let FastAPI serialise it
(camelCase comes from `ContractModel`). **Never** call a repository from a route.

### 7.10 Router aggregation — `src/api/routers/<entity>/router.py`

URL shape is `/api/<entity>/<version>/<path>`. `/api` is the base on the domain router's `prefix`;
the `/<entity>/v1` segment rides on each `include_router` call, so **the version is per-endpoint** —
one endpoint can move to `/orders/v2` without touching the others. Do **not** collapse the segment
onto the router's own `prefix`: FastAPI rejects including a prefix-less router that has an empty
collection-root path.

```python
from fastapi import APIRouter, Depends

from src.api.dependencies.jwt_dependency import get_current_user
from src.api.routers.order import cancel_order_route, create_order_route, get_all_orders_route, get_order_route

router = APIRouter(prefix="/api", tags=["orders"], dependencies=[Depends(get_current_user)])
router.include_router(create_order_route.router, prefix="/orders/v1")
router.include_router(get_order_route.router, prefix="/orders/v1")
router.include_router(get_all_orders_route.router, prefix="/orders/v1")
router.include_router(cancel_order_route.router, prefix="/orders/v1")
```

**URL changes are the one behaviour change migration forces.** Record the old → new mapping in the
inventory and surface it to the user — clients will need it.

### 7.11 Bindings — `src/api/dependencies/bindings/<entity>.py`

Per-domain `register(typed_binder)`. Binding modules live in the **API layer** (they import
adapters) — never in `src/application/`. Bind through `TypedBinder`, never plain tuples, which drop
the static check.

```python
from src.application.use_cases.order.cancel_order_use_case import CancelOrderUseCase
from src.application.use_cases.order.create_order_use_case import CreateOrderUseCase
from src.application.use_cases.order.get_all_orders_use_case import GetAllOrdersUseCase
from src.application.use_cases.order.get_order_use_case import GetOrderUseCase
from src.domain.repositories.order.order_repository import OrderRepository
from src.infrastructure.di.typed_binder import TypedBinder
from src.infrastructure.repositories.order.sqlalchemy_order_repository import SqlAlchemyOrderRepository


def register(typed_binder: TypedBinder) -> None:
    """Bind the order domain's repository and use cases (all transient)."""
    typed_binder.bind_typed(OrderRepository).to(SqlAlchemyOrderRepository)
    typed_binder.bind_self_typed(CreateOrderUseCase)
    typed_binder.bind_self_typed(GetOrderUseCase)
    typed_binder.bind_self_typed(GetAllOrdersUseCase)
    typed_binder.bind_self_typed(CancelOrderUseCase)
```

Then one line in `AppModule.configure()`: `order_bindings.register(typed_binder)`.

**Scopes are chosen by what holds request state:**

- `singleton` — engine, session factory, settings, stateless services (`BcryptPasswordHasher`,
  `JwtTokenService`).
- `request` — the write unit of work `SqlAlchemyTransactionContext`, logger, user context. The
  transaction context is bound to **both** itself and the `TransactionContext` port via two
  `@request @provider` methods that return the same instance, so a use case's `begin()` and a
  repository's `write()` nest on one write session. There is **no** request-scoped `AsyncSession`.
- **transient** (no scope) — stateless orchestrators: use cases, repositories, and the
  `ConnectionFactory` adapter (`SqlAlchemyConnectionFactory`). Repositories get their session through
  the injected `ConnectionFactory` (`read()` for a fresh short-lived session, `write()` for the
  request write unit of work).

`@inject` is **required** on every implementation whose `__init__` takes dependencies. Omitting it
is a runtime `TypeError`, not a type error — it will not be caught by pyrefly.

### 7.12 `src/main.py`

```python
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from injector import Injector
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.dependencies.providers import AppModule
from src.api.middleware import registration as middleware_registration
from src.api.routers.auth.router import router as auth_router
from src.api.routers.order.router import router as order_router
from src.config.settings import Settings
from src.infrastructure.logging.json_logger import configure_logging

injector = Injector([AppModule()])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Manage the application startup and shutdown lifecycle."""
    configure_logging(app.state.injector.get(Settings))
    yield
    engine = app.state.injector.get(AsyncEngine)
    await engine.dispose()


app = FastAPI(title="...", description="...", version="1.0.0", lifespan=lifespan)
app.state.injector = injector
middleware_registration.register(app)

app.include_router(auth_router)
app.include_router(order_router)
```

---

## 8. External services

Anything the application calls that is not the database — email, object storage, cache, payment
gateway, third-party HTTP API — becomes a **port** in `src/ports/<service>.py` (a `Protocol` with
the concise contract docstrings) and a **mechanism-qualified adapter** in
`src/infrastructure/<area>/<mechanism>_<service>.py` that explicitly subclasses the port. Bind it in
`AppModule.configure()` with the scope its state demands (stateless client → `singleton`).

Use cases depend on the port, never the SDK. If a source use case imports `boto3`, `httpx`,
`smtplib`, or a vendor client directly, that import is the defect the port removes.

---

## 9. Error handling

This is the rule most likely to be violated by a migrated codebase, because the typical FastAPI
project wraps everything in `try`/`except`. Most of those blocks get **deleted**.

### 9.1 One reporter

Failures are reported in ONE place: `exception_handler_middleware`, registered first so it is
innermost. It catches anything escaping a route, logs `request.unhandled_exception` through the
request-scoped `Logger` (traceback, `method`, `path`, `request_id`, `user_id`), and returns
`500 {"detail": "Internal Server Error"}`. The body stays opaque — detail belongs in the correlated
log.

### 9.2 When `try`/`except` is legitimate

Only when the `except`/`finally` block does **real work the middleware cannot** — work specific to
that call site that either **translates** the failure into the layer's vocabulary or **undoes**
something:

- Repositories mapping `IntegrityError`/`DBAPIError` to result enums (translate).
- `SqlAlchemyTransactionContext.begin` rolling back, then re-raising (undo).
- `JwtTokenService.decode_token` returning `None` on `InvalidTokenError` (translate).
- The request-scope teardown logging a failed `aclose()` so the remaining disposals still run.
- A `BackgroundTasks` callable (§9.5).

### 9.3 When it is not

**Never catch merely to report.** A block that only logs and re-raises, wraps the exception, or
hand-builds a 500 duplicates the middleware — delete it and let the exception propagate. Same for
`except: raise` and a `finally` that adds nothing.

**Never catch to produce an `HTTPException`.** Routes raise `HTTPException` for outcomes they
*expect* and detect themselves (not-found, auth failure) — never as a translation of a caught
unexpected exception.

**Never catch `Exception` to continue with a default** unless that default is a real result (a
result enum, `None` from a decode). Swallowing an error behind a plausible success hides it from
both the log and the caller.

**No `try` is needed for rollback in a use case:** leaving a `begin()` block by exception already
rolls back, and the exception continues to the middleware.

**Migration heuristic:** for each `try`/`except` in the source, ask *what does the except block do
besides report?* If the answer is "nothing", delete it. If it maps a driver error to an outcome,
it becomes a result-enum mapping in a repository adapter. If it produces an HTTP error for an
expected outcome, that outcome becomes a result enum value or an `HTTPException` the route raises
directly.

### 9.4 Middleware

One concern per module in `src/api/middleware/<concern>_middleware.py`. `register(app)` in
`registration.py` is the **only** place middleware is added and owns the ordering. Starlette runs
the most recently registered first, so the outermost is registered **last**.

Order (innermost → outermost): `exception_handler`, `access_log`, `request_id`,
`RequestScopeMiddleware`. Any middleware resolving a request-scoped binding must be registered
**before** `RequestScopeMiddleware`.

Default shape is a `BaseHTTPMiddleware` dispatch function. `RequestScopeMiddleware` is deliberately
a **pure ASGI class** and must never be converted: `call_next` returns when the response *starts*,
so the scope would dispose its request-scoped collaborators (the write unit of work, the `Logger`,
the `UserContext`) while `BackgroundTasks` and streaming bodies are still running — silently, because
anyio's context copy still resolves the same, already-disposed instances. Regression tests:
`tests/api/middleware/test_request_scope_middleware.py`.

### 9.5 Background tasks

A `BackgroundTasks` callable is the one place that **must** catch for itself. It runs after the
response is sent, so its exception escapes `exception_handler` entirely, reaching uvicorn as a bare
`Exception in ASGI application` with no `request_id`/`user_id`. Wrap the task body and log through
the injected `Logger` — it is the only reporter that task gets.

Background tasks and streaming bodies run **inside** the request scope. Their own DB work is a new
unit of work needing its own `write()` / `begin()` block. Genuinely separate units of work belong in
a task queue.

### 9.6 The read-route background-task trap (largely dissolved)

Before the `ConnectionFactory`, a background task on a **read** route pinned a pool connection for
its whole duration: a shared request session's `SELECT` autobegan a transaction that ended only when
the session closed at request end — after the background work.

`ConnectionFactory.read()` dissolves this. It hands the read a **fresh short-lived session** and
closes it on block exit, so the `SELECT`'s autobegun transaction ends and the pooled connection is
returned **immediately** — long before any background task runs. Reads therefore need no `begin()`
wrapper. A **write** still commits (freeing its connection) before a background task starts, so the
task inherits a clean session and opens its own unit of work.

---

## 10. Configuration files

### 10.1 `pyproject.toml`

Dependencies are managed with `uv`. **Always `uv run`** — never invoke `.venv` binaries directly.
Convert `requirements.txt` by mapping each pin into `[project].dependencies`, dropping anything the
template's stack replaces (`python-jose` → `PyJWT`, custom loggers, `databases`, sync `psycopg2`).

The ruff, pyrefly, and pytest sections are reproduced **exactly** — same rules, same line length,
same preset:

```toml
[project]
name = "<project-name>"
version = "1.0.0"
description = "<description>"
readme = "README.md"
requires-python = ">=3.13"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy[asyncio]>=2.0.36",
    "asyncpg>=0.30.0",
    "pydantic>=2.10.0",
    "email-validator>=2.0.0",
    "pydantic-settings>=2.6.0",
    "python-dotenv>=1.0.1",
    "injector>=0.22.0",
    "PyJWT>=2.10.0",
    "passlib[bcrypt]>=1.7.4",
    "bcrypt>=3.2.0,<4.0",
    "alembic>=1.13.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]

[dependency-groups]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "pyrefly>=1.1.0",
    "aiosqlite>=0.20.0",
    "types-passlib>=1.7.7",
    "pre-commit>=4.0.0",
]

[tool.ruff]
line-length = 140
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = []

[tool.ruff.lint.isort]
split-on-trailing-comma = false

[tool.ruff.format]
skip-magic-trailing-comma = true

[tool.pyrefly]
python-version = "3.13"
project-includes = ["src/**", "tests/**"]
# "legacy" is pyrefly's own recommended preset for codebases migrating from
# mypy: it matches mypy's practical strictness without adopting pyrefly-only
# checks (e.g. mandatory @override) that would be a separate, bigger change.
preset = "legacy"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

Do not lower `line-length`, do not remove a rule from `select`, do not change `preset`, and do not
add per-file ignores. `skip-magic-trailing-comma = true` means the formatter uses the full 140
columns — let it; do not hand-wrap. `asyncio_mode = "auto"` means **no `@pytest.mark.asyncio`
decorators** anywhere.

Keep `[project.optional-dependencies].dev` in sync with `[dependency-groups].dev` if the source
project relied on `pip install -e ".[dev]"`.

### 10.2 `.pre-commit-config.yaml`

The template ships this file. It runs the **lint / format / type-check** gates through `uv run`, so
hook results and terminal results cannot diverge. It deliberately does **not** run the test suite:
unit tests belong in CI (or `uv run pytest` run manually), so commits stay fast. Copy it verbatim:

```yaml
repos:
  - repo: local
    hooks:
      - id: ruff-check
        name: ruff check --fix
        entry: uv run ruff check src tests --fix
        language: system
        pass_filenames: false
        always_run: true

      - id: ruff-format
        name: ruff format
        entry: uv run ruff format src tests
        language: system
        pass_filenames: false
        always_run: true

      - id: pyrefly
        name: pyrefly check
        entry: uv run pyrefly check
        language: system
        pass_filenames: false
        always_run: true
```

`local` + `language: system` hooks are deliberate: they use the versions resolved in `uv.lock`, so a
hook cannot drift from what `uv run ruff check` does at the terminal. All three take
`pass_filenames: false` + `always_run: true` and target `src tests` (pyrefly reads `project-includes`
from `pyproject.toml`), so each runs the whole-project gate exactly — never touching files outside the
project. `pre-commit` assumes the config sits at the **git root**; if this project lives inside a
larger monorepo, run the hooks from a standalone checkout or move the config to the actual git root.

Install after `uv sync`:

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

If the source project already has a `.pre-commit-config.yaml`, it is **replaced**, not merged.
Hooks for tools the template does not use (black, isort, flake8, mypy, autoflake) are removed —
ruff and pyrefly subsume them, and running both would produce fighting formatters.

### 10.3 `.env.example` and settings

Every setting appears in `.env.example` with a safe default and no real secret. `.env` is local and
gitignored.

```bash
# Database Configuration
DB_DRIVER=postgresql+asyncpg
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME=<project>_db
IS_SQL_ECHO_ENABLED=false
POOL_SIZE=5
MAX_OVERFLOW=10

# JWT Configuration
JWT_SECRET_KEY=changeme-use-a-strong-random-secret-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Logging
LOG_LEVEL=INFO
```

`Settings.database_url` returns a **`URL` object, not `str(URL)`** — `str()` masks the password as
`***` and DB auth then fails. Copy `src/config/settings.py` from the template and add the source
project's own settings as fields; keep `get_settings()`'s `@lru_cache`.

### 10.4 Docker

`Dockerfile`, `docker-compose.yml`, and `.dockerignore` are copied from the template; only the DB
name and ports change. Note the PostgreSQL 18 volume mount is `/var/lib/postgresql`, **not**
`/var/lib/postgresql/data` — the deeper path silently fails to persist on PG 18 images.

### 10.5 Alembic

`alembic/env.py` is the chassis async version: it imports `Base` and the models package
(`import src.infrastructure.database.models  # noqa: F401`) so autogenerate sees every table. Set
`sqlalchemy.url` in `alembic.ini` (sync-safe URL) and keep `prepend_sys_path = .`.

Preserve the source project's migration history — it describes databases that already exist. Add new
revisions for changes migration forces (renamed constraints, enum types). Never rewrite a revision
that has already been applied outside your control. If the source project used `create_all()` and
has no migrations, generate an initial revision from the models and say so explicitly.

---

## 11. Tests

`tests/` mirrors `src/` exactly. `asyncio_mode = "auto"` is configured — no `@pytest.mark.asyncio`.

**Domain** (`tests/domain/entities/<entity>/test_<entity>.py`) — pure unit tests. No mocks, no I/O.
Cover every invariant (`pytest.raises(ValueError)`) and every state transition.

**Use cases** (`tests/application/use_cases/<entity>/`) — `AsyncMock(spec=<Port>)` for each port. A
**single-write** use case has no transaction context: assert the repository result is forwarded. A
**multi-write** use case uses a `FakeTransactionContext` from the local `conftest.py`
(commit-on-clean-exit; rollback on exception or `rollback()`) — assert it is **not rolled back on
success** and **rolled back on failure** (there is no `commit()` to assert). Mock the port, never the
adapter. Unit-of-work behaviour (auto-commit, rollback, poisoned-unit fail-fast) is integration-tested
in `tests/infrastructure/database/` over a real `SqlAlchemyConnectionFactory` on aiosqlite.

**Routes** (`tests/api/routers/<entity>/`) — a minimal `FastAPI()` in the `conftest.py`, the router
under test included, `app.state.injector = Injector([TestModule()])` binding mock **instances**
(`binder.bind(GetOrderUseCase, to=mock)`), and `app.dependency_overrides` for `get_current_user`.
**Never import `src/main.py`** in a route test — it would build the real injector and reach for a
database.

Because the mocks are instance-bound, no request scope is needed in route tests.

**Migrating existing tests:** a test that exercised a route through the DB becomes a route test with
a mocked use case *plus* a use case test with a mocked repository — one test usually splits in two.
A test asserting a business rule becomes a domain test. Tests calling `TestClient(app)` with a real
session are the ones to rewrite first. Delete root-level `test_*.py` scratch scripts; behaviour
worth keeping moves into `tests/`.

DI machinery tests live in `tests/infrastructure/di/` and come with the chassis — keep them; they
are the regression net for the request scope.

**Architecture fitness test** (`tests/architecture/test_layer_dependencies.py`, chassis) — copied
verbatim, it walks `src/` and parses each module's imports (AST), failing on any breach of the
inward-only dependency direction (Domain imports nothing; Ports only Domain/`shared`; Application only
Domain/Ports/`shared`; Infrastructure inward of API) or of Domain/Ports framework-purity (no
third-party imports; Application never imports `sqlalchemy`/`fastapi`). It names the offending file,
so the layering cannot silently rot as the project grows. Extend its rule tables only when you add a
genuinely new layer or a legitimately new allowed edge.

---

## 12. `AGENT.md` for the migrated repo

The migrated project gets its **own** `AGENT.md` — the single source of truth for its architecture,
the file every future agent and developer reads before touching code. Base it on this template's
`AGENT.md` (all twelve sections) and make it *about the migrated project*: its entities, its
routers, its ports, its URL map.

Sections, in order:

1. **Architecture** — the layer table, the dependency rule, the composition root, the file-organisation tree (§2, populated with the real entity names).
2. **Domain-Driven Design** — aggregate roots, one repository port per aggregate, ubiquitous language, where validation lives.
3. **Naming Conventions** — classes (ports, adapters, use cases, contracts), variables and properties (§4).
4. **Core Patterns** — ports & adapters; DI (injector + TypedBinder, the three scopes, `@inject`); session/transactions/unit of work; converters; auth & current user; routes & responses; middleware & ordering; error handling.
5. **Enums** and API response conventions.
6. **Database** — DB-generated values, constraint naming, shared driver-error classification, async everywhere.
7. **External Services** — the port + adapter rule (§8).
8. **Adding a New Entity** — the numbered end-to-end recipe (domain → infrastructure → application → API → tests).
9. **Testing** — the four test kinds and their shapes.
10. **Documentation & Code Style** — no module docstrings; port-documented-once + MRO hover; 140 columns; `uv run` gates; the no-suppression rule; one level of abstraction per method.
11. **Anti-Patterns** — the "never" list (§14), each with the reason.
12. **Keeping Quick-Reference Files in Sync** — list the mirrors and state that `AGENT.md` is authoritative.

Then write the quick-reference mirrors the target repo's tooling needs. At minimum `CLAUDE.md`; add
`AGENTS.md`, `.clinerules`, `.cursorrules`, `.windsurfrules`, `.antigravity/rules.md`,
`.github/copilot-instructions.md` if those tools are in use. Each mirrors `AGENT.md`'s critical
rules and opens by pointing at `AGENT.md` as the source of truth. Section 12 exists precisely
because these drift — they are updated together, in the same commit, always.

`README.md` is human-facing and separate: what the project is, setup (`uv sync`,
`uv run pre-commit install`, `docker compose up -d`, `uv run alembic upgrade head`,
`uv run uvicorn src.main:app --reload`), the URL map, and the gate commands.

---

## 13. Verification

Run in order. All must pass before the migration is called done.

**1. Gates.**

```bash
uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/
uv run pyrefly check
uv run pytest
uv run pre-commit run --all-files
```

**2. No suppressions were added.** `git diff` shows no new `# noqa`, `# type: ignore`, or pyrefly
ignore comments (the one in `alembic/env.py` is pre-existing and expected).

**3. Layer boundaries hold.** Each of these greps returns nothing:

```bash
grep -rE "^from (src\.(application|infrastructure|api|ports))|^import src\.(application|infrastructure|api|ports)" src/domain/   # Domain imports nothing
grep -rE "^from src\.application" src/ports/                                                                                     # Ports never import Application
grep -rE "sqlalchemy|pydantic|fastapi" src/domain/                                                                               # Domain is framework-free
grep -rE "AsyncSession" src/application/                                                                                         # no sessions in use cases
grep -rn "AsyncSession" src/infrastructure/repositories/                                                                          # repositories inject ConnectionFactory, not a session
grep -rn "\.commit()" src/application/                                                                                            # no use case commits (auto-commit on clean exit)
grep -rn "DTO" src/ tests/                                                                                                       # no DTO naming
grep -rn "get_db\|SessionLocal\|orm_mode\|from_attributes\|basicConfig" src/                                                      # source-project leftovers
```

**4. Nothing is left behind.** The source tree (`app/`, `api/`, old `tests/`, `requirements.txt`)
is gone. `migration/INVENTORY.md` shows every row migrated or explicitly dropped with a reason.

**5. The DI graph resolves.** There is no graph-completeness validation, so a missing binding only
surfaces at runtime. Boot the app and hit it for real:

```bash
docker compose up -d
uv run alembic upgrade head
uv run uvicorn src.main:app --reload
```

Then exercise **at least one route per entity** — one write, one read, one authenticated — and
confirm: the response body is camelCase, an `X-Request-ID` header comes back, one JSON
`request.completed` log line appears per request carrying `request_id` (and `user_id` on
authenticated routes), and a deliberate failure returns an opaque
`500 {"detail": "Internal Server Error"}` with a correlated `request.unhandled_exception` entry in
the log. Report actual output — do not assert success from the code alone.

**6. Route parity.** Compare `[route.path for route in app.routes]` against the Phase 0 inventory.
Every source route has a counterpart. Report the old → new URL mapping.

**7. Connections are not leaking.** After a run including any background task, the pool is not
exhausted (§9.6).

---

## 14. Anti-patterns — never

Each one exists because it has bitten this codebase or would silently defeat it.

- An **anemic domain** — invariants and state transitions belong on the entity, not in a use case.
- **Bindings outside the composition root** (`AppModule.configure()` or the per-domain `register()` functions it calls); binding through plain tuples instead of `TypedBinder`, which drops the static check; binding modules in `src/application/` instead of the API layer.
- **Omitting `@inject`** on an implementation whose `__init__` takes dependencies — resolution fails with `TypeError` at runtime.
- Keeping **session state in a module-global `ContextVar`** (the transaction context's per-task `ContextVar` is an instance member of the request-scoped adapter, not module-global); **injecting an `AsyncSession` into a use case or a repository** — repositories get sessions through the injected `ConnectionFactory` (`read()` / `write()`), use cases never touch a session.
- **Committing or rolling back inside a repository** — the transaction context owns the boundary (auto-commit on clean exit, rollback on exception). Putting the repository's `try`/`except` **inside** the `write()` block instead of outside it.
- **Re-implementing driver-error classification** per repository instead of importing `is_deadlock` from `src/infrastructure/database/errors.py`.
- Calling `commit()` **from a use case** — there is no `commit()`; the outermost `begin()` commits on a clean exit. Abort with `await transaction.rollback()` (benign non-success result) or by letting an exception propagate. Wrapping a **single** write in `begin()` — a single repository write self-commits; `begin()` is only for **multi-write** atomicity.
- Returning **`JSONResponse(model.model_dump())`** from a route.
- A `try`/`except` that **only logs, re-raises, wraps, or hand-builds a 500** — the middleware does that once for every route. Catch only to translate (to a result enum, to `None`) or to undo (rollback). Never swallow an error behind a fake success. Exception: a `BackgroundTasks` callable must catch and log for itself.
- Rewriting **`RequestScopeMiddleware` as a `BaseHTTPMiddleware` dispatch function** — the scope would dispose its request-scoped collaborators (the write unit of work, the `Logger`, the `UserContext`) under background tasks and streaming bodies, which still resolve the same disposed instances, silently.
- Making ports **ABCs** or suffixing them **`Base`** — use `Protocol`.
- **Duplicating docstrings on adapters** — the port is the single documented contract, resolved through the MRO.
- **Module docstrings or file header comments**, anywhere.
- **Classes of only static methods** — use module functions.
- Packing **every step of an operation into one method** — extract each nameable sub-goal into a helper.
- **Bypassing use cases** — routes never call repositories directly.
- Using **`DTO`** in any name; suffixing a model `Request`/`Response` when it is not that HTTP body; inventing a model to carry a use case's arguments (pass scalars).
- Letting **`src/ports/` import from Application** — a type a port returns belongs beside the port.
- Adding **`# noqa`, `# type: ignore`, or any suppression** without checking with the user first.

---

## 15. Reference — the worked example

The template repository *is* the reference implementation. When a rule here is ambiguous, the code
wins. Read, in order:

- `src/domain/entities/user/user.py` — a non-anemic aggregate root.
- `src/domain/repositories/user/user_repository.py` — the documented port.
- `src/infrastructure/repositories/user/sqlalchemy_user_repository.py` — the adapter, error mapping, `_to_entity`.
- `src/application/use_cases/user/create_user_use_case.py` — the transaction boundary.
- `src/application/use_cases/auth/login_use_case.py` — a multi-port use case returning a result enum.
- `src/api/routers/user/` — route per operation + aggregation.
- `src/api/dependencies/providers.py` — the composition root.
- `src/api/middleware/registration.py` — the ordering, and why.
- `tests/api/routers/user/conftest.py` — the route-test rig.
- `AGENT.md` — all of it.
