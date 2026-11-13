---
name: my-sess-close
description: >
  Finalizes an AI agent coding session: updates the project state snapshot (STATE.md),
  synchronizes README.md with the latest project state, evaluates permanent memory/rule promotion,
  inspects local and remote Git repository state, and proposes/executes closing Git actions
  (commit, stash, push, merge, or branch completion).
  Trigger this skill whenever closing a session, wrapping up a task, handing off work, or when the user runs /my-sess-close.
---

# My Session Close — State Handoff, README Sync, Knowledge Promotion & Git Wrap-up

This skill ensures every session ends cleanly with an up-to-date state snapshot for loop continuity, a synchronized `README.md`, promoted long-term knowledge, and a clean Git repository state.

---

## STEP 1: AI STATE SNAPSHOT (`STATE.md`) & `README.md` UPDATE

1. **Locate Target `STATE.md`**:
   - Search in order of precedence:
     1. `<root>/.agents/memory/STATE.md`
     2. `<root>/memory/STATE.md`
     3. `<root>/STATE.md`
   - If an existing file is found, update it in place.
   - If none exists, create `<root>/.agents/memory/STATE.md`.

2. **Overwrite `STATE.md` with Current Snapshot (No History Accumulation)**:
   - Invoking `/my-sess-close` directly authorizes updating `STATE.md` and `README.md` without a separate plan approval gate.
   - Keep `STATE.md` strictly as a concise, current-point-in-time snapshot so the next session's `my-sess-open` loads minimal tokens with zero stale noise (historical logs belong in `git log`).
   - Record the current branch as `Active Branch: <branch-name>` (if the branch is later merged and deleted in Step 3.3, Step 3.3 updates `Active Branch` to `<base-branch>`).
   - Use the following structure:
     ```markdown
     # Session State

     - **Updated**: YYYY-MM-DD HH:MM
     - **Active Branch**: `<branch-name>`

     ## Current Goal
     - <1–2 sentences describing the active objective>

     ## Progress & Checklist
     - [x] <Completed item in this/recent session>
     - [ ] <Remaining item>

     ## Key Decisions & Blockers
     - **Decisions**: <Core architectural/design choices settled>
     - **Blockers / Open Issues**: <Unresolved problems, failing tests, or "None">

     ## Next Action
     - <Immediate first step for the next session>
     ```

3. **Synchronize `README.md` with Latest Project State**:
   - Inspect `<root>/README.md` (if present) against the changes made during the session (new features, skills/modules added or renamed, CLI/API changes, configuration updates, or architectural changes).
   - If any part of `README.md` is outdated or missing coverage of the session's changes, update `<root>/README.md` immediately so project documentation stays in lockstep with the codebase and `STATE.md`.

---

## STEP 2: PERMANENT KNOWLEDGE PROMOTION (MEMORY & RULES)

1. **Evaluate Session Learnings**:
   - Review whether the session uncovered recurring bug patterns, project-wide architectural invariants, or domain rules that must persist permanently beyond the current task.
2. **Confirm Promotion (Only When Applicable)**:
   - If no permanent rule/memory candidates exist, skip silently to Step 3.
   - If candidates exist, prompt the user via `ask_question`:
     - **Question**: "이번 세션에서 발견한 핵심 규칙/패턴을 영구 Memory 또는 Rule 파일로 분리 저장할까요?"
     - **Options**:
       - `(Recommended) Save to memory/ or rules/ (<proposed-filename>.md)`
       - `Skip promotion (keep only in STATE.md)`
   - When approved, write or update the target file in `<root>/.agents/memory/` (or `<root>/memory/`) or `<root>/.agents/rules/` (or `<root>/rules/`).

---

## STEP 3: GIT REPOSITORY STATE & CLOSING ACTIONS

1. **Inspect Git State**:
   - Run `git status --porcelain -b` and `git diff --stat` to inspect modified/untracked files (including `STATE.md`), current branch, and ahead/behind status against remote.

2. **Handle Uncommitted Changes**:
   - If uncommitted or untracked changes exist, ask the user via `ask_question`:
     - **Question**: "커밋되지 않은 변경사항이 있습니다. 어떻게 처리할까요?"
     - **Options**:
       - `(Recommended) Invoke my-git-commit skill (logical group commits)`
       - `Commit directly using current session context`
       - `Stash changes (git stash)`
       - `Leave uncommitted as-is`
   - Execute the selected action:
     - **Option 1**: Follow the [my-git-commit](../my-git-commit/SKILL.md) workflow.
     - **Option 2**: Stage relevant files (`git add`) and commit with a Conventional Commit message summarizing the session work.
     - **Option 3 (`Stash changes`)**: Stash only code/workspace changes while keeping `STATE.md` and promoted `memory/` or `rules/` files intact in the working tree (`git stash push -u -m "wip: <branch/task summary>" -- . ':!<path-to-STATE.md>' ':!.agents/memory/*' ':!.agents/rules/*' ':!memory/*' ':!rules/*'`), and note in `STATE.md` (`Next Action`) that WIP code is stored in `git stash`.

3. **Handle Branch & Remote Sync**:
   - After resolving working tree changes, inspect branch integration and remote sync needs (`git branch --show-current`, `git status -sb`).
   - If the working tree still has uncommitted changes (`Leave uncommitted as-is` or un-committed `STATE.md` after stash), do not offer branch-switching/merge actions that would conflict; only offer `Keep current branch as-is` or `Push current branch to remote`.
   - Ask the user via `ask_question`:
     - **Question**: "현재 브랜치(`<branch>`)의 후속 형상 관리를 어떻게 진행할까요?"
     - **Options**:
       - `(Recommended) Keep current branch as-is (work in progress)`
       - `Push current branch to remote (git push)`
       - `Merge into base branch (main/master) locally and clean up branch`
       - `Create PR / Worktree cleanup / Discard branch (invoke finishing-a-development-branch)`
   - Execute the selected action:
     - **Keep as-is**: Do nothing further.
     - **Push**: Run `git push` (or `git push -u origin <branch>` if no upstream is set).
     - **Merge locally**: Update `STATE.md`'s `Active Branch` to `<base-branch>` (`main`/`master`) and `Next Action` to `None (task completed)` and commit; then checkout `<base-branch>`, pull latest if remote exists, merge `<branch>`, verify tests using the locked runtime `<prefix>` (e.g., `uv run pytest`), and delete `<branch>` (`git branch -d <branch>`).
     - **Invoke skill**: Follow [finishing-a-development-branch](../finishing-a-development-branch/SKILL.md) (skipping its redundant uncommitted-changes check and using the locked `<prefix>` for test verification; if merged or discarded, ensure `STATE.md` reflects `<base-branch>`).

---

## STEP 4: CLOSING SUMMARY

Output a concise 2–3 line closing briefing:
- `Updated State & Docs`: `<path to STATE.md>`, `README.md` (`updated` or `up-to-date`), and any promoted `memory/` or `rules/` files
- `Git Status`: `<current branch>`, `<last commit / stash / push / merge result>`
- `Next Session Entry`: `<1-line Next Action recorded in STATE.md>`
