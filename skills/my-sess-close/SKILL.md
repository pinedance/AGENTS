---
name: my-sess-close
description: >
  Finalizes an AI agent coding session: inspects session and Git state, confirms closing
  decisions interactively, synchronizes STATE.md, README.md, and promoted knowledge in a
  single pass, and orchestrates the selected Git/branch wrap-up actions.
  Trigger this skill whenever closing a session, wrapping up a task, handing off work, or when the user runs /my-sess-close.
---

# My Session Close — State Handoff, README Sync, Knowledge Promotion & Git Wrap-up

This skill ensures every session ends cleanly with an up-to-date state snapshot for loop continuity, a synchronized `README.md`, promoted long-term knowledge, and a clean Git repository state.

---

## STEP 1: READ-ONLY INSPECTION & PRE-CLOSE BRIEFING

1. **Inspect Git & Session Context**:
   - Run `git status --porcelain -b` and `git diff --stat` to identify `<branch>` (or detached HEAD), `<base-branch>` (`git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null`), modified/untracked files (ignoring ephemeral `.agents/docs/` and `.agents/scratch/` artifacts per `my-git-commit`), and whether unpushed local commits exist (`ahead > 0` on tracked upstream, or local commits ahead of `<base-branch>` when `git rev-parse --abbrev-ref @{u}` confirms no upstream is configured).
   - Detect workspace layout via `GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)` and `GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)`:
     - `GIT_DIR == GIT_COMMON`: normal repository.
     - `GIT_DIR != GIT_COMMON` under `.worktrees/` or `worktrees/`: agent-owned worktree (eligible for cleanup on merge/discard).
     - `GIT_DIR != GIT_COMMON` elsewhere: harness-owned external worktree (preserve directory; never remove it).
   - Locate target `STATE.md` in precedence order: `<root>/.agents/memory/STATE.md` → `<root>/memory/STATE.md` → `<root>/STATE.md` (defaulting to `<root>/.agents/memory/STATE.md` when absent), and check via `git check-ignore -q <state-path>` whether `STATE.md` is gitignored or Git-committable.
   - Check `<root>/README.md` (if present) for documentation drift against session changes, and evaluate whether reusable architectural invariants or recurring bug patterns warrant promotion to `<root>/.agents/memory/` (`memory/`) or `<root>/.agents/rules/` (`rules/`).
   - Compute **`has_committable_changes`**: `true` if committable working tree changes already exist, `README.md` requires an update, a non-gitignored knowledge file will be written, or target `STATE.md` is not gitignored; otherwise `false`.

2. **Output Pre-Close Briefing**:
   - Output a concise 2–3 line status snapshot:
     - `Working Tree`: changed/untracked files + upcoming `STATE.md`/`README.md` sync scope
     - `Knowledge Candidates`: `<proposed-filename>.md` or `None`
     - `Branch Status`: `<branch>` and ahead/behind or unpushed commit state

---

## STEP 2: INTERACTIVE CLOSING DECISIONS

Ask applicable closing questions one at a time via `ask_question` and wait for each response before proceeding (falling back to numbered plain-text options if `ask_question` is unavailable):

1. **Permanent Knowledge Promotion (Only If Candidates Exist)**:
   - Skip silently to Step 2.2 when no candidates exist.
   - Otherwise prompt via `ask_question`:
     - **Question**: "이번 세션에서 발견한 핵심 규칙/패턴을 영구 Memory 또는 Rule 파일로 분리 저장할까요?"
     - **Options**:
       - `(Recommended) Save to memory/ or rules/ (<proposed-filename>.md)`
       - `Skip promotion (record session context in STATE.md only)`
   - Update `has_committable_changes` to `true` if an approved target path is not gitignored.

