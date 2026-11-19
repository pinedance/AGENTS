# Project

## Governance & Workflow

* **Session Initialization Gate (SSoT):** If `my-sess-open` is active in the workspace, run it as the first action; initialization, runtime lock, and task branch setup follow `my-sess-open` SSoT. *(Fallback when absent: read local `AGENTS.local.md`, `rules/*.md`, `memory/*.md`, and `README.md`.)*
* **Plan-Before-Edit Gate:** Never invoke file edit/write tools on codebase files (or dump full replacement code/diffs in chat) without explicit approval of the active Detailed Plan. Selecting a high-level option or approving a Tier 1 Macro Plan authorizes direction and persisting `.agents/plans/*/macro.md` only — not codebase edits. *(Purely cosmetic one-liners like typos may skip plan overhead and verify directly.)*
* **User-Gated Completion:** Passing verification is evidence, not completion. Never commit or close a Phase/task until the user inspects verification output and declares completion.
* **Execution Flow (Two-Tier Lazy JIT):**
  * **Single-Phase Fast Path** (localized single unit): `Inspect & Interview (if unclear) → Detailed Plan → Explicit Approval → Execute & Verify → Report Evidence & Wait → Auto Multi-Commit`.
  * **Multi-Phase Workflow** (2+ stages/subsystems — **lazy JIT delegation** to prevent upfront over-planning and context waste as early phases evolve):
    1. **Tier 1 — Macro Plan (Coordinator):** Define only overall objective, global constraints, Phase boundaries, dependencies, and verifiable deliverables (`- [ ] Phase k`). Defer all phase-internal interviews and file/line plans to Tier 2. On approval, persist metadata (`Branch`, `Base Branch`, `Locked Runtime`) and checklist to `.agents/plans/YYYY-MM-DD-<topic>/macro.md`, then enter Phase 1.
    2. **Tier 2 — Phase `k` Loop (Implementer):** Read `macro.md` (restoring metadata directly after `/compact` without re-running `my-sess-open`) → JIT inspect & interview Phase `k` if unclear → Detailed Plan → Explicit Approval → Execute & Verify → Report Evidence & Wait.
    3. **Phase Boundary Gate (on user completion declaration):** Run `Auto Multi-Commit` and check `[x] Phase k` in `macro.md`. Intermediate Phase (`k < N`): report commit SHA(s), recommend `/compact`, and wait (or advance directly if instructed). Final Phase (`k == N`): skip `/compact`, report completion and SHA(s), and guide to `/my-sess-close` (or delegate directly if `/my-sess-close` was invoked).
  * **Detailed Plan Contract** (active Phase/task only): (1) exact target file paths and ranges, (2) concise core changes (no full code blocks, prose drafts, or full diffs), (3) concrete verification commands.
  * **Auto Multi-Commit:** On user completion declaration (or `/my-sess-close`), split changes into logical Conventional Commits directly from active context per `my-git-commit` SSoT without a separate commit prompt; load `my-git-commit` only when context is insufficient (post-`/compact`, pre-existing dirty files, external edits).

## Core Principles

* **No Speculation:** Clarify missing scope or requirements 1 question at a time with context and clear options (`ask_question` preferred) instead of assuming.
* **Evidence Integrity:** Back every assertion about paths, file state, CLI behavior, or completion with direct command output.
* **Objective Stance:** Stay analytical; push back on unnecessary complexity, surface tradeoffs, and avoid performative agreement.
* **Minimal Surgical Scope (YAGNI):** Touch only what the task requires and remove only orphans created by your changes. Lazy-load `my-coding-guidelines` when planning, writing, or reviewing code.
* **Safety & Invariants (Fail-Fast):** Require explicit approval before destructive operations (`-f`, `--force`, `rm -rf`, `git clean`, hard resets, permanent deletion). Reference `~/.cache/agents/backups/<project>/latest` before irreversible actions. Preserve workspace symlinks (`AGENTS.md`, `skills`) without flattening.

## Workspace Paths (SSoT)

* **Plans:** `.agents/plans/YYYY-MM-DD-<topic>/` (`macro.md`, optional `phase-XX.md` / `plan.md`)
* **User Deliverables:** `.agents/docs/user/` (standalone user-facing docs outside task plans)
* **Scratch:** `.agents/scratch/` (temporary scripts and debug files)
