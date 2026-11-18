---
name: my-sess-open
description: >
  Unified session initialization skill: loads and strictly enforces project directives
  (AGENTS.md, rules, memory) and session state snapshot (STATE.md), runs safety snapshot backup,
  locks runtime execution prefix (uv, poetry, pnpm, etc.), inspects and syncs Git repository state
  (uncommitted changes, fetch/pull/push, branch setup), and configures session settings (caveman).
  Trigger this skill at session start, when starting a new task or branch, or when the user invokes /my-sess-open.
---

# My Session Open — Workspace Initialization, Directives, Runtime & Git Setup

This skill is the mandatory entry gate for every session. It initializes directives and state context, protects untracked files, locks the runtime prefix, synchronizes Git state, and configures session settings.

---

## STEP 0: DIRECTIVES, STATE INGESTION & SAFETY SNAPSHOT (SILENT)

**Execute tool calls silently. DO NOT output text until Step 0 is completed.**

1. **Read Project Directives & Memory**:
   - Read `<root>/.agents/AGENTS.md` or `<root>/AGENTS.md` (skip if absent).
   - Read `<root>/.agents/AGENTS.local.md` (skip if absent).
   - Read `<root>/README.md` (skip if absent) to comprehend project scope and technical details.
   - List `<root>/.agents/rules/` (or `<root>/rules/`) and read each active `.md` rule file.
   - List `<root>/.agents/memory/` (or `<root>/memory/`) and read each active `.md` file (excluding `STATE.md`, which is loaded in Step 0.2).
2. **Read Session State Snapshot (`STATE.md`)**:
   - Check in order of precedence: `<root>/.agents/memory/STATE.md` → `<root>/memory/STATE.md` → `<root>/STATE.md`.
   - If present, load `Current Goal`, `Active Branch`, `Blockers`, and `Next Action` to restore loop continuity.
   - If `STATE.md` references an active `.agents/docs/user/*-macro-plan.md` with pending `[ ]` phases, read that macro-plan file as well to restore Phase roadmap continuity.
3. **Strict Enforcement & Communication Mode**:
   - Actively enforce every loaded rule, memory, and coding guideline ([my-coding-guidelines](../my-coding-guidelines/SKILL.md)) throughout the session.
   - Activate Caveman Mode (`/caveman full`) immediately for all subsequent responses.
4. **Run Safety Snapshot Backup**:
   - Execute `<root>/skills/my-sess-open/scripts/session-backup.sh` (or via `.agents/skills/my-sess-open/scripts/session-backup.sh`).
   - Record the returned snapshot path (`~/.cache/agents/backups/<project>/latest`) for the final briefing.

---

## STEP 1: RUNTIME DISCOVERY & LOCKING

1. **Lockfile Introspection** (`<root>` and 1-depth subdirs: `backend/`, `frontend/`, `server/`):
   - **Python**: `uv.lock` (`uv run`), `poetry.lock` (`poetry run`), `Pipfile.lock` (`pipenv run`), `.venv/` (`.venv/bin/python`), `environment.yml` (`conda run`), `pyproject.toml`.
   - **Node**: `pnpm-lock.yaml` (`pnpm`), `yarn.lock` (`yarn`), `bun.lockb` (`bun`), `package-lock.json` (`npm`).
   - **Polyglot**: `Cargo.toml` (`cargo`), `go.mod` (`go`), etc.
2. **Auto-Lock vs. User Confirmation**:
   - If a single runtime lockfile is unambiguously detected (or explicitly specified in the user prompt), lock it silently without asking.
   - If no lockfile is found, lock `None` (no runtime prefix needed) silently without asking.
   - Prompt via `ask_question` ONLY when multiple conflicting lockfiles exist in the same scope, offering the primary candidate as `(Recommended)`.
3. **Fail-Fast Health Check & Prefix Enforcement**:
   - Verify tool availability (`<prefix> --version` or base binary `--version`). On failure, halt and prompt user.
   - All subsequent toolchain commands MUST use the locked prefix (e.g., `uv run pytest`). Bare runtime execution (`python`, `pytest`, `npm`) is prohibited.

---

## STEP 2: GIT STATE INSPECTION, REMOTE SYNC & BRANCH SETUP

1. **Inspect Git State & Fetch Remote**:
   - Check if a remote exists (`git remote`). If present, run `git fetch --quiet` to update remote tracking refs.
   - Run `git status --porcelain -b` to inspect:
     - Current branch and upstream tracking status (`ahead N`, `behind M`)
     - Modified, staged, or untracked files

2. **Handle Uncommitted Changes (Only If Dirty)**:
   - Check dirty state excluding ephemeral `.agents/docs/` and `.agents/scratch/` artifacts (per `my-git-commit` SSoT). If the working tree has no committable changes, proceed silently to Step 2.3.
   - If uncommitted modifications exist, output a brief `git status --short` summary first, then prompt via `ask_question`:
     - **Question**: "작업 시작 전 커밋되지 않은 변경사항이 발견되었습니다. 어떻게 처리할까요?"
     - **Options**:
       - `(Recommended) Logical group commits first (my-git-commit)`
       - `Single commit first (my-git-commit Single-Unit Mode)`
       - `Stash changes (git stash)`
       - `Proceed with current uncommitted changes`
   - Execute the selected action before proceeding (for Option 1 or Option 2, read and follow [my-git-commit](../my-git-commit/SKILL.md) in `Autonomous Logical-Split Mode` or `Single-Unit Mode` respectively, without a second confirmation prompt).