2. **Working Tree Wrap-Up Strategy (Only If `has_committable_changes` Is True)**:
   - If `has_committable_changes` is `false` (clean tree and only gitignored `STATE.md` will be updated), skip silently to Step 2.3.
   - Otherwise prompt via `ask_question`:
     - **Question**: "세션 변경사항(상태·문서 갱신 포함)을 어떻게 정리할까요?"
     - **Options**:
       - `(Recommended) Logical group commits (my-git-commit)`
       - `Single session commit (my-git-commit Single-Unit Mode)`
       - `Stash code changes (git stash; keep STATE.md & knowledge files)` *(offer when uncommitted code/workspace changes exist)*
       - `Leave uncommitted in working tree`

3. **Branch & Remote Wrap-Up Strategy**:
   - Present only atomic options compatible with `<branch>` and Step 2.2 outcome:
     - **Dirty working tree (`Stash` or `Leave uncommitted` chosen in Step 2.2)**:
       - On a non-base branch (`<branch> != <base-branch>`): prompt via `ask_question` with `(Recommended) Keep current branch as-is (work in progress)`, `Push committed history to remote (git push)` *(include if a remote exists and unpushed commits exist)*, and `Discard current branch (<branch>)`.
       - On `<base-branch>`: if a remote exists and unpushed commits exist, prompt via `ask_question` with `(Recommended) Keep <base-branch> local as-is` vs `Push committed history to remote (git push)`; otherwise skip Step 2.3.
     - **Clean or committing working tree (Step 2.2 skipped or selected a commit option)**:
       - On `<base-branch>`: if a remote exists and local commits are/will be ahead of remote (unpushed commits exist or Step 2.2 selected a commit option), prompt via `ask_question` with `(Recommended) Keep <base-branch> local as-is` vs `Push <base-branch> to remote (git push)`; otherwise skip Step 2.3.
       - On a **detached HEAD**: omit local merge (no named branch to merge) and prompt via `ask_question` with `(Recommended) Keep detached HEAD as-is`, `Push HEAD as new branch & create Pull Request`, and `Discard detached work`.
       - On a non-base feature/task branch: prompt via `ask_question`:
         - **Question**: "현재 브랜치(`<branch>`)의 후속 형상 관리를 어떻게 진행할까요?"
         - **Options**:
           - `(Recommended) Keep current branch as-is (work in progress)`
           - `Push current branch to remote (git push)`
           - `Merge into base branch (<base-branch>) locally and clean up branch`
           - `Push & create Pull Request`
           - `Discard current branch (<branch>)`

---

## STEP 3: VERIFIED EXECUTION & SINGLE-PASS STATE PERSISTENCE

Invoking `/my-sess-close` authorizes updating `STATE.md`, `README.md`, and confirmed `memory/`/`rules/` files once Step 2 choices are confirmed. Execute in causal order so `STATE.md` is written once with verified post-action state:

1. **Branch Discard Path (Only If `Discard` Selected in Step 2.3)**:
   - Skip committing on `<branch>`. Display the permanent deletion summary (`Branch <branch>` or `detached HEAD`, commits to lose, uncommitted/untracked workspace files, and owned worktree path if applicable) and require two-step explicit confirmation: typed `'discard'` first, then `'yes'` (`(yes/no)`). If declined, abort discard and return to Step 2.3.
   - Once confirmed, switch off `<branch>` and clean up according to workspace layout (Step 1.1):
     - **Normal repo (`GIT_DIR == GIT_COMMON`)**: `git checkout -f <base-branch>`, `git clean -fd`, and (if named branch) `git branch -D <branch>`.
     - **Owned worktree (`.worktrees/` or `worktrees/`)**: capture `WORKTREE_PATH=$(git rev-parse --show-toplevel)` and `MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)`, then `cd "$MAIN_ROOT"`, `git worktree remove --force "$WORKTREE_PATH"`, `git worktree prune`, and (if named branch) `git branch -D <branch>`.
     - **External / harness worktree**: `git checkout -f --detach <base-branch>`, `git clean -fd`, and (if named branch) `git branch -D <branch>`.
   - On `<base-branch>`, write any approved knowledge file (Step 2.1) and overwrite `STATE.md` (`Active Branch: <base-branch>`, `Next Action` set to next objective or `None`). If Step 2.2 selected a commit option and written state/knowledge files on `<base-branch>` are non-gitignored, commit them via [my-git-commit](../my-git-commit/SKILL.md) (`Single-Unit Mode`). Proceed directly to Step 4.

