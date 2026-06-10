# Critical Review — FastAPI Clean Architecture Template

Scope: `FastAPI/API_PostgressDB/`. Findings are ordered by severity. Each item
states the problem, where it lives, why it matters, and what to do about it.
This is a critique, not a celebration — the things that work are not listed.

---

## CRITICAL

### C1. No authorization — any authenticated user is effectively an admin
`src/api/routers/user/user_routes.py:13-17`, `src/api/dependencies/jwt_dependency.py`

The entire user router is guarded only by `get_current_user`, which performs
**authentication** (is the token valid?) and never **authorization** (is this
user allowed to do this?). The decoded `role` is pushed into `UserContext` and
then *never read by anything*.

Consequences for a freshly-copied template:
- A user with `role=user` can `POST /users`, `DELETE /users/{id}` for anyone,
  and — worst — `PATCH /users/{id}/role` to set their own role to `admin`.
- That is a textbook privilege-escalation / IDOR hole shipped as the default.

A "clean architecture" template that builds an entire request-scoped
`UserContext` + role plumbing and then enforces nothing is misleading: it looks
secure without being secure. Provide a role/permission dependency
(`require_role(UserRole.ADMIN)`) and apply it, or drop the role plumbing
entirely so nobody assumes it does something.

### C2. The advertised camelCase contract is silently violated; `response_model` is decorative
`src/api/result_status_maps.py:67-72,85-90,103-108`, `src/api/routers/auth/auth_routes.py:44-48,96-100`, `src/api/schemas/base_schema.py`

`APIModelBase` is sold (AGENT.md §2) as "serialises to camelCase JSON". But
every mutating endpoint and both auth endpoints build the body with
`JSONResponse(content=SomeModel(...).model_dump())`.

Verified behaviour (Pydantic v2):
- `model_dump()` with no args emits **snake_case** (`{'access_token': ...}`,
  `{'created_at': ...}`), because `by_alias` defaults to `False`.
- Returning a `Response` object **bypasses** FastAPI's `response_model`
  entirely — no serialization, no alias application, no validation.

Meanwhile the read endpoints (`GET /users`, `GET /users/{id}`) return the model
*object*, so FastAPI serializes it with `by_alias=True` → **camelCase**
(`createdAt`).

Net result: the same API emits `createdAt` on GET and `created_at` /
`access_token` on everything else. The `response_model=` declarations are
purely cosmetic (OpenAPI only) and cannot catch response-shape drift. Either
return models directly (let FastAPI serialize) or pass
`model_dump(by_alias=True)` — and stop declaring `response_model` while
returning raw `JSONResponse`, because it gives a false sense of a typed
contract.

### C3. Insecure defaults baked into settings
`src/config/settings.py:40`, `:17`

```python
jwt_secret_key: str = "changeme-use-a-strong-random-secret-in-production"
db_password: str = "postgres"
```

A template is *designed to be copied*. A defaulted JWT signing key means any
deployment that forgets `.env` boots with a **publicly known secret**, so
anyone can forge admin tokens. Secrets must have **no default** and fail fast
at startup (`jwt_secret_key: str` with no value → `ValidationError` if unset).
Defaulting them trains every downstream user into an insecure habit.

### C4. Refresh tokens never re-validate the user
`src/application/use_cases/auth/auth_use_case.py:80-99`

`refresh_token()` decodes the token and immediately mints a new access+refresh
pair. It never checks that the user still exists, is still `ACTIVE`, or still
has the role embedded in the token. Combined with no revocation list and
rotating refresh tokens that don't invalidate their predecessor:
- A deleted or deactivated account keeps minting valid access tokens until the
  refresh token's natural expiry (default 7 days).
- A demoted admin keeps an admin-roled token for the access-token lifetime, and
  can refresh the stale role indefinitely.

At minimum, re-load the user on refresh and re-embed current role/status.

---

## HIGH (architecture & correctness)

### H1. `begin_transaction` and "repositories swallow exceptions" are mutually incompatible
`src/infrastructure/database/connection_factory.py:47-94`, `src/infrastructure/repositories/user/user_repository.py:50-64,149-180`

The repository contract (AGENT.md §3) says mutations **catch all DB exceptions
and return result enums** — nothing propagates. Separately, `begin_transaction`
shares one session across repos via a `ContextVar` and commits on clean exit.

These two rules collide. Inside a `begin_transaction` block, if a repo's
`flush()` raises `IntegrityError`, the repo swallows it and returns
`UNIQUE_CONSTRAINT_ERROR`. The shared session is now in an **aborted**
transaction state, but no exception propagated — so the outer
`async with session.begin()` exits "cleanly" and issues a **COMMIT on an
aborted transaction**, which raises (`PendingRollbackError` / driver error).
The "all-or-nothing atomic" feature is therefore unsafe by construction: a
failure in any step corrupts the commit instead of producing a clean rollback.