3. **Handle Remote Synchronization (`pull` / `push`, Only If Out-of-Sync)**:
   - **If up-to-date (`ahead 0, behind 0`) or no remote exists**: Proceed silently to Step 2.4.
   - **If working tree is clean and local is strictly behind remote (`ahead 0, behind M`)**: Automatically run `git pull --ff-only` silently (prompt via `ask_question` only if `--ff-only` fails).
   - **If local is behind remote with a dirty tree**: Prompt via `ask_question` with `(Recommended) Pull remote changes to local (git pull)` vs `Skip sync and proceed`.
   - **If local is ahead of remote**: Prompt via `ask_question` with `(Recommended) Push local changes to remote (git push)` vs `Skip sync and proceed`.
   - **If diverged (ahead and behind)**: Prompt via `ask_question` to `Pull with rebase (git pull --rebase)`, `Merge pull (git pull)`, or `Skip sync`.

4. **Branch Setup (Explicit / Resume / Auto-Branch Default)**:
   - **Explicit branch in prompt**: If the user specified a target branch name in their initial prompt, create/switch to it immediately (`git checkout -b <branch-name>` or `git checkout <branch-name>`).
   - **Resuming `STATE.md` branch**: If resuming unfinished work from `STATE.md` and current branch differs from `STATE.md`'s `Active Branch`, verify `Active Branch` still exists locally or on remote; if it exists and the working tree is clean/compatible, switch to it automatically (`git checkout <Active Branch>`) without prompting. If already merged/deleted, stay on the current branch silently.
   - **New session task on `main`/`master` (Auto-Branch Default)**: Do NOT ask user approval for branch creation or branch name. Once the task involves file, plan, or code modifications (immediately if clear from initial prompt, or at Step 4.3 right after User Interview before persisting `macro-plan.md` or modifying files), automatically create and switch to an AI-named task branch (`git checkout -b <prefix>/<slug>`, e.g., `feat/...`, `fix/...`, `refactor/...`). Keep the current branch silently for purely read-only Q&A sessions.

---

## STEP 3: STATUS BRIEFING & SAFETY GATE

1. **Output Status Briefing** (concise 2–4 lines so the user has full workspace context on the first turn):
   - **Directives & State**: Loaded rules/memories + `STATE.md` summary (`Current Goal` & `Next Action`, or `No STATE.md`)
   - **Safety Snapshot**: `~/.cache/agents/backups/<project>/latest`
   - **Locked Runtime**: `<prefix>`
   - **Git State**: `<branch>` (sync status: clean / pulled / pushed)
2. **Execution Safety Gate**:
   - Follow `AGENTS.md`'s Two-Tier Execution Flow: require Tier 1 Macro Plan approval for multi-phase tasks and explicit active-Phase Detailed Plan approval before modifying codebase files.

---

## STEP 4: TOPIC ALIGNMENT & USER INTERVIEW HANDOFF

1. **Topic vs. `STATE.md` & Macro Plan Check**:
   - Compare the user's stated session topic/goal against `STATE.md`'s `Current Goal` and `Next Action`. If `STATE.md` has unfinished work that differs from the new topic, clarify whether to resume the existing goal or pivot to the new topic.
   - When resuming an active `.agents/docs/user/*-macro-plan.md` with pending `[ ]` phases, skip Macro Plan regeneration and hand off directly to the next pending Phase's JIT Detailed Plan.
2. **Mandatory User Interview & Planning Handoff**:
   - Do NOT jump directly to a Detailed Plan or code edits. Inspect only the minimum files needed to understand the stated topic, then initiate a 1-question-at-a-time User Interview (preferring `ask_question`) to concretize scope, requirements, and constraints.
   - Once requirements are concrete, classify scope per `AGENTS.md`:
     - **Multi-phase task (2+ phases)**: Propose a **Macro Plan** (Phase boundaries, objectives, and deliverables only; strictly defer per-phase detailed plans), obtain explicit user approval, enforce `Step 4.3` Auto-Branch Check if still on `main`/`master`, persist `.agents/docs/user/YYYY-MM-DD-<topic>-macro-plan.md`, and enter Phase 1 JIT Detailed Planning.
     - **Single-phase task**: Enforce `Step 4.3` Auto-Branch Check (if modifying files on `main`/`master`) and proceed directly to the Detailed Plan.
3. **Auto-Branch Check (If Still on `main`/`master`)**:
   - Once the task requires repository/plan files or codebase modifications and the workspace is still on `main` or `master`, automatically create and switch to an AI-named task branch (`git checkout -b <prefix>/<slug>`) without asking user approval before persisting `macro-plan.md` or modifying any files.