2. **Pre-Merge / Pre-PR Test Gate (Only If `Merge locally` or `Push & create Pull Request` Selected in Step 2.3)**:
   - Run the project test suite using the session's locked runtime `<prefix>` from `my-sess-open` before writing `Active Branch: <base-branch>` or integrating/pushing.
   - **If tests fail**: Abort the merge/PR and stay on `<branch>`; write `README.md`/knowledge (if applicable) and overwrite `STATE.md` with `Active Branch: <branch>` and `Blockers` recording the failing tests (`merge/PR deferred`), execute Step 2.2's working tree choice on `<branch>`, and jump to Step 4.

3. **Stash Code First (Only If `Stash` Selected in Step 2.2)**:
   - Run `git stash push -u -m "wip: <branch/task summary>" -- . ':!<path-to-STATE.md>' ':!.agents/memory/*' ':!.agents/rules/*' ':!memory/*' ':!rules/*'` before writing state/knowledge files so `STATE.md` and promoted files remain intact in the working tree.

4. **Persist Promoted Knowledge, `README.md` & `STATE.md` Once**:
   - Write or update the approved `memory/` or `rules/` file (Step 2.1) and `<root>/README.md` (if Step 1 identified drift).
   - Overwrite `STATE.md` as a concise current-point-in-time snapshot (no history accumulation; historical logs belong in `git log`):
     - `Merge locally` (pre-merge tests passed): `Active Branch: <base-branch>`, `Next Action: None (task completed)` (or next planned task).
     - `Stash`: `Active Branch: <branch>`, noting in `Next Action` that WIP code is stored in `git stash`.
     - `Keep` / `Push` / `Push & create Pull Request`: `Active Branch: <branch>` and immediate next step.
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

5. **Dispatch Working Tree & Branch Actions**:
   - **Working Tree (from Step 2.2)**:
     - `Logical group commits` or `Single session commit`: Read and follow [my-git-commit](../my-git-commit/SKILL.md) in `Interactive Logical-Split Mode` or `Single-Unit Mode` respectively.
     - `Stash` / `Leave uncommitted` / skipped: Working tree already matches target state.
   - **Branch & Remote (from Step 2.3)**:
     - `Keep as-is` / skipped: No further Git action (preserve any worktree).
     - `Push`: Run `git push` (or `git push -u origin <branch>` if no upstream is set; preserve any worktree).
     - `Merge locally`:
       - If in a worktree (`GIT_DIR != GIT_COMMON`), capture `WORKTREE_PATH=$(git rev-parse --show-toplevel)` and `cd` to `MAIN_ROOT=$(git -C "$(git rev-parse --git-common-dir)/.." rev-parse --show-toplevel)` first.
       - Run `git checkout <base-branch>`, `git pull` (if a remote exists), and `git merge <branch>`.
       - Re-verify the project test suite on the merged `<base-branch>` result using the locked runtime `<prefix>`. If merge conflicts or post-merge tests fail, halt before removing any worktree or branch and report the failure.
       - Once verified: if `WORKTREE_PATH` is an owned worktree (`.worktrees/` or `worktrees/`), run `git worktree remove "$WORKTREE_PATH"` and `git worktree prune`; then delete `<branch>` (`git branch -d <branch>`).
     - `Push & create Pull Request`:
       - Run `git push -u origin <branch>` (or `git push origin HEAD:refs/heads/<new-branch>` on detached HEAD) and create the Pull Request, preserving any worktree for PR feedback iteration.

---

## STEP 4: CLOSING SUMMARY

Output a concise 2–3 line closing briefing:
- `Updated State & Docs`: `<path to STATE.md>`, `README.md` (`updated` or `up-to-date`), and any promoted `memory/` or `rules/` files
- `Git Status`: `<active branch>`, `<commit / stash / push / merge / PR / discard result>`
- `Next Session Entry`: `<1-line Next Action recorded in STATE.md>`
