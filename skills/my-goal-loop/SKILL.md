---
name: my-goal-loop
description: >
  Domain-agnostic autonomous iterative convergence controller executing a repeating Work, Independent Audit, and Keep/Revert Ratchet cycle governed by an upfront Frozen Goal Contract. Make sure to trigger this skill whenever the user asks to iterate, refine, refactor, optimize, or reconcile targets repeatedly until a condition, quality/logic rubric, SSoT consistency rule, test/build gate, or quantitative benchmark/metric target is satisfied — including Korean and English requests such as "특정 목표/조건 달성까지 반복", "작업 후 감사/검증 루프", "수렴할 때까지 수정/개선", "조건 만족할 때까지 루프", "audit loop", "iterate until goal/condition/metric is met", or "/my-goal-loop", even when they do not explicitly mention "goal loop". Do NOT use for one-shot static reviews, single-pass interactive task edits, or linear forward execution of sequential plans.
---

# My Goal Loop

Autonomously drive iterative `Work -> Independent Audit -> Keep/Revert Ratchet` cycles until an explicit convergence contract is satisfied or a safety circuit breaker halts execution.

## 1. Overview & Role Boundaries (SoC)

- **Zero Domain Overfitting**: Never hardcode domain modes, preset audit profiles, or hidden rubrics. Code refactoring, skill/workflow SSoT alignment, quantitative benchmark optimization, and document refinement all execute through the exact same state machine parameterized solely by the session's `Frozen Goal Contract`.
- **Single-File & Host-Agnostic Portability (YAGNI)**: Keep execution self-contained in this prompt protocol with zero auxiliary scripts, hooks, plugins, or background daemons. Use an isolated read-only subagent for qualitative audits when the host supports subagents; fall back seamlessly to structured inline verification tables when it does not.
- **User Language Alignment**: Write internal contracts and reasoning consistently, while conducting all user-facing interviews, contract approvals, and exit reports in the user's language.
- **Separation of Concerns (SoC)**:
  - `AGENTS.md` Two-Tier Flow: Governs linear Phase planning, execution, and completion commits; `my-goal-loop` focuses strictly on autonomous trial-and-audit convergence and ratchet rollback across rounds.
  - `my-coding-guidelines` / `my-prompt-audit`: Provide evaluation standards an `Audit Oracle` may reference when iterative code or prompt cleanup is requested.

## 2. Entry Gate — JIT Interview & Frozen Goal Contract

Lock falsifiable pass/fail criteria before touching any file so neither evaluation standards nor scope drift under mid-loop rationalization.

### Dynamic Interview Rules

1. **Extract First**: Parse any explicit goals, target files, guards, metrics, or rubrics already provided in the user request; never re-ask settled items.
2. **One Question at a Time**: If any mandatory slot is missing or ambiguous, interview the user one question at a time (`ask_question` preferred; free-form answers accepted).
3. **Zero Invented Criteria**: Never guess or fabricate the `Audit Oracle`. Derive deterministic commands, qualitative rubrics, or hybrid criteria explicitly with the user.

### 5 Mandatory Contract Slots

1. **Goal**: Specific, falsifiable end state (e.g., zero blocking findings, zero contradictions, or threshold metric achieved).
2. **Mutable Scope**: Exact files/directories allowed to change and whether creating new files inside that scope is allowed. Treat all out-of-scope files as strictly read-only.
3. **Invariants / Safety Guards**: Existing functionality, rules, symlinks, schemas, or regression commands that must remain intact throughout every round.
4. **Audit Oracle**: Objective judge run every round — deterministic command(s) (exit codes, parsed metrics), user-approved AI qualitative rubric with mandatory direct evidence, or a hybrid of both.
5. **Keep / Revert Rule & Bounds**: Minimum verifiable net improvement over `last-good` required for `KEEP` versus `REVERT`, plus `max_iterations` (default `5`) and `stall_limit` (default `2`), adjustable per contract.

### Standard Template 1 — Frozen Goal Contract Block

```markdown
- Goal: <falsifiable convergence condition(s)>
- Mutable Scope: <allowed paths and whether new file creation in scope is permitted>
- Invariants / Safety Guards: <non-negotiable preserved behaviors/links and guard commands>
- Audit Oracle: <deterministic commands and/or AI qualitative rubric + direct evidence rule>
- Keep/Revert Rule: <minimum verifiable net progress threshold over last-good>
- Bounds: max_iterations=5, stall_limit=2
```

