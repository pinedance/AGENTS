---
name: my-goal-loop
description: >
  Domain-agnostic autonomous iterative convergence controller executing a repeating Work, Independent Audit, and Keep/Revert Ratchet cycle governed by an upfront Frozen Goal Contract. Make sure to trigger on /my-goal-loop or any Korean/English request to repeatedly iterate, audit, refine, refactor, or optimize until a falsifiable condition, rubric, SSoT invariant, test gate, or metric target converges (even without saying "goal loop"). Do NOT use for one-shot static reviews, single-pass interactive edits, or linear execution of sequential plans.
---

# My Goal Loop

Autonomously drive `Work → Independent Audit → Keep/Revert Ratchet` cycles until an explicit convergence contract holds or a circuit breaker halts execution.

## 1. Design Principles & SoC

- **Zero Domain Overfitting & Single-File Portability (YAGNI)**: Execute any target (code refactor, prompt alignment, benchmark optimization, docs) through this self-contained state machine parameterized solely by `Frozen Goal Contract`, with zero auxiliary scripts, hooks, or background daemons.
- **Host-Agnostic Audit Isolation**: Dispatch a read-only `Fresh-Context Auditor` subagent when the host supports subagents; fall back to inline structured verification tables (`file:line` + verbatim outputs) when it does not.
- **User Language Alignment**: Keep contracts consistent while conducting interviews, approvals, and exit reports in the user's language.
- **Separation of Concerns (SoC)**: `AGENTS.md` Two-Tier Flow governs linear Phase planning and commits; `my-goal-loop` governs autonomous convergence and snapshot rollback; `my-coding-guidelines` / `my-prompt-audit` supply criteria an `Audit Oracle` may reference.

## 2. Entry Gate — JIT Interview & Frozen Goal Contract

Lock falsifiable pass/fail criteria before touching files to prevent scope creep or shifting evaluation standards mid-loop.

- **Interview & Zero Invented Criteria**: Extract explicit criteria from the user request first, clarify missing contract slots per `AGENTS.md` No Speculation, and derive every `Audit Oracle` check/rubric explicitly with the user rather than inventing pass conditions.
- **Single Upfront Approval Gate**: Finalize all 5 mandatory contract slots below and present the `Frozen Goal Contract` in `AGENTS.md` Detailed Plan format for **one explicit user approval** prior to Round 1; once approved, iterate autonomously until convergence or halt.

```markdown
# 5 Mandatory Contract Slots (Standard Template 1 — Frozen Goal Contract)
- Goal: <specific falsifiable end state (0 blocking findings, 0 contradictions, or metric target)>
- Mutable Scope: <exact modifiable paths + whether new files inside scope are permitted; external paths read-only>
- Invariants / Safety Guards: <preserved behaviors/symlinks/schemas + deterministic guard commands>
- Audit Oracle: <deterministic commands, user-approved AI qualitative rubric with direct evidence, or hybrid>
- Keep/Revert Rule: <minimum verifiable net improvement over last-good required for KEEP vs REVERT>
- Bounds: max_iterations=5, stall_limit=2
```

## 3. Convergence Loop Engine

### Step 0 — Baseline, Task Branch & Scratch Init

1. Run frozen `Invariants / Safety Guards` and `Audit Oracle` against the untouched initial state; if `Goal` and `Safety Guards` already pass cleanly, modify zero files and exit immediately with `ALREADY_SATISFIED`.
2. **Task Branch Guard**: Before creating scratch state or mutating Round 1, ensure an active task branch per `AGENTS.md` Shared Conventions Task Branch Guard.
3. Allocate `<run-id>` (`YYYYMMDD_HHMMSS-<slug>`) under `.agents/scratch/goal-loop/<run-id>/`: snapshot pre-existing `Mutable Scope` files into `last-good/` preserving relative paths, record them in `manifest.txt`, and initialize `ledger.md`.

### Step 1 — Atomic Work

1. Read `ledger.md` first (prior hypotheses, `REVERT` causes, remaining `Finding ID`s) so failed approaches are not repeated verbatim.
2. Apply one minimal atomic change (single hypothesis or tightly coupled bundle) strictly inside `Mutable Scope`. If progress requires out-of-scope edits, destructive operations, or resolving conflicting requirements, halt immediately via `Scope / Ambiguity Halt`.

### Step 2 — Independent Audit

