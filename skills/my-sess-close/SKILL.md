---
name: my-sess-close
description: >
    Finalizes an AI agent coding session: inspects Git and session state, confirms closing decisions interactively, persists STATE.md, README.md, and promoted knowledge in a single pass, and dispatches Git/branch wrap-up actions. Trigger whenever closing a session, wrapping up a task, handing off work, or on /my-sess-close.
---

# My Session Close

End every session with a verified point-in-time `STATE.md` snapshot, synced `README.md`, promoted long-term knowledge, and clean Git/branch state.

## STEP 1: Read-Only Inspection & Briefing

1. **Inspect Git & Context**:
    - Run `git status --porcelain -b` and `git diff --stat`. Resolve `<branch>` (or detached HEAD), `<base-branch>` and committable exclusions (per `AGENTS.md` Shared Conventions), and unpushed commit state (`ahead > 0`, or commits ahead of `<base-branch>` when `git rev-parse --abbrev-ref @{u}` fails).
    - Detect worktree layout (`GIT_DIR` vs `GIT_COMMON` resolved via `git rev-parse`): equal → normal repo; unequal under `.worktrees/` or `worktrees/` → agent-owned worktree (removable on merge/discard); unequal elsewhere → external/harness worktree (preserve directory).
    - Locate `STATE.md` via `AGENTS.md` Shared Conventions precedence (default `<root>/.agents/memory/STATE.md`) and check `git check-ignore -q <state-path>`.
    - Check active `.agents/plans/*/00-roadmap.md` for pending `[ ]` phases, `<root>/README.md` for doc drift, and reusable invariants/patterns warranting promotion to `.agents/memory/` or `.agents/rules/`.
    - Set `has_committable_changes = true` if committable dirty files exist, `README.md` updates, a tracked knowledge file will be written, or `STATE.md` is not gitignored; else `false`.
2. **Pre-Close Briefing (2–3 lines)**: `Working Tree` (changes + `STATE.md`/`README.md` scope), `Knowledge Candidates` (`<filename>.md` or `None`), `Branch Status` (`<branch>` + sync/unpushed state).

## STEP 2: Interactive Closing Decisions

Ask applicable questions 1 at a time via `ask_question` (numbered plain-text fallback). Working-tree commits run automatically in Step 3.5 unless the user explicitly requested stash or leaving changes uncommitted.

1. **Knowledge Promotion (only if candidates exist)**:
    - Prompt `"이번 세션에서 발견한 핵심 규칙/패턴을 영구 Memory 또는 Rule 파일로 분리 저장할까요?"` with `(Recommended) Save to .agents/memory/ or .agents/rules/ (<proposed-filename>.md)` vs `Skip promotion (record in STATE.md only)`. Set `has_committable_changes = true` if an approved file is tracked.
2. **Branch & Remote Strategy** (present only options valid for current state):
    - **On `<base-branch>`**: If remote exists and ahead (or `has_committable_changes` on default path), prompt `(Recommended) Keep <base-branch> local as-is` vs `Push <base-branch> to remote (git push)`; else skip.
    - **On detached HEAD**: Prompt `(Recommended) Keep detached HEAD as-is` | `Push HEAD as new branch & create Pull Request` | `Discard detached work`.
    - **On non-base branch**:
        - If user explicitly requested `Stash` or `Leave uncommitted`: `(Recommended) Keep current branch as-is (work in progress)` | `Push committed history to remote (git push)` _(if remote + unpushed)_ | `Discard current branch (<branch>)`.
        - Default (clean or auto-committing): Prompt `"현재 브랜치(<branch>)의 후속 형상 관리를 어떻게 진행할까요?"` with `(Recommended) Merge into base branch (<base-branch>) locally and clean up branch` | `Keep current branch as-is (work in progress)` | `Push current branch to remote (git push)` | `Push & create Pull Request` | `Discard current branch (<branch>)`.

## STEP 3: Verified Execution & Single-Pass Persistence

Invoking `/my-sess-close` authorizes updating `STATE.md`, `README.md`, and confirmed `.agents/{memory,rules}/` files after Step 2. Execute in causal order so `STATE.md` reflects verified post-action state.

