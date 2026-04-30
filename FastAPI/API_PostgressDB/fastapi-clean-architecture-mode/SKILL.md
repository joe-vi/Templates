---
name: fastapi-clean-architecture-mode
description: Activate Clean Architecture rules for the current FastAPI session — enforces unidirectional layer dependencies, repository pattern with result enums, dependency inversion via fastapi-injector, and all naming conventions on every file written or edited until the session ends.
disable-model-invocation: true
metadata:
  version: "1.1.0"
---

# FastAPI Clean Architecture — Mode Skill

Activates Clean Architecture rules for the current FastAPI session. Everything Claude writes or edits from this point will follow the 4-layer structure, dependency direction, repository pattern, and naming discipline.

For scaffolding a new project use `/fastapi-clean-architecture-template`. To audit an existing project use `/fastapi-clean-architecture-review`.

---

## On activation

1. Read `rules.md` from this skill's directory — it contains the full rule set. Apply every rule to all files written or edited for the rest of this session.
2. Confirm to the user: "FastAPI Clean Architecture mode is active. All architecture rules are now enforced for this session."