### Single Upfront Approval Gate

Present the finalized `Frozen Goal Contract` in `.agents/AGENTS.md` Detailed Plan format for **one explicit user approval** prior to Round 1. Once approved, iterate autonomously without per-round confirmation until convergence or a circuit-breaker halt.

## 3. Universal 6-Step Loop Engine

### Step 0 — Baseline & Scratch Init

1. Run frozen `Invariants / Safety Guards` and `Audit Oracle` against the initial untouched state to establish `Baseline`.
2. If both `Goal` and `Safety Guards` already pass cleanly, modify zero files and exit immediately with `ALREADY_SATISFIED`.
3. **Task Branch Guard**: Before creating scratch state or modifying any file in Round 1, ensure an active task branch per [my-sess-open](../my-sess-open/SKILL.md) Step 4.3 SSoT (never mutate `Mutable Scope` on `<base-branch>` or an unrelated branch unless explicitly requested).
4. Otherwise allocate `<run-id>` (e.g., `YYYYMMDD_HHMMSS-<slug>`) under `.agents/scratch/goal-loop/<run-id>/`: copy pre-existing `Mutable Scope` files into `last-good/` preserving relative paths, record all pre-existing relative paths in `manifest.txt`, and initialize `ledger.md`.

### Step 1 — Atomic Work

1. Read `ledger.md` first (prior hypotheses, `REVERT` causes, remaining `Finding ID`s) so failed attempts are never repeated verbatim.
2. Execute one minimal atomic modification (single hypothesis or tightly coupled edit bundle) strictly inside `Mutable Scope` whose causal impact can be cleanly judged in one audit pass.
3. If achieving the goal appears to require out-of-scope edits, destructive actions, or resolving conflicting requirements, make no unauthorized edits and trigger `Scope / Ambiguity Halt` immediately.

### Step 2 — Independent Audit

1. **Deterministic Fail-Fast First**: Execute all `Safety Guards` and deterministic `Audit Oracle` commands first. If any `Safety Guard` fails, classify the round as `REVERT` immediately without spending tokens on qualitative AI review.
2. **Two-Tier AI Qualitative Audit Isolation** (when `Audit Oracle` includes qualitative judgment):
   - **Primary Path (Subagent-Capable Host — Read-Only `Fresh-Context Auditor`)**: Dispatch a fresh read-only subagent to eliminate self-grading confirmation bias. Strip the worker's reasoning trace, intent claims, and self-justifications; supply only the verbatim `Frozen Goal Contract`, `Mutable Scope` file paths plus diff against `last-good/`, and raw guard/command outputs.
   - **Fallback Path (Host Without Subagents)**: Run audit inline, strictly banning unsupported assertions ("vibe checks"). Produce a 1:1 structured verification table mapping every `Goal` criterion and `Invariant` to exact `file:line` citations and verbatim command outputs before scoring.

#### Standard Template 2 — Fresh-Context Auditor Prompt & Output Schema

```markdown
Role: Independent read-only auditor. Do not edit files. Judge strictly from provided artifacts.
Inputs:
1. Verbatim Frozen Goal Contract
2. Diff against last-good/ and Mutable Scope file paths (worker rationale omitted)
3. Latest raw Safety Guard and deterministic Audit Oracle command outputs

Required Output:
- Overall Verdict: PASS | FAIL
- Invariants Status: INTACT | VIOLATED (cite exact evidence if VIOLATED)
- Findings Table: | Finding ID | Criterion / Invariant | Severity | Direct Evidence (file:line or command output) | Concrete Gap |
```

### Step 3 — Keep / Revert Ratchet

1. **Decision `KEEP`**: Every `Safety Guard` passes AND `Audit Oracle` confirms verifiable net progress over `last-good` toward `Goal` (improved target metric, fewer blocking findings/contradictions, or strictly narrower gap). Sync `last-good/` to match the accepted working-tree state.
2. **Decision `REVERT`**: Triggered on any `Safety Guard` failure, invariant violation, metric regression, zero-progress tie, command crash, or increased defects. Immediately restore files from `last-good/` and prune unpromoted round files per Section 4.
3. **Ledger Append**: Record one row per round in `.agents/scratch/goal-loop/<run-id>/ledger.md` using Standard Template 3.