1. **Deterministic Fail-Fast First**: Run all `Safety Guards` and deterministic `Audit Oracle` commands first; any `Safety Guard` failure triggers immediate `REVERT` before qualitative AI audit.
2. **Two-Tier Qualitative Audit Isolation** (when `Audit Oracle` includes qualitative scoring):
   - *Subagent Host (Primary)*: Invoke a fresh read-only subagent with worker rationale and intent claims stripped, supplying only the inputs in Template 2 to prevent confirmation bias.
   - *No-Subagent Host (Fallback)*: Audit inline with zero unsupported claims, mapping every `Goal` criterion and `Invariant` 1:1 to exact `file:line` citations and verbatim command outputs.

```markdown
# Standard Template 2 — Fresh-Context Auditor Prompt & Output
Role: Independent read-only auditor. Judge strictly from provided artifacts without editing files.
Inputs: (1) Verbatim Frozen Goal Contract, (2) Diff against last-good/ + Mutable Scope paths, (3) Latest raw Safety Guard / deterministic Audit Oracle outputs.
Required Output:
- Overall Verdict: PASS | FAIL
- Invariants Status: INTACT | VIOLATED (cite exact evidence if VIOLATED)
- Findings Table: | Finding ID | Criterion / Invariant | Severity | Direct Evidence (file:line or command output) | Concrete Gap |
```

### Step 3 — Keep / Revert Ratchet & Ledger

1. **Decision `KEEP`**: Every `Safety Guard` passes AND `Audit Oracle` proves verifiable net progress over `last-good`; sync `last-good/` to the working tree.
2. **Decision `REVERT`**: Triggered on any `Safety Guard` failure, invariant violation, metric regression, zero-progress tie, crash, or new defect; restore `Mutable Scope` from `last-good/` and prune unpromoted creations per Section 4.
3. Append one row to `.agents/scratch/goal-loop/<run-id>/ledger.md`:

```markdown
# Standard Template 3 — Goal Loop Ledger (<run-id>)
- Status: RUNNING | ALREADY_SATISFIED | CONVERGED | HALTED (<trigger>)
- Baseline: <initial metric / finding summary>
- Final / Current Best: <latest last-good metric / finding summary>

| Round | Hypothesis / Change Summary | Audit & Guard Result | Decision (KEEP/REVERT) | Key Evidence & Next Note |
|---|---|---|---|---|
```

### Step 4 — Closing Verify & Circuit-Breaker Advance

1. When a `KEEP` round satisfies every `Goal` criterion, run **Closing Verify**: re-execute the complete frozen `Invariants / Safety Guards` and `Audit Oracle` verbatim with zero skipped checks. On pass, mark `ledger.md` as `CONVERGED` and stop immediately without post-convergence edits; on failure, reclassify (restoring `last-good/` if needed) before checking circuit breakers.
2. Otherwise evaluate Section 4 circuit breakers; if untripped, increment the round counter and return to `Step 1`.

## 4. Non-Destructive Rollback & 3-Way Circuit Breakers

- **Zero-Commit Snapshot Rollback (Fail-Fast)**: Per `AGENTS.md` Safety & Invariants, omit `git commit` mid-loop and destructive Git resets/cleans. On `REVERT`, overwrite modified `Mutable Scope` files from `last-good/` and compare against `manifest.txt` to delete only unpromoted newly created in-scope files while keeping out-of-scope files, Git state, and symlinks untouched.
- **3-Way Circuit Breakers (`HALTED`)**: Halt immediately when: (1) **Budget Exhausted** (rounds == `max_iterations`, default `5`), (2) **Stall / Oscillation** (`stall_limit`, default `2` consecutive `REVERT`s, consecutive zero-progress ties, or A↔B finding oscillation), or (3) **Scope / Ambiguity Halt**.
- **Pre-Exit Tree Check**: Confirm every working-tree file in `Mutable Scope` matches `last-good/` cleanly before reporting `CONVERGED` or `HALTED`.

## 5. Governance & Exit Gate

1. **Mandatory Exit Report**: Deliver (1) `Exit Status & Reason` (`ALREADY_SATISFIED`, `CONVERGED`, or `HALTED` + trigger), (2) `Baseline -> Final Summary` (metric/finding deltas + retained files), and (3) `Verification Evidence` (`Closing Verify` outputs, `file:line` citations, `ledger.md` summary).
2. **User Completion Declaration Gate**: `Closing Verify` (`CONVERGED`) is verification evidence, not completion. Preserve `.agents/scratch/goal-loop/<run-id>/` and hold commits until explicit user completion declaration per `AGENTS.md` User-Gated Completion and Phase Boundary Gate. On `HALTED`, leave `last-good` intact and ask the user whether to: (1) adjust contract/`Mutable Scope` and resume, (2) raise `max_iterations` and resume, or (3) accept/discard `last-good`.
