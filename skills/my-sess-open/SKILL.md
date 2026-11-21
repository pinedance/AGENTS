---
name: my-sess-open
description: >
  Unified session initialization skill: loads directives and STATE.md (with lazy loading for coding guidelines), runs safety snapshot backup, locks runtime prefix, syncs Git state, configures Caveman mode, and applies Task Branch Guard. Trigger at session start, when starting a new task/branch, or on /my-sess-open.
---

# My Session Open

Mandatory session entry gate. Initialize context, safety snapshot, runtime lock, and Git state cleanly via SSoT and Fail-Fast principles.

## STEP 0: Silent Boot, Lazy Loading & Safety Snapshot

Run tool calls silently before any user-visible output.

1. **Directives & Project Rules/Memory**:
   - Skip re-reading `AGENTS.md` if already injected in host system prompt; otherwise read `<root>/.agents/AGENTS.md` or `<root>/AGENTS.md` (if present).
   - Read `<root>/.agents/AGENTS.local.md` and `<root>/README.md` (if present).
   - Read all `.md` files under `<root>/.agents/rules/` and `<root>/.agents/memory/` (following per-project symlinks, excluding `STATE.md`). Treat root `rules/`, `memory/`, and `~/.agents/{rules,memory}` strictly as shared storage — never auto-scan them unless symlinked into `<root>/.agents/`.
   - **Lazy-Load Coding Guidelines**: Defer reading [my-coding-guidelines](../my-coding-guidelines/SKILL.md) until entering code planning, implementation, or review.
2. **Session State (`STATE.md`)**:
   - Resolve `STATE.md` via `AGENTS.md` Shared Conventions precedence.
   - Load `Current Goal`, `Active Branch`, `Blockers`, and `Next Action`. If `STATE.md` references an active `.agents/plans/*/00-roadmap.md` with pending `[ ]` phases, read that `00-roadmap.md`.
3. **Voice Mode**: Activate Caveman Mode (`/caveman`) for all subsequent responses.
4. **Safety Snapshot**: Run `~/.agents/skills/my-sess-open/scripts/session-backup.sh "<root>"` (fallback `<root>/.agents/skills/my-sess-open/scripts/session-backup.sh "<root>"`) and record `~/.cache/agents/backups/<project>/latest`.

## STEP 1: Runtime Discovery & Locking (Fail-Fast)

1. Inspect `<root>` and 1-depth subdirs (`backend/`, `frontend/`, `server/`):
   - **Python (precedence tier)**: explicit lockfiles (`uv.lock`→`uv run`, `poetry.lock`→`poetry run`, `Pipfile.lock`→`pipenv run`) outrank `.venv/` (`.venv/bin/python`), `environment.yml` (`conda run`), and bare `pyproject.toml`.
   - **Node / Polyglot**: `pnpm-lock.yaml` (`pnpm`), `yarn.lock` (`yarn`), `bun.lockb` (`bun`), `package-lock.json` (`npm`), `Cargo.toml` (`cargo`), `go.mod` (`go`).
2. Lock a single highest-precedence runtime (or `None` if absent) silently. Prompt via `ask_question` only when conflicting lockfiles coexist at the same precedence tier (recommended candidate first).
3. If locked runtime is not `None`, verify executable availability (`<tool> --version`, e.g., `uv --version`, `.venv/bin/python --version`; `go version` for Go); halt and prompt on failure. Enforce `<prefix>` on all subsequent toolchain commands (no bare `python`, `pytest`, `npm`).

## STEP 2: Git Inspection & Remote Sync

1. If remote exists (`git remote`), run `git fetch --quiet`; inspect `git status --porcelain -b`.
2. **Dirty Tree (Committable Changes Only)**: Ignore ephemeral paths per `AGENTS.md` Shared Conventions exclusions. If clean, skip. Otherwise print `git status --short` and prompt via `ask_question`:
   - Question: `"작업 시작 전 커밋되지 않은 변경사항이 발견되었습니다. 어떻게 처리할까요?"`
   - Options: `(Recommended) Logical group commits first (my-git-commit)` | `Single commit first (my-git-commit Single-Unit Mode)` | `Stash changes (git stash)` | `Proceed with current uncommitted changes`
   - Execute the selected action before proceeding (for commit options, follow [my-git-commit](../my-git-commit/SKILL.md) in the corresponding mode without a second prompt).
3. **Remote Sync (Only If Out-of-Sync)**:
   - Up-to-date or no remote: skip.
   - Clean & strictly behind: run `git pull --ff-only` silently (prompt only on failure).
   - Dirty & behind: prompt `git pull` vs skip. Ahead: prompt `git push` vs skip. Diverged: prompt `git pull --rebase` / `git pull` / skip.
4. **Explicit Branch Only**: If the initial prompt specifies a target branch, switch/create it immediately; otherwise defer branch creation to Step 4.3.

## STEP 3: Status Briefing

Output a concise 2–4 line briefing:
- **Directives & State**: Loaded `.agents/{rules,memory}` docs + `STATE.md` summary (or `No STATE.md`)
- **Safety Snapshot**: `~/.cache/agents/backups/<project>/latest`
- **Locked Runtime**: `<prefix>`
- **Git State**: `<branch>` (sync status)

Enforce `AGENTS.md` Plan-Before-Edit and User-Gated Completion SSoT.

## STEP 4: Topic Alignment, Interview & Task Branch Handoff

1. **Stale `STATE.md` Check & Alignment**:
   - Resolve `<base-branch>` per `AGENTS.md` Shared Conventions. Silently treat `STATE.md` as stale if it has zero pending `[ ]` items AND its `Active Branch` no longer exists (`git show-ref --verify --quiet refs/heads/<branch>`) or is already merged into `<base-branch>` (`git branch --merged <base-branch>`).
   - Otherwise, if active unfinished `STATE.md` work differs from the user's topic, clarify via `ask_question` (resume vs pivot).
   - On resume: checkout `Active Branch` (if different, existing, and tree-compatible) + apply Step 2.3 sync; if an active `00-roadmap.md` has pending `[ ]` phases, enter `AGENTS.md` Tier 2 directly.
2. **Interview & Planning Handoff**:
   - Skip interview for purely read-only Q&A or read-only audit workflows (e.g., `my-prompt-audit` Mode 1).
   - For change tasks: inspect minimal context, clarify gaps 1 question at a time (`ask_question` preferred) scoped to entry tier (`Roadmap` vs `Single-Phase`), then hand off to `AGENTS.md` Execution Flow.
3. **Task Branch Setup**:
   - Apply `AGENTS.md` Shared Conventions Task Branch Guard unless an explicit branch was switched in Step 2.4 (branch from `HEAD` if uncommitted changes were retained in Step 2.2).