#### Standard Template 3 — `ledger.md` Schema

```markdown
# Goal Loop Ledger — <run-id>
- Status: RUNNING | ALREADY_SATISFIED | CONVERGED | HALTED (<trigger>)
- Baseline: <initial metric / finding summary>
- Final / Current Best: <latest last-good metric / finding summary>

| Round | Hypothesis / Change Summary | Audit & Guard Result | Decision (KEEP/REVERT) | Key Evidence & Next Note |
|---|---|---|---|---|
```

### Step 4 — Convergence & Closing Verify

1. Immediately after a `KEEP` round appears to satisfy every `Goal` criterion, run **Closing Verify**: re-execute the complete frozen `Invariants / Safety Guards` and `Audit Oracle` verbatim with zero skipped checks.
2. If `Closing Verify` passes, mark `ledger.md` as `CONVERGED` and terminate immediately — perform zero post-convergence polish edits or scope creep.
3. If `Closing Verify` surfaces a missed guard or condition failure, reclassify the round/state accordingly (restore `last-good/` if regression occurred) and continue to `Step 5`.

### Step 5 — Circuit Breaker Check

If not yet converged, evaluate Section 4 circuit breakers. When none have tripped, increment the round counter and return to `Step 1`.

## 4. Non-Destructive Rollback & 3-Way Circuit Breakers

### Zero-Commit Snapshot Rollback

- Follow `.agents/AGENTS.md`: **never run `git commit` mid-loop** and **never execute destructive Git commands** (`git reset --hard`, `git checkout -f`, `git clean -f`).
- On `REVERT`: overwrite modified `Mutable Scope` files using their exact copies in `.agents/scratch/goal-loop/<run-id>/last-good/`. Compare `Mutable Scope` against `last-good/` and `manifest.txt`, and remove only newly created in-scope files that were never promoted to `last-good/`. Never touch pre-existing out-of-scope files, git state, or symlinks.

### 3-Way Circuit Breakers (`HALTED`)

Halt execution immediately and transition to `HALTED` when any of the following conditions hold:

1. **Budget Exhausted**: Completed rounds reach `max_iterations` (default `5`).
2. **Stall / Oscillation**: `stall_limit` (default `2`) consecutive `REVERT` rounds, consecutive rounds with zero net metric/finding improvement, or alternating `Finding ID`s where fixing A repeatedly reintroduces B.
3. **Scope / Ambiguity Halt**: Further progress requires editing outside `Mutable Scope`, performing destructive actions, or resolving contradictory contract requirements/invariants.

### Pre-Exit Working Tree Check

Before delivering any `CONVERGED` or `HALTED` report, verify that every `Mutable Scope` file in the working tree matches `.agents/scratch/goal-loop/<run-id>/last-good/` cleanly with zero failed-round residue left behind.

## 5. Governance & Exit Gate

### Mandatory Exit Report

Upon exiting with `ALREADY_SATISFIED`, `CONVERGED`, or `HALTED`, report all three sections to the user:

1. **Exit Status & Reason**: Final status (`ALREADY_SATISFIED`, `CONVERGED`, or `HALTED` plus exact circuit-breaker trigger).
2. **Baseline -> Final Summary**: Delta from `Baseline` to final `last-good` metrics/findings and the exact list of retained modified/created files.
3. **Verification Evidence**: Direct command outputs and `file:line` citations observed during `Closing Verify` (or final audit), plus a summary of `.agents/scratch/goal-loop/<run-id>/ledger.md`.

### User Completion Declaration Gate

- Passing `Closing Verify` (`CONVERGED`) is **verification evidence, not task completion**. Never execute `git commit` until the user inspects the evidence and explicitly declares completion; preserve `.agents/scratch/goal-loop/<run-id>/` intact during user review. Once the user declares completion, follow `AGENTS.md` Completion & Phase Boundary Gate SSoT for commits and Phase transitions.
- When exiting via `HALTED`, leave the verified `last-good` state intact and ask the user whether to: (1) adjust the contract or `Mutable Scope` and resume, (2) raise `max_iterations` and resume, or (3) accept/discard the current `last-good` changes.
