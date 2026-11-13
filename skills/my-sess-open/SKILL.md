---
name: my-sess-open
description: >
  Unified session initialization skill: loads and strictly enforces project directives
  (AGENTS.md, rules, memory) and session state snapshot (STATE.md), runs safety snapshot backup,
  locks runtime execution prefix (uv, poetry, pnpm, etc.), inspects and syncs Git repository state
  (uncommitted changes, fetch/pull/push, branch setup), and configures session settings (caveman, model selection).
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
   - Only prompt via `ask_question` when ambiguous (multiple conflicting lockfiles or no lockfile found), offering the primary candidate as `(Recommended)` and `No execution environment needed`.
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
   - If the working tree is clean, proceed silently to Step 2.3.
   - If uncommitted modifications exist, prompt the user via `ask_question`:
     - **Question**: "작업 시작 전 커밋되지 않은 변경사항이 발견되었습니다. 어떻게 처리할까요?"
     - **Options**:
       - `(Recommended) Commit changes first (invoke my-git-commit or direct commit)`
       - `Stash changes (git stash)`
       - `Proceed without committing`
   - Execute the chosen action before proceeding.

3. **Handle Remote Synchronization (`pull` / `push`, Only If Out-of-Sync)**:
   - **If up-to-date (`ahead 0, behind 0`) or no remote exists**: Proceed silently to Step 2.4.
   - **If local is behind remote**: Prompt via `ask_question` with `(Recommended) Pull remote changes to local (git pull)` vs `Skip sync and proceed`.
   - **If local is ahead of remote**: Prompt via `ask_question` with `(Recommended) Push local changes to remote (git push)` vs `Skip sync and proceed`.
   - **If diverged (ahead and behind)**: Prompt via `ask_question` to `Pull with rebase (git pull --rebase)`, `Merge pull (git pull)`, or `Skip sync`.

4. **Branch Setup (Explicit / Resume vs. Deferred to Post-Interview)**:
   - **Explicit branch in prompt**: If the user specified a target branch name in their initial prompt, create/switch to it immediately (`git checkout -b <branch-name>` or `git checkout <branch-name>`).
   - **Resuming `STATE.md` branch**: If resuming unfinished work from `STATE.md` and current branch differs from `STATE.md`'s `Active Branch`, confirm via `ask_question` whether to switch to `Active Branch`.
   - **Topic-only on `main`/`master` (Defer branch creation)**: Do NOT prompt to create a new branch before the User Interview. Keep the current branch and defer new branch creation until the User Interview confirms that file/code changes are needed.

---

## STEP 3: STATUS BRIEFING & MODEL SELECTION

1. **Output Status Briefing** (concise 2–4 lines, output before model check so the user has full workspace context on the first turn):
   - **Directives & State**: Loaded rules/memories + `STATE.md` summary (`Current Goal` & `Next Action`, or `No STATE.md`)
   - **Safety Snapshot**: `~/.cache/agents/backups/<project>/latest`
   - **Locked Runtime**: `<prefix>`
   - **Git State**: `<branch>` (sync status: clean / pulled / pushed)
2. **Model Selection Gate**:
   - Unless the user explicitly stated their model preference in the initial prompt (e.g., "모델 그대로"), invoke the [my-models](../my-models/SKILL.md) skill protocol to ask whether they want to switch models via `/model`, and wait for the user's response before proceeding to Step 4.
3. **Execution Safety Gate**:
   - Do not modify codebase files without presenting a Detailed Plan and receiving explicit user approval, in accordance with `AGENTS.md`.

---

## STEP 4: TOPIC ALIGNMENT & USER INTERVIEW HANDOFF

1. **Topic vs. `STATE.md` Check**:
   - Compare the user's stated session topic/goal against `STATE.md`'s `Current Goal` and `Next Action`. If `STATE.md` has unfinished work that differs from the new topic, clarify whether to resume the existing goal or pivot to the new topic.
2. **Mandatory User Interview Gate (Context Concretization)**:
   - Do NOT jump directly to a Detailed Plan or code edits. Inspect only the minimum files needed to understand the stated topic, then initiate a 1-question-at-a-time User Interview (preferring `ask_question`) to concretize scope, requirements, and constraints before proposing a Detailed Plan.
3. **Post-Interview Branch Gate (If on `main`/`master`)**:
   - Once the User Interview confirms the task requires file/code modifications and the workspace is still on `main` or `master`, prompt via `ask_question` (`(Recommended) Create and switch to '<task-name>' branch` vs `Keep working on current branch`) before modifying any files.
