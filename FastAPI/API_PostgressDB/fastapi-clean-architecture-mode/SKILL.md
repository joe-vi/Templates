---
name: fastapi-clean-architecture-mode
description: Activate Clean Architecture rules for the current FastAPI session — enforces unidirectional layer dependencies, ports as typing.Protocol, the repository pattern with result enums, typed declarative dependency injection (injector + TypedBinder: one binding per line with explicit scopes, conformance checked by mypy), and all naming conventions on every file written or edited until the session ends.
disable-model-invocation: true
metadata:
  version: "2.0.0"
---

# FastAPI Clean Architecture — Mode Skill

Activates Clean Architecture rules for the current FastAPI session. Everything Claude writes or edits from this point will follow the 4-layer structure, dependency direction, ports-and-adapters pattern, and naming discipline.

For scaffolding a new project use `/fastapi-clean-architecture-template`. To audit an existing project use `/fastapi-clean-architecture-review`.

---

## On activation

1. Read `rules.md` from this skill's directory — it contains the full rule set. Apply every rule to all files written or edited for the rest of this session.
2. Confirm to the user: "FastAPI Clean Architecture mode is active. All architecture rules are now enforced for this session."
