# Migration Prompt

Paste the prompt below into an agent session **opened in the FastAPI project you want to migrate**
(not in the template). Before pasting, copy these two files plus the template itself somewhere the
agent can read:

```bash
# from the project being migrated
mkdir -p migration
cp /path/to/template/migration/CLEAN_ARCHITECTURE_MIGRATION_GUIDE.md migration/
git clone <template-repo-url> /tmp/fastapi-clean-architecture-template   # or a local path
```

Then fill in the two placeholders at the top of the prompt (`<TEMPLATE_PATH>` and the project
description) and paste everything between the markers.

---

## The prompt

<!-- ────────────────────────── COPY FROM HERE ────────────────────────── -->

You are migrating this FastAPI project to the Clean Architecture + DDD structure defined by the
reference template at `<TEMPLATE_PATH>`.

**Read `migration/CLEAN_ARCHITECTURE_MIGRATION_GUIDE.md` in full before doing anything else, and
read `<TEMPLATE_PATH>/AGENT.md` in full after it.** Together they are the specification for this
work: the guide tells you what to do, `AGENT.md` and the template's own source tell you exactly what
the result must look like. Re-read the relevant guide section at the start of each phase rather than
working from memory — the rules are specific and the failure mode is confidently producing something
that looks right and violates four of them.

### What I want

Every file in this project ends up in one of three states: **moved and rewritten** into a layer
directory under `src/`, **replaced** by a chassis file copied verbatim from the template, or
**deleted** with its behaviour accounted for elsewhere. When you are finished, the old tree does not
exist and `src/` matches the target tree in §2 of the guide. This is a restructuring, not a redesign:
every route this project serves today must still be served, every business rule must still be
enforced. Do not add features, drop endpoints, or improve business logic in passing.

Carry over, exactly as specified in the guide:

- The **ruff and pyrefly configuration**, byte-identical to the template's (§10.1) — 140 columns,
  `select = ["E", "F", "I", "N", "W", "UP"]`, `skip-magic-trailing-comma = true`, pyrefly `legacy`
  preset. Do not soften a rule to make the code pass.
- The **pre-commit hook** (§10.2), running the same `uv run` commands as the gates, installed with
  `uv run pre-commit install`. If this project already has a pre-commit config, replace it — do not
  merge, and drop hooks for tools the template does not use (black, isort, flake8, mypy).
- An **`AGENT.md`** for this repo (§12), written for *this* project's entities and routes, plus the
  quick-reference mirrors, plus a rewritten `README.md`.

### How to work

Follow the phased procedure in §6 — **inward-out**: Domain, then Ports, Application, Infrastructure,
API. Run the four gates at the end of every phase and do not start the next one with them red:

```bash
uv run ruff check src/ tests/ --fix && uv run ruff format src/ tests/
uv run pyrefly check
uv run pytest
uv run pre-commit run --all-files
```

Do not migrate two entities in parallel. Take one aggregate end to end so the pattern is proven,
show me the result, then repeat for the rest.

**Start with Phase 0 and stop there.** Capture the current behaviour (test suite result, the full
route list with methods and status codes, the DB schema), then produce `migration/INVENTORY.md`: one
row per source module — its responsibility, its destination path(s) in the target tree, and any open
question. Keep it updated as you go; it is the artifact that proves nothing was missed. **Show me
the inventory and wait for my approval before touching any code.**

### Rules I care about most

These are the ones a migration gets wrong, all of them detailed in the guide:

- **Never add a suppression** — no `# noqa`, no `# type: ignore`, no pyrefly ignore comment — to
  make a gate pass. If a rule can only be satisfied by suppressing it, stop and show me the design
  alternatives.
- **Copy the chassis verbatim** (§3). `request_scope.py`, `typed_binder.py`,
  `request_scope_middleware.py`, the middleware, the ports, the DB machinery — including
  `connection_factory.py`, `sqlalchemy_connection_factory.py`, and `sqlalchemy_transaction_context.py`
  — copy the bytes. Do not adapt them to this project's existing conventions, and do not merge this
  project's `get_db`, logging setup, or exception handlers into them. Those get deleted.
- **Delete the `try`/`except` blocks** (§9). Most of this project's error handling duplicates the
  `exception_handler` middleware and goes away. Catch only to translate a failure into the layer's
  vocabulary (a result enum, `None` from a decode) or to undo work (rollback) — never merely to
  report. The one exception is a `BackgroundTasks` callable, which must catch and log for itself.