1. **Discard Path (only if `Discard` selected)**:
    - Skip committing on `<branch>`. Print permanent deletion summary (`<branch>`/detached, commits/files/owned worktree lost) and require 2-step typed confirmation: `'discard'` then `'yes'` (abort back to Step 2.2 on decline).
    - Clean up by layout (omit `git branch -D <branch>` if detached): normal (`git checkout -f <base-branch>`, `git clean -fd`, `git branch -D <branch>`), owned worktree (`cd "$MAIN_ROOT"`, `git worktree remove --force "$WORKTREE_PATH"`, `git worktree prune`, `git branch -D <branch>`), external worktree (`git checkout -f --detach <base-branch>`, `git clean -fd`, `git branch -D <branch>`).
    - On `<base-branch>`, write approved knowledge + `STATE.md` (`Active Branch: <base-branch>`), auto-commit if tracked (unless left uncommitted), and jump to Step 4.
2. **Pre-Merge / Pre-PR Test Gate (Fail-Fast; only if `Merge locally` or `Push & create PR`)**:
    - Run the project test suite using the session's locked runtime `<prefix>`.
    - On failure: abort merge/PR, stay on `<branch>`, persist `README.md`/knowledge/`STATE.md` (recording failing tests in `Blockers`), run default auto-commit, and jump to Step 4.
3. **Stash First (only if explicitly requested)**:
    - Run `git stash push -u -m "wip: <summary>" -- . ':!<state-path>' ':!.agents/memory/*' ':!.agents/rules/*' ':!memory/*' ':!rules/*'`.
4. **Single-Pass Persistence (`.agents/{memory,rules}/`, `README.md`, `STATE.md`)**:
    - Write approved `.agents/memory/` or `.agents/rules/` file and drifted `README.md`.
    - Overwrite `STATE.md` as a concise point-in-time snapshot (no history accumulation; defer writing until Step 3.5 only when `Merge locally` runs in an owned worktree and `STATE.md` is gitignored so it persists in `$MAIN_ROOT`):
        - `Merge locally` (tests passed): `Active Branch: <base-branch>`, `Next Action: None (task completed)` (or next planned task).
        - `Stash` / `Keep` / `Push` / `PR`: `Active Branch: <branch>` + immediate next step (note WIP stash if stashed; record `00-roadmap.md` path and next pending `Phase k` if mid-roadmap).
    - Schema:

        ```markdown
        # Session State

        - **Updated**: YYYY-MM-DD HH:MM
        - **Active Branch**: `<branch-name>`

        ## Current Goal

        - <1–2 sentences>

        ## Progress & Checklist

        - [x] <Completed item>
        - [ ] <Remaining item>

        ## Key Decisions & Blockers

        - **Decisions**: <Settled architectural/design choices>
        - **Blockers / Open Issues**: <Unresolved issues or "None">

        ## Next Action

        - <Immediate first step for next session>
        ```

5. **Dispatch Working Tree & Branch Actions**:
    - **Working Tree**: On default path with `has_committable_changes = true`, run `Auto Multi-Commit` per `AGENTS.md` SSoT (load [my-git-commit](../my-git-commit/SKILL.md) only when context is insufficient).
    - **Branch & Remote**:
        - `Keep`/skipped: no-op.
        - `Push`: `git push` (`-u origin <branch>` if no upstream).
        - `Push & create PR`: push (`git push origin HEAD:refs/heads/<new-branch>` if detached) and open PR; preserve worktree.
        - `Merge locally`: `cd "$MAIN_ROOT"` if worktree → `git checkout <base-branch>` → `git pull` (if remote) → `git merge <branch>` → re-verify test suite with `<prefix>` (halt before cleanup on conflict/failure and update `STATE.md` with `Blockers`) → remove owned worktree (`git worktree remove` + `prune`) → `git branch -d <branch>` → persist deferred gitignored `STATE.md` in `$MAIN_ROOT`.

## STEP 4: Closing Summary

Output 2–3 concise lines: `Updated State & Docs`, `Git Status`, and `Next Session Entry`.
