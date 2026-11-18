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
   - If `STATE.md` references an active `.agents/plans/*/macro.md` with pending `[ ]` phases, read that `macro.md` file as well to restore Phase roadmap continuity.
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
   - Skip Step 1.3 if locked runtime is `None`.
   - Otherwise verify tool availability (`<prefix> --version` or base binary `--version`). On failure, halt and prompt user.
   - All subsequent toolchain commands MUST use the locked prefix (e.g., `uv run pytest`). Bare runtime execution (`python`, `pytest`, `npm`) is prohibited.

---

## STEP 2: GIT STATE INSPECTION, REMOTE SYNC & BRANCH SETUP

1. **Inspect Git State & Fetch Remote**:
   - Check if a remote exists (`git remote`). If present, run `git fetch --quiet` to update remote tracking refs.
   - Run `git status --porcelain -b` to inspect:
     - Current branch and upstream tracking status (`ahead N`, `behind M`)
     - Modified, staged, or untracked files

2. **Handle Uncommitted Changes (Only If Dirty)**:
   - Check dirty state excluding ephemeral `.agents/plans/`, `.agents/docs/`, and `.agents/scratch/` artifacts (per `my-git-commit` SSoT). If the working tree has no committable changes, proceed silently to Step 2.3.
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

4. **Pre-Interview Branch Check (Explicit Branch Only)**:
   - **Explicit branch in prompt**: If the user specified a target branch name in their initial prompt, create/switch to it immediately (`git checkout -b <branch-name>` or `git checkout <branch-name>`).
   - **Otherwise (Defer to Step 4)**: Keep the current branch through Step 3 Briefing so topic vs. `STATE.md` alignment (Step 4.1) is evaluated before switching or creating branches.

---

## STEP 3: STATUS BRIEFING & SAFETY GATE

1. **Output Status Briefing** (concise 2–4 lines so the user has full workspace context on the first turn):
   - **Directives & State**: Loaded rules/memories + `STATE.md` summary (`Current Goal` & `Next Action`, or `No STATE.md`)
   - **Safety Snapshot**: `~/.cache/agents/backups/<project>/latest`
   - **Locked Runtime**: `<prefix>`
   - **Git State**: `<branch>` (sync status: clean / pulled / pushed)
2. **Execution Safety Gate**:
   - Enforce `AGENTS.md` SSoT: follow Two-Tier Planning approvals before codebase edits and wait for User Completion Declaration before committing.

---

## STEP 4: TOPIC ALIGNMENT, INTERVIEW & TASK BRANCH HANDOFF

1. **Topic vs. `STATE.md` & Macro Plan Alignment**:
   - Compare the user's stated session topic/goal against `STATE.md`'s `Current Goal` and `Next Action`. If `STATE.md` has unfinished work that differs from the new topic, clarify via `ask_question` whether to resume the existing goal or pivot to the new topic.
   - **If resuming `STATE.md` work**: When current branch differs from `STATE.md`'s `Active Branch` and `Active Branch` still exists locally or on remote (with a clean/compatible tree), switch to it automatically (`git checkout <Active Branch>`) and apply `Step 2.3` remote sync check; if an active `.agents/plans/*/macro.md` has pending `[ ]` phases, hand off directly to the next pending Phase's JIT User Interview & Detailed Plan per `AGENTS.md` Tier 2.
2. **Mandatory User Interview & Planning Handoff**:
   - Do NOT jump directly to a Detailed Plan or code edits. Inspect only the minimum files needed to understand the stated topic, then initiate a 1-question-at-a-time User Interview (preferring `ask_question`) scoped strictly to entry classification:
     - **Multi-phase task (2+ phases)**: Concretize ONLY overall goals, global constraints, and Phase boundaries (`Macro User Interview`), deferring Phase-specific detail questions to each Phase's Tier 2 JIT User Interview.
     - **Single-phase task**: Concretize task requirements directly before proposing the Detailed Plan.
   - Once concrete, apply `Step 4.3` Task Branch Setup (when changes are needed) and hand off directly to `AGENTS.md`'s Two-Tier Execution Flow (`Single-Phase Fast Path` vs. `Tier 1 Macro Plan`).
3. **Task Branch Setup (SSoT)**:
   - For a new session task requiring repository, plan, or codebase modifications (when no explicit branch was given in Step 2.4): do NOT ask user approval for branch creation or branch name. Whether currently on `<base-branch>` (`main`/`master`) or lingering on a prior unrelated branch, automatically create and switch to a new AI-named branch off `<base-branch>` (`git checkout -b <prefix>/<slug> <base-branch>`, or from `HEAD` if uncommitted changes were intentionally retained in Step 2.2) before persisting `macro.md` or modifying any files. Keep the current branch silently for purely read-only Q&A sessions.