Compounding it: **nothing in the codebase ever calls `begin_transaction`.** The
`TransactionManager` (`src/infrastructure/database/transaction_manager.py`) is a
do-nothing delegate, untested, and unused. The template ships a complex,
latent-broken feature that has never been exercised. Either make the
swallow-vs-propagate model coherent (e.g. repos *don't* swallow inside a UoW)
and add a real test, or delete the transaction machinery until it's needed.

### H2. Implicit session sharing through a module-global `ContextVar` is spooky-action-at-a-distance
`src/infrastructure/database/connection_factory.py:18,51-60`

`get_session()` silently changes behaviour based on `_active_session`, a global
set somewhere else entirely. A repository method's transactional semantics now
depend on invisible ambient state rather than its inputs. This is hard to
reason about, hard to test in isolation, and breaks under nesting: a nested
`begin_transaction` overwrites the ContextVar, so the "inner" work commits on a
*different* connection than the "outer" — silently non-atomic despite the
abstraction promising atomicity. An explicit Unit-of-Work passed as a parameter
is more verbose but honest; hidden globals are exactly what clean architecture
is supposed to avoid.

### H3. Over-abstraction: pass-through layers and a 6-model user for plain CRUD
`src/application/use_cases/user/user_use_case.py`, `user_dto.py`, `user_converter.py`, `src/domain/entities/user/user.py`

The use cases contain **no business logic**. `delete_user` → `repository.delete`;
`update_user_role` → `repository.update_role`; `get_all_users` → fetch + map.
They are indirection, not behaviour. Meanwhile a single user is represented six
ways — `UserModel`, `User` (entity), `CreateUserDTO`, `UserDTO`,
`UserCreateRequest`, `UserResponse` — wired together by **two** converter
classes (`UserEntityConverter`, `UserConverter`) doing field-for-field copies.

This is the classic anemic-domain-model + converter-explosion anti-pattern.
Clean Architecture's layering pays off when there is domain logic to protect;
applied to trivial CRUD it produces "lasagna code" — many thin layers, high
boilerplate-to-value ratio, every new field touched in ~6 files. The template
should either (a) include a non-trivial use case that justifies the structure,
or (b) be honest that this much ceremony is overkill for CRUD.

### H4. Repositories swallow *every* exception with zero logging
`src/infrastructure/repositories/user/user_repository.py:63-64,156-157,179-180`

```python
except Exception:
    return operation_results.CreateResult.FAILURE
```

A blanket `except Exception` catches `AttributeError`, `TypeError`, mapping
bugs, connection exhaustion — everything — and collapses them to an opaque
`FAILURE` → HTTP 500 with no log line, no stack trace, no correlation id. The
project has a structured logger but the repository never uses it. In production
this is undebuggable: real bugs masquerade as generic failures and disappear.
Catch the specific DB exceptions you map; let unexpected ones propagate to a
global handler that logs them.

---

## MEDIUM (smells & gaps)

### M1. No pagination
`src/infrastructure/repositories/user/user_repository.py:90-108`, `get_all` / `GET /users`

`get_all()` does `SELECT * FROM users` and materializes everything. In a
template people copy verbatim, an unbounded list endpoint is a built-in
performance/DoS footgun. Ship limit/offset (or keyset) pagination as the
default pattern.

### M2. Duplicated entity-mapping
`src/infrastructure/repositories/user/user_repository.py:80-88,124-132`

`get_by_id` and `get_by_username` contain identical `User(...)` construction
blocks; `get_all` repeats it a third time. Extract a private
`_to_entity(model) -> User`. Right now adding a column means editing three
copies.

### M3. Redundant database indexes (verified against the migration)
`src/infrastructure/database/models/user_model.py:25-28`, `alembic/versions/4d9f6f49ad6f_*.py:36-37`

- `email`: `index=True` **and** `UniqueConstraint("email", ...)`. In Postgres a
  unique constraint already creates a unique index, so this produces **two**
  indexes on `email` (`ix_users_email` + the unique index).
- `id`: `index=True` **and** `primary_key=True`. The PK is already indexed, so
  `ix_users_id` is a second redundant index.

Both redundant indexes are real — they're in the generated migration. Drop the
`index=True` flags; they only add write overhead.

### M4. `passlib` is unmaintained and forces a bcrypt pin; no 72-byte guard
`pyproject.toml:19-20`, `src/infrastructure/auth/password_hasher.py`

`passlib` 1.7.4 is effectively abandoned and is incompatible with `bcrypt>=4`
(the well-known `module 'bcrypt' has no attribute '__about__'` issue), which is
why `bcrypt>=3.2.0,<4.0` is pinned — you're stuck on an old bcrypt to keep a
dead library working. bcrypt also silently truncates passwords beyond 72 bytes,
which isn't guarded. Prefer the `bcrypt` package directly, or
`argon2-cffi`/`pwdlib`.

### M5. Over-engineered concurrency handling
`src/infrastructure/repositories/user/user_repository.py:55-62,149-155,172-178`, `src/domain/enums/operation_results.py`

Every mutation inspects `exc.__cause__` for `DeadlockDetectedError` and maps to
`CONCURRENCY_ERROR`. For a single-row `INSERT`/`UPDATE`/`DELETE`, deadlocks are
essentially never produced, so `CreateResult.CONCURRENCY_ERROR` is dead weight
copied into every method. `LoginResult.FAILURE` is similarly never produced by
the auth use case. Don't model error states the code can't actually reach.

### M6. No global error handling, CORS, security headers, or login rate-limiting
`src/main.py`

No `app.add_exception_handler`, no CORS middleware, no rate limit on
`POST /auth/login` (open to credential brute-force). For a template positioned
as production-shaped, these omissions are notable — at least the global
exception handler is needed to make H4 survivable.

### M7. Type model fights itself (`# type: ignore` smell)
`src/application/use_cases/user/user_converter.py:21,26`, `src/application/use_cases/auth/auth_use_case.py:66-71`

`User.id` / `User.created_at` are `… | None` (unpersisted state) but `UserDTO`
requires non-optional, so the converter is littered with `# type: ignore`. The
"persisted vs not-yet-persisted" states are conflated into one dataclass.
Strict typing is configured (`disallow_untyped_defs = true`) yet routinely
suppressed — that defeats the point. Model the two states distinctly (e.g. a
`NewUser` input vs a persisted `User`) and the ignores disappear.

---

## LOW (documentation, consistency, hygiene)

### L1. Documentation contradicts the code
- **Line length:** `pyproject.toml:50` sets `line-length = 80`; `CLAUDE.md:58`
  says "Max line length: **140 characters**" (AGENT.md correctly says 80, so
  CLAUDE.md is simply wrong).
- **`create_all`:** `AGENT.md:349` claims "This template uses `create_all()`
  for simplicity." There is **no `create_all` anywhere** in the codebase
  (verified) — it uses Alembic. Stale, misleading guidance.
- **`updated_at`:** `AGENT.md:166-167` documents `updated_at` with
  `onupdate=func.now()` as a core DB pattern. No `updated_at` column exists in
  the model or migration, and the entity has no such field. The docs describe a
  column that isn't there.
- **Login docstring:** `auth_routes.py:31` says tokens "embed the user's id,
  username, and role." The token embeds `sub` and `role` only — no username
  (`token_service.py:42-47`).

### L2. Seven overlapping agent-instruction files with a manual sync mandate
`.cursorrules`, `.clinerules`, `.windsurfrules`, `AGENT.md`, `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.antigravity/rules.md`

`AGENT.md:353-365` instructs maintainers to hand-sync rules across all of these.
L1 already shows the drift this guarantees. Keep one source of truth and have
the rest be thin symlinks/includes, not parallel copies.

### L3. `from_attributes=True` on `UserResponse` is dead config
`src/api/routers/user/user_schema.py:42`

`UserResponse` is always constructed via the explicit converter from a DTO,
never with `model_validate(orm_obj)`, so `from_attributes=True` does nothing.
Remove it or stop using the converter.

### L4. `test_api.py` is misplaced and brittle
`test_api.py` (repo root)

It lives outside `tests/`, spawns a real uvicorn process, and requires a live
Postgres plus the seeded admin. It duplicates the route coverage already in
`tests/api/` and won't run in CI without infrastructure. It's an integration
smoke script masquerading as a test — name and locate it as such, or fold it
into a proper integration suite gated behind a DB fixture.

### L5. Bootstrap depends on a hardcoded bcrypt hash in a migration; no signup path
`alembic/versions/4d9f6f49ad6f_*.py:40-52`

The only way to get the first usable account is a bcrypt hash embedded in the
initial migration (and there is no public signup endpoint, by design). Rotating
that bootstrap password means writing a new migration. Fine for a demo; call it
out explicitly, and never let that default hash reach a real environment.

### L6. The user default is defined in three places
`src/domain/entities/user/user.py:17-18`, `src/application/use_cases/user/user_dto.py:24-25`, `src/infrastructure/database/models/user_model.py:33-37`

`role`/`status` defaults are declared on the entity, on the create DTO, and as
SQLAlchemy column defaults — and `create()` passes them explicitly anyway, so
the column default never fires. Three sources of truth for one rule; they will
drift.

---

## Summary

The template is internally consistent and the layer boundaries are mechanically
respected, but it has **two genuinely dangerous defaults** (no authorization,
defaulted secrets), **a broken-and-unused transaction feature**, an
**inconsistent serialization contract that its own docs promise**, and a
**boilerplate-to-value ratio that's hard to justify for CRUD**. The supporting
documentation also contradicts the code in several places. Address C1–C4 before
anyone ships from this; treat H1–H4 as required cleanup before calling the
architecture "clean."
