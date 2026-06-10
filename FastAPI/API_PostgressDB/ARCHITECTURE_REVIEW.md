# Structural & Infrastructure Critique — FastAPI Clean Architecture Template

This review ignores feature/placeholder concerns (auth policy, pagination,
validation, secret handling) and logic bugs. It targets only **structure**,
**infrastructure components** (ConnectionFactory, DI, session/transaction
management), and **whether the patterns are idiomatic for Python and FastAPI**.

The short version: the template is a faithful port of a C#/Java/Guice
"Clean Architecture + IoC container" layout into Python. Most of the friction
comes from importing idioms that Python and FastAPI already solve natively, and
then having to build scaffolding to make the imported idioms work.

---

## 1. Two dependency-injection systems running in parallel

`src/container.py`, `src/main.py:40-41`, `src/api/dependencies/jwt_dependency.py`

FastAPI ships a first-class DI system (`Depends`) with request-scoped caching,
`yield` setup/teardown, sub-dependencies, and `dependency_overrides` for tests.
This template bolts a **second** container on top — `injector` +
`fastapi-injector` — and then forbids the native one (AGENT.md §3: "never use
`Depends()` for use cases, use `Injected()`").

Why this is a structural problem, not just a taste call:

- **`Injected()` is itself implemented on top of `Depends`.** So the rule
  "don't use Depends, use Injected" is illusory — you're using `Depends`
  underneath, plus a whole extra container above it. You now maintain two
  mental models and two resolution mechanisms for one job. The JWT guard proves
  it: `get_current_user` mixes `Depends(_security)` *and*
  `Injected(TokenServiceBase)` in the same signature.
- **`injector` is a Guice clone — constructor injection with explicit
  binding.** That is a Java idiom. In Python you rarely need a container: duck
  typing + `Depends` + module-level singletons cover the same ground without a
  binding registry.
- **Every `__init__` must be decorated `@inject` or the app dies at startup.**
  The docs list this as a top "anti-pattern / debugging tip"
  (`AGENT.md:106,325,345`). A framework that requires boilerplate on every
  class, where forgetting it is a documented recurring failure mode, is adding
  fragility, not removing it.
- **`request_scope` only works if `InjectorMiddleware` is added before
  `attach_injector`, which must run before routers are included.** Three
  ordering constraints on global setup, each documented as a `LookupError`
  source (`AGENT.md:107,326-327`). That is exactly the kind of order-dependent
  global wiring FastAPI's native DI avoids.
- **You lose FastAPI-native testing.** The route test has to construct a second
  `Injector`, a `TestModule`, `InstanceProvider`, *and* still fall back to
  `app.dependency_overrides` for the guard
  (`tests/api/routers/user/test_user_routes.py:42-58`) — i.e. it uses both DI
  systems to test one endpoint.

Net: the container earns its keep only if you have deep graphs that are painful
to wire by hand. For a CRUD service, `Depends` providers (`get_user_use_case`,
`get_session`) would be shorter, idiomatic, and fully framework-integrated.

---

## 2. ConnectionFactory: session state lives in a module global

`src/infrastructure/database/connection_factory.py:18,47-94`

```python
_active_session: ContextVar[AsyncSession | None] = ContextVar("_active_session", default=None)
```

The "current session" is a **module-level `ContextVar`**, while
`ConnectionFactory` is a **singleton**. So the object that is supposed to own
session lifecycle doesn't actually hold the session — the session hangs off
global module state that any code in the async context can observe. That is
"action at a distance": a repository method's transactional behaviour is
decided by invisible ambient state set by something else entirely.

Concrete structural consequences:

- **`get_session()` is overloaded to mean three different things** depending on
  hidden state: (a) standalone autocommit write session, (b) standalone
  read-only session, (c) silently enlist in an ambient transaction. One method,
  one signature, three behaviours selected by a global flag and a boolean. That
  is hard to read and harder to test.
- **Concurrency hazard baked into the design.** `AsyncSession` is not safe for
  concurrent use. Because the session is shared via `ContextVar`, the moment a
  use case does `asyncio.gather(repo_a.x(), repo_b.y())` inside
  `begin_transaction`, both calls grab the *same* session on the *same*
  connection concurrently → corruption. The pattern invites the bug.
- **Nesting silently breaks atomicity.** A nested `begin_transaction`
  overwrites the ContextVar with a new session/connection, runs, commits
  independently, then `reset()`s back to the outer token. The inner work
  committed on a different connection than the outer — "atomic" in name only.

The idiomatic FastAPI approach is a single request-scoped session yielded by a
`Depends(get_session)` dependency (or an explicit Unit-of-Work object passed as
a parameter). Both make the session visible and owned, instead of ambient.

---

## 3. `begin_transaction` uses a non-idiomatic "rollback callable" + a redundant wrapper

`src/infrastructure/database/connection_factory.py:69-94`, `src/infrastructure/database/transaction_manager.py`, `src/application/services/transaction_manager_base.py`

Two separate problems here.

**(a) The rollback-flag-via-yielded-coroutine is convoluted.**
```python
async def rollback() -> None:
    nonlocal should_rollback
    should_rollback = True
yield rollback
```
The context manager yields an `async` callable whose only effect is to set a
`bool`. It does nothing awaitable — making it a coroutine is misleading.
Callers must remember to `await rb()` to abort. The idiomatic context-manager
contract is "commit on clean exit, roll back on exception"; bolting on a manual
abort flag re-invents control flow that `raise`/`except` already expresses.

**(b) `TransactionManager` is pure indirection that exists only to satisfy a
rule.** `ConnectionFactoryBase` already exposes `begin_transaction()`.
`TransactionManagerBase` declares the *identical* signature, and
`TransactionManager` implements it by… calling `ConnectionFactory.begin_transaction()`:
```python
def begin_transaction(self):
    return self._connection_factory.begin_transaction()
```
No behaviour is added. The class exists solely because the layering rule says
use cases may not see `ConnectionFactoryBase`. The contract docstring is
copy-pasted across both ABCs (`connection_factory_base.py:34-58` vs
`transaction_manager_base.py:11-41`). An abstraction whose only job is to
forward one call to another abstraction with the same shape is a layer tax, not
a design.

(And note the whole transaction subsystem is never invoked anywhere in the
template — it is untested scaffolding.)

---

## 4. ABCs used as interfaces where `Protocol` is the Pythonic tool

`src/domain/repositories/user/user_repository_base.py`, every `*_base.py`

Every port is an `abc.ABC` with all methods `@abstractmethod` and zero shared
behaviour: repository, use case, connection factory, transaction manager,
password hasher, token service, logger, user context. That is precisely the
"interface" use case `typing.Protocol` was added for.

Using `ABC` here means:
- Implementations must **nominally subclass** and therefore **import** the port
  (`class UserRepository(UserRepositoryBase)`). With `Protocol` (structural
  typing) the implementation needs no import of and no inheritance from the
  port — looser coupling, which is the entire point of "dependency inversion."
- You can't satisfy a port with a pre-existing/third-party class without writing
  an adapter subclass.

ABCs aren't *wrong*, but a "clean architecture" template that's all interfaces
and no shared base behaviour is the canonical argument *for* `Protocol`. Shipping
`ABC` everywhere reads as a C#/Java transliteration.

---

## 5. Naming: the interface is `...Base`, the implementation gets the clean name

`UserRepositoryBase` (port) → `UserRepository` (impl); `ConnectionFactoryBase` →
`ConnectionFactory`; etc.

In idiomatic Python the *abstraction* usually owns the clean, central name
(`UserRepository`, or a `UserRepository` Protocol) and the *implementation* is
qualified by its mechanism (`SqlAlchemyUserRepository`, `PostgresUserRepository`,
`BcryptPasswordHasher`). This template inverts that: the abstraction is tagged
with a `Base` suffix (an inheritance-mechanics word, not a domain word) and the
concrete SQLAlchemy class claims the unqualified name — which also means the
name gives no hint that it's the Postgres/SQLAlchemy variant. When a second
implementation appears, the naming scheme has nowhere to go.

---

## 6. Converters are static-method classes (Java utility-class idiom)

`src/application/use_cases/user/user_converter.py`, `src/api/routers/user/user_converter.py`, `src/api/routers/auth/auth_converter.py`

```python
class UserConverter:
    @staticmethod
    def to_create_dto(...): ...
    @staticmethod
    def to_response(...): ...
```

These classes are never instantiated and hold only `@staticmethod`s. In Python
a class that is purely a namespace for stateless functions is an anti-pattern —
**the module is the namespace**. `user_converter.to_create_dto(...)` (plain
module functions) is the idiomatic form; the wrapping class adds a level of
indirection and a meaningless `self`-less type for no benefit.

Structurally this also fragments mapping logic across **three** sites that
aren't unified: schema↔DTO (`api/.../user_converter.py`), entity↔DTO
(`application/.../user_converter.py`), and model↔entity done *inline and
duplicated* inside the repository (`user_repository.py:80-88,124-132`). Two of
the three conversions are formalised as classes; the third is copy-pasted. The
boundaries multiply the mapping rather than containing it.

---

## 7. Package layout: deep, sparse, single-item packages + module-alias imports

`src/domain/entities/user/user.py`, `src/domain/repositories/user/user_repository_base.py`, …

"Organise by type, then by entity" (AGENT.md §1) produces a very deep tree where
most directories hold exactly one file for one entity: `entities/user/user.py`,
`repositories/user/user_repository_base.py`,
`use_cases/user/user_use_case.py`, and so on. A single `User` entity spans
~20 directories and a swarm of `__init__.py` files. For one entity that's a lot
of near-empty packages to navigate; the structure scales in directory count
faster than in actual code.

It also forces the codebase's pervasive **module-aliasing import style**:
```python
from src.domain.entities.user import user as user_module
... user_module.User
from src.application.use_cases.user import user_dto as user_dto_module
```
Because the module is named `user` and the class `User` (and the path is deep),
every file imports the *module* and aliases it, then dotted-accesses the class.
This is unusual Python — the common form is `from ....user import User`. The
alias-everything convention adds noise to every file and is a direct symptom of
the `entity/entity.py` nesting. (`# type: ignore` markers in the converters are
a secondary symptom of the same over-structuring.)

---

## 8. Global singletons and a composition root that reaches into them

`src/container.py:89`, `src/main.py:27-30,40-41`

`injector = Injector([AppModule()])` is a module-level, import-time singleton.
`main.py` then both attaches it to the app *and* reaches back into the global
(`container.injector.get(ConnectionFactoryBase)`) inside `lifespan`. So shutdown
is coupled to a module global rather than to app state. The cleaner shape is to
build the injector in the lifespan / app factory and hang it on `app.state`,
keeping a single ownership path. As written, anything that imports `container`
triggers container construction as a side effect of import.

---

## 9. Scope mixing is fragile across NoScope intermediaries

`src/container.py:58-86`, `src/infrastructure/logging/custom_logger.py`

`CustomLogger` and `UserContext` are `request_scope`; use cases and repositories
are unscoped (`injector` default `NoScope` = new instance per resolution);
`ConnectionFactory`/hashers/token service are `singleton`. An unscoped
`AuthUseCase` depends on a request-scoped `CustomLogger`, which depends on a
request-scoped `UserContext`. This only resolves correctly *inside* a live
request (the `InjectorMiddleware` window).

The trap: resolve any of these outside that window — a `BackgroundTasks`
callback (which runs *after* the middleware/response), a startup hook, a CLI
script — and the request-scoped leaf raises `LookupError` or yields a stale
instance. Threading request scope through unscoped objects means the safe
resolution context is implicit and easy to violate. FastAPI's own request scope
(plain `Depends`) is bounded by the endpoint and doesn't leak this way.

---

## 10. Fighting FastAPI's response model instead of using it

`src/api/result_status_maps.py:67-72`, `src/api/routers/auth/auth_routes.py:44-48,96-100`

Endpoints declare `response_model=...` but then return
`JSONResponse(content=Model(...).model_dump())`. Returning a `Response` object
**bypasses** `response_model` entirely — FastAPI does no serialization,
filtering, or alias application. So `response_model` here is dead decoration
(OpenAPI only), and the hand-built `model_dump()` (snake_case, no `by_alias`)
silently diverges from the camelCase that `APIModelBase` was created to
guarantee — while the read endpoints, which *do* return the model object, get
FastAPI's camelCase serialization. Same API, two serialization paths, because
the framework's serializer is bypassed on half the routes.

This is a structural mismatch: the whole `APIModelBase` + `response_model`
apparatus is set up and then routed around. Either return the model and let
FastAPI serialize (set status via the route decorator / `response.status_code`),
or don't declare `response_model` on routes that return raw `JSONResponse`.

---

## Bottom line

None of these are bugs in the "it crashes" sense; they're the cost of mapping a
container-centric, interface-everywhere, layer-per-concern architecture onto a
stack (Python + FastAPI) that provides lighter native answers for most of it. In
rough priority for a template that others will copy:

1. **Drop the second DI container** (§1) or justify it with a graph that
   actually needs it; lean on `Depends`.
2. **Make session ownership explicit** (§2) — request-scoped `Depends(get_session)`
   or an explicit UoW — instead of a module-global `ContextVar`, and rework the
   `begin_transaction` rollback-callable (§3).
3. **Prefer `Protocol` over `ABC`** for the ports (§4) and rename so the
   abstraction owns the clean name (§5).
4. **Convert the static-method converter classes to module functions** (§6) and
   stop bypassing `response_model` (§10).
5. The deep single-item packages + alias imports (§7) and global composition
   root (§8) are lower-stakes but compound the daily friction.