- **The domain must not be anemic** (§7.2). A rule that concerns one aggregate lives on the entity,
  not in a use case. If this project's "models" are dataclasses of fields and its "services" hold
  all the logic, that logic moves onto the entities — that is the substance of this migration, not a
  detail of it.
- **Never name anything `DTO`**, and never invent a model just to group a use case's arguments —
  pass scalars (§4).
- **Routes never call repositories.** Use cases never receive an `AsyncSession`. **Repositories inject
  the `ConnectionFactory`** — wrapping reads in `read()` (a fresh short-lived session) and writes in
  `write()` (the request write unit of work), with the `try`/`except` **outside** the `write()` block
  — and **never commit or roll back**. There is **no `commit()`**: the outermost `begin()` commits on
  a clean exit, so a **single-write** use case drops the transaction context and calls the repository
  directly, while a **multi-write** use case opens one `begin()` block for atomicity (rolling back
  explicitly on a benign non-success result). A DB error mid-unit rolls the whole unit back and every
  following write in it fails fast.
- URLs become `/api/<entity>/v1/...` with the version per-endpoint (§7.10). This is the one
  behaviour change the migration forces — record the old → new mapping and report it to me.

### Ask, don't guess

Raise these instead of deciding silently: a "service" that might be one operation or five; logic
that belongs to two aggregates at once; a model with no aggregate root; anything touching money,
permissions, or audit trails where the current behaviour looks accidental; any business rule you
cannot place cleanly in a layer. A wrong guess here is expensive to unwind later, and I would rather
answer a question than review a plausible invention.

### Done means

Everything in §13 passes, including the parts that need the app actually running:

1. All four gates green.
2. No suppressions added (`git diff` proves it).
3. The layer-boundary greps in §13.3 all return nothing.
4. The old tree is gone; `migration/INVENTORY.md` shows every row migrated or explicitly dropped
   with a reason.
5. **The app boots and serves real requests.** There is no DI graph validation in this
   architecture — a missing binding only surfaces at runtime, on first resolution. Start Postgres,
   run the migrations, start uvicorn, and exercise at least one write, one read, and one
   authenticated route per entity. Confirm: camelCase response bodies, an `X-Request-ID` header, one
   JSON `request.completed` log line per request carrying `request_id` (and `user_id` where
   authenticated), and an opaque `500 {"detail": "Internal Server Error"}` with a correlated
   `request.unhandled_exception` log entry on a deliberate failure. Show me the actual output.
6. Route parity against the Phase 0 inventory, with the old → new URL mapping reported.

Report honestly. If a test fails, show me the failure. If you skipped a step, say so. If a rule and
this project's reality genuinely conflict, tell me rather than bending the rule quietly.

<!-- ────────────────────────── COPY TO HERE ────────────────────────── -->

---

## Notes on using it

**Scope it if the project is large.** The prompt above migrates everything. For a big codebase,
append: *"Phase 2 onward, handle only the `<entity>` aggregate. Stop after its route tests pass and
show me the result."* Then re-run per aggregate. The chassis is copied once; entities are additive
after that.

**The Phase 0 stop is deliberate.** The inventory is where you catch a misread of the domain — a
"service" the agent plans to shatter into eight use cases, or two models it plans to fold into one
aggregate. Fixing that costs a sentence at Phase 0 and a day at Phase 5.

**If the project is not on `uv`,** add: *"This project uses `<pip/poetry/pipenv>`. Convert it to
`uv` as part of Phase 1: translate the dependency pins into `pyproject.toml` per §10.1, generate the
lockfile with `uv sync`, and delete the old dependency files."*

**If there is no test suite,** add: *"This project has no tests. Phase 0's behaviour capture rests on
the route inventory and manual exercise alone — flag that risk before you start, and write the domain
and use-case tests as you migrate rather than at the end."*

**If the source is not PostgreSQL,** the driver-error classification in
`src/infrastructure/database/errors.py` is asyncpg-specific (`is_deadlock` unwraps `__cause__` to an
asyncpg error type). Add: *"This project uses `<database>`. Adapt `errors.py`'s classifiers to that
driver, keeping the module as the single shared place they live — never per repository."*
