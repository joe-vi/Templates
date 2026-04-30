---
name: fastapi-clean-architecture-mode
description: Activate Clean Architecture rules for the current FastAPI session — enforces unidirectional layer dependencies, repository pattern with result enums, dependency inversion via fastapi-injector, and all naming conventions on every file written or edited until the session ends.
when_to_use: When working in a FastAPI project and you want Clean Architecture rules — strict layer boundaries, dependency inversion, repository pattern, DI discipline — enforced for this session without scaffolding or running a full audit.
mode: true
disable-model-invocation: true
version: "1.1.0"
---

# FastAPI Clean Architecture — Mode Skill

Activates Clean Architecture rules for the current FastAPI session.

For scaffolding a new project use `/fastapi-clean-architecture-template`. To audit an existing project use `/fastapi-clean-architecture-review`.

---

## On activation

1. Read `rules.md` from this skill's directory — it contains the full rule set. Apply every rule to all files written or edited for the rest of this session.

2. Confirm to the user: "FastAPI Clean Architecture mode is active. All architecture rules are now enforced for this session."

3. Check whether a `CLAUDE.md` file exists in the project root:

   **If `CLAUDE.md` does not exist:**
   Offer to create a minimal one that imports the rules non-destructively:
   ```
   Create CLAUDE.md containing:
     @.claude/fastapi-ca-rules.md
   Create .claude/fastapi-ca-rules.md by copying rules.md from this skill.
   ```
   Tell the user: "A minimal CLAUDE.md has been created. It imports the FastAPI Clean Architecture rules automatically on every future session — no need to invoke this skill again."

   **If `CLAUDE.md` already exists:**
   Do NOT overwrite or replace it. Instead check whether it already references the FastAPI CA rules. If it does not, offer to append a single import line:
   ```
   Append to the end of the existing CLAUDE.md:

   ## FastAPI Clean Architecture Rules
   @.claude/fastapi-ca-rules.md
   ```
   And create `.claude/fastapi-ca-rules.md` by copying `rules.md` from this skill.
   Tell the user: "One import line has been appended to your existing CLAUDE.md. Your existing configuration is untouched."

   In both cases, the actual rules live in `.claude/fastapi-ca-rules.md` — a self-contained file that can be updated independently of CLAUDE.md.
