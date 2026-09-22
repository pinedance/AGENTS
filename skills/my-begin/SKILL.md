---
name: my-begin
description: >
  Initializes workspace context at session/task start: loads and strictly enforces project directives
  (AGENTS.md, rules, memory) and discovers/confirms/enforces project runtime execution prefixes (uv, poetry, pnpm, etc.).
---

# My Begin — Workspace Initialization, Directives & Runtime Binding

---

## STEP 0: DIRECTIVES INGESTION (SILENT)

**Execute tool calls silently. DO NOT output text until completed.**

1. **Read Directives**:
   - `view_file` on `<root>/.agents/AGENTS.md` or `<root>/AGENTS.md` (skip if absent).
   - `view_file` on `<root>/.agents/AGENTS.local.md` (skip if absent).
   - List `<root>/.agents/rules/` (or `<root>/rules/`) and `view_file` on each active `.md` rule file.
   - List `<root>/.agents/memory/` and `view_file` on each active `.md` file.
2. **Precedence & Strict Enforcement**:
   - **Actively enforce every rule**: Do not merely read directives; all subsequent reasoning, tool executions, and responses throughout the session must strictly comply with loaded rules and memory.
   - Project directives override default assumptions. If directives mandate a specific runtime (e.g., poetry), prioritize it in Step 1.

---

## STEP 1: RUNTIME DISCOVERY & LOCKING

1. **Lockfile Introspection** (`<root>` and 1-depth subdirs: `backend/`, `frontend/`, `server/`):
   - **Python**: `uv.lock` (`uv run`), `poetry.lock` (`poetry run`), `Pipfile.lock` (`pipenv run`), `.venv/` (`.venv/bin/python`), `environment.yml` (`conda run`), `pyproject.toml`.
   - **Node**: `pnpm-lock.yaml` (`pnpm`), `yarn.lock` (`yarn`), `bun.lockb` (`bun`), `package-lock.json` (`npm`).
   - **Polyglot**: `Cargo.toml` (`cargo`), `go.mod` (`go`), etc.
2. **User Confirmation**:
   - Prompt user via `ask_question` (markdown choices fallback if unavailable) with detected runtime as `(Recommended)`. Include `No execution environment needed` and write-in support.
3. **Fail-Fast Health Check**:
   - Run `<prefix> --version`. On failure, halt execution; prompt user for alternate runtime or binary path.
4. **Mandatory Prefix Enforcement**:
   - Language/runtime toolchain commands MUST use the locked prefix (e.g., `<prefix> pytest`, `<prefix> python`).
   - In polyglot/monorepo projects with multiple subsystems (e.g., backend vs. frontend), bind respective prefixes to their working directories (Cwd).
   - **Prohibited**: Bare/unmanaged runtime execution (e.g., naked `python`, `pytest`, `npm`). Standard OS/VCS tools (`git`, shell built-ins) remain unaffected.

---

## STEP 2: SUMMARY & HANDOFF

1. **Status Briefing**: Output 1–2 lines reporting loaded directives and `Locked execution prefix: '<prefix>'`.
2. **Handoff**:
   - Standalone: Prompt for task.
   - Caller skill (`my-new-session`): Return control with locked context.

---

## Usage Protocol for Calling Skills

```markdown
**Context Initialization Gate**: Invoke `my-begin` first to enforce directives and lock runtime execution prefix.
```
