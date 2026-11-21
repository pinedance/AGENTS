# Project

## Governance & Workflow

* **Session Initialization Gate (SSoT):** If `my-sess-open` is active in the workspace, run it as the first action; initialization and runtime lock follow `my-sess-open` SSoT (task branch rules follow `Shared Conventions` Task Branch Guard). *(Fallback when absent: read local `.agents/AGENTS.local.md`, `.agents/rules/*.md`, `.agents/memory/*.md`, and `README.md`.)*
* **Plan-Before-Edit Gate:** Never invoke file edit/write tools on codebase files (or dump full replacement code/diffs in chat) without explicit approval of the active Detailed Plan. Selecting a high-level option or approving a Tier 1 Roadmap authorizes direction and persisting `.agents/plans/*/00-roadmap.md` only — not codebase edits. *(Purely cosmetic one-liners like typos may skip plan overhead and verify directly.)*
* **User-Gated Completion:** Passing verification is evidence, not completion. Never commit or close a Phase/task until the user inspects verification output and declares completion.
* **Execution Flow (Two-Tier Lazy JIT):**
  * **Single-Phase Fast Path** (localized single unit): `Inspect & Interview (if unclear) → Detailed Plan → Explicit Approval → Persist <topic>.md → Execute & Verify → Report Evidence & Wait → Auto Multi-Commit`.
  * **Multi-Phase Workflow** (2+ stages/subsystems — **lazy JIT delegation** to prevent upfront over-planning and context waste as early phases evolve):
    1. **Tier 1 — Roadmap (Coordinator):** Define only overall objective, global constraints, Phase boundaries, dependencies, and verifiable deliverables (`- [ ] Phase k`). Defer all phase-internal interviews and file/line plans to Tier 2. On approval, persist metadata (`Branch`, `Base Branch`, `Locked Runtime`) and checklist to `.agents/plans/YYYY-MM-DD-<topic>/00-roadmap.md`, then enter Phase 1.
    2. **Tier 2 — Phase `k` Loop (Implementer):** Read `00-roadmap.md` (restoring metadata directly after `/compact` without re-running `my-sess-open`) → JIT inspect & interview Phase `k` if unclear → Detailed Plan → Explicit Approval → Persist `XX-<slug>.md` → Execute & Verify → Report Evidence & Wait.
    3. **Phase Boundary Gate (on user completion declaration):** Run `Auto Multi-Commit` and check `[x] Phase k` in `00-roadmap.md`. Intermediate Phase (`k < N`): report commit SHA(s), recommend `/compact`, and wait (or advance directly if instructed). Final Phase (`k == N`): skip `/compact`, report completion and SHA(s), and guide to `/my-sess-close` (or delegate directly if `/my-sess-close` was invoked).
  * **Detailed Plan Contract** (active Phase/task only): (1) exact target file paths and ranges, (2) concise core changes (no full code blocks, prose drafts, or full diffs), (3) concrete verification commands. On approval, persist the approved Detailed Plan to `.agents/plans/YYYY-MM-DD-<topic>/XX-<slug>.md` (Multi-Phase, 2-digit zero-padded lowercase ASCII kebab-case in the `00-roadmap.md` directory; match existing phases via `XX-*.md`) or `.agents/plans/YYYY-MM-DD-<topic>.md` (Single-Phase, with `Branch`, `Base Branch`, `Locked Runtime` metadata).
  * **Auto Multi-Commit:** On user completion declaration (or `/my-sess-close`), partition cohesive changes directly without a commit prompt using Conventional Commits (`feat|fix|refactor|docs|test|chore|ci|style`; multi-purpose files by primary intent; title `< 50` chars matching repo language; bullet body for multiple changes; `Shared Conventions` exclusions) and verify with `git log --oneline -5`; load `my-git-commit` only when context is insufficient (post-`/compact`, pre-existing dirty files, external edits).

## Core Principles

* **No Speculation:** Clarify missing scope or requirements 1 question at a time with context and clear options (`ask_question` preferred) instead of assuming.
* **Evidence Integrity:** Back every assertion about paths, file state, CLI behavior, or completion with direct command output.
* **Objective Stance:** Stay analytical; push back on unnecessary complexity, surface tradeoffs, and avoid performative agreement.
* **Minimal Surgical Scope (YAGNI):** Touch only what the task requires and remove only orphans created by your changes. Lazy-load `my-coding-guidelines` when planning, writing, or reviewing code.
* **Safety & Invariants (Fail-Fast):** Require explicit approval before destructive operations (`-f`, `--force`, `rm -rf`, `git clean`, hard resets, permanent deletion). Reference `~/.cache/agents/backups/<project>/latest` before irreversible actions. Preserve workspace symlinks (`.agents/*`) without flattening.

## Shared Conventions & Paths (SSoT)

* **Workspace Paths & Commit Exclusions:** Plans `.agents/plans/` (`YYYY-MM-DD-<topic>.md` for Single-Phase; `YYYY-MM-DD-<topic>/{00-roadmap.md, XX-<slug>.md}` for Multi-Phase), User Deliverables `.agents/docs/user/`, Scratch `.agents/scratch/`. Exclude ephemeral paths (`.agents/plans/`, `.agents/docs/`, `.agents/scratch/`) from Git commits unless explicitly requested; persistent markdown (`README.md`, `SKILL.md`, `STATE.md`, `rules/*.md`, `memory/*.md`) remains committable.
* **Session State (`STATE.md`) Precedence:** `<root>/.agents/memory/STATE.md` → `<root>/STATE.md`.
* **Base Branch Resolution:** `git show-ref --verify --quiet refs/heads/main && echo main || (git show-ref --verify --quiet refs/heads/master && echo master)`.
* **Task Branch Guard:** Before the first repo, plan, or code write (unless an explicit branch was requested), if on `<base-branch>` or an unrelated prior branch, auto-create `git checkout -b <type>/<slug> <base-branch>` (or from `HEAD` if uncommitted changes are retained) without asking approval; preserve a matching active task branch and keep the current branch on read-only runs.
