---
name: my-code-review
description: >
   Review project codebase thoroughly across multiple dimensions: execution logic correctness, code errors, code quality, duplicate code, and excessive exception handling that violates Fail-Fast principles. Evaluates code quality, duplication, and exception handling strictly against the standards defined in the my-coding-guidelines skill. Use this skill whenever the user asks to review code, check code quality, find bugs, audit a codebase, look for duplicates, evaluate exception handling, or wants any kind of systematic code analysis — even if they don't explicitly say "code review".
---

# Code Review

Perform a comprehensive, multi-dimensional review of the target codebase or file(s). The goal is to surface real, actionable issues — not to produce a checklist of minor nitpicks. Think like a senior engineer who owns this code and must maintain it.

## Review Dimensions

Perform the review across the following five dimensions. Each dimension specifies its evaluation standard and detection focus areas inline.

### 1. Execution Logic Evaluation (실행 로직 평가)

Trace the actual execution flow and reason about correctness:

- Are algorithms producing the intended result for all inputs, including edge cases?
- Are data transformations preserving meaning at each step?
- Are state mutations happening in the right order?
- Are async operations (promises, threads, coroutines) sequenced correctly?
- Are boundary conditions handled correctly at the *logic level* (empty collections, null inputs, off-by-one)? (Input-validation guards belong to dimension 5.)
- Are return values and side effects consistent with what callers expect?

Flag logic bugs with a concrete example of how they would manifest (e.g., "when input list is empty, `reduce()` on line 42 throws — no guard exists").

### 2. Code Error Review (코드 에러 검토)

Look for defects that would cause failures at runtime or produce wrong results:

- Null / undefined dereferences
- Type mismatches or unsafe casts
- Resource leaks (unclosed files, DB connections, sockets)
- Incorrect error propagation (swallowed exceptions, lost stack traces)
- Race conditions and shared mutable state
- Off-by-one errors, integer overflow, incorrect index arithmetic
- Dependency on undefined behavior or language-specific gotchas

Be specific: quote the line or snippet and explain *why* it is an error.

### 3. Code Quality Evaluation (코드 퀄리티 평가)

Assess maintainability, readability, and naming conventions strictly against the **Architecture & Design Principles**, **Coding Style & Clean Code**, **Naming Conventions**, and **Documentation** sections defined in [my-coding-guidelines](../my-coding-guidelines/SKILL.md). Read that file before evaluating. Detection focus areas (standards defined in my-coding-guidelines):

- **Architecture**: SRP violations, tight coupling, YAGNI violations, constructor side-effects
- **Coding Style**: function length >30–40 lines, nesting >2 levels, SLAP violations, magic values, implicit types, inline imports, nested helpers, dead code, file layout order
- **Naming**: missing verb-noun prefix, missing boolean prefix (`is_`/`has_`/`can_`), vague names, non-standard abbreviations, non-plural collections, asymmetric antonyms
- **Documentation**: comments explaining *what* instead of *why*

### 4. Duplicate Code Evaluation (중복 코드 평가)

Identify repetition that increases maintenance burden, evaluated against the **Single Source of Truth (SSoT)** and **DRY** principles in [my-coding-guidelines](../my-coding-guidelines/SKILL.md). Read that file before evaluating. The following are *detection patterns* — the evaluation standard is my-coding-guidelines:

- **Near-identical blocks**: Differ only by a variable or constant → suggest extracting into a parameterized function.
- **Copy-pasted logic**: Duplicated code that should be shared → suggest extracting to a utility or base class.
- **Multiple implementations**: Same concept implemented in different parts of the codebase → suggest consolidating.
- **Similar data structures**: Structures representing the same domain concept → suggest unifying.

When flagging duplication, point to *all* locations and suggest the consolidation target.

### 5. Fail-Fast & Exception Handling Review (fast fail 위배 / 과도한 예외처리 검토)

Evaluate the exception handling design and state validation flow strictly against the **Error Handling & Reliability** section in [my-coding-guidelines](../my-coding-guidelines/SKILL.md). Read that file before evaluating. Detection focus areas (standards defined in my-coding-guidelines):

- **Fail-Fast missing**: entry points not immediately halting on invalid args, wrong types, or invalid state
- **Exception swallowing**: empty `except`/`catch` or over-broad catches (e.g., `except Exception`) that mask bugs
- **Silent fallbacks**: returning `null`, `-1`, or empty defaults on failure indistinguishable from valid results
- **Stack trace lost**: re-throwing without preserving original context (e.g., `raise Exception(str(e))`)
- **Oversized try blocks**: `try` wrapping unrelated logic, masking which line actually raises
- **Operational errors unhandled**: network, DB, I/O calls with no try-catch
- **Boundary states not guarded**: missing *defensive validation* at function entry points (empty collections, None inputs, off-by-one); logic-level boundary errors are covered in dimension 1

---

## Output Format

Structure your review as follows. Skip sections with no findings — don't pad with "No issues found" for every clean section.

```
## Code Review: <target>

### Summary
One paragraph: overall health of the code, most critical issues, general impression.

### 1. Execution Logic
[findings or omit section]

### 2. Code Errors
[findings or omit section]

### 3. Code Quality
[findings or omit section]

### 4. Duplicate Code
[findings or omit section]

### 5. Fail-Fast & Exception Handling
[findings or omit section]

### Priority Action Items
Numbered list: most impactful fixes first. Each item: what to fix, where, why it matters.
```

**Severity levels**:
- 🔴 **Critical**: runtime failures, data corruption, unhandled exceptions, Fail-Fast violations
- 🟡 **Major**: maintainability degradation, naming violations, significant duplication, logic smell
- 🔵 **Minor**: documentation, style, low-impact improvements

For each finding, include:
- **Location**: file path + line number or function name
- **Issue**: what is wrong and why
- **Guideline**: which my-coding-guidelines rule was violated (for dimensions 3, 4, 5)
- **Suggestion**: concrete fix or direction

Example:

> #### 🔴 Missing Fail-Fast at entry point
> - **Location**: `src/service.py:42` — `process_order()`
> - **Issue**: `order_id` is not validated for `None`; downstream `db.fetch(order_id)` raises unhandled `TypeError`.
> - **Guideline**: Error Handling & Reliability — Fail-Fast (for Programming Errors)
> - **Suggestion**: Add `if order_id is None: raise ValueError("order_id must not be None")` at function entry.

---

## Review Process

1. **Confirm Scope**:
   - If the user specifies a file, module, or feature, use that as the review scope.
   - If the scope is the entire project, start with entry points and high-traffic paths.
   - **If scope is unclear**, ask the user which files or features to prioritize before proceeding.
   - Record the agreed scope at the top of every dimension file and `consolidated.md`.

2. **Allocate Dimensions to Subagents**:
   - Generate a single `YYYYMMDD_HHMMSS` timestamp now (e.g., `20260625_132000`). This timestamp is the session ID for all files in this review.
   - Invoke 5 subagents in parallel, one per dimension. Pass the following to each subagent:
     - The agreed scope (file list or module boundary)
     - The session timestamp (`YYYYMMDD_HHMMSS`)
     - The dimension name to substitute as `<Dimension Name>` in the prompt template below
   - Use this prompt template for each subagent invocation:

     ```
     You are performing a focused code review for the **<Dimension Name>** dimension only.

     Session ID: <YYYYMMDD_HHMMSS>
     Scope: <agreed scope — list of files or module path>

     Your job:
     1. Read `.agents/skills/my-coding-guidelines/SKILL.md` in full — all quality, duplication,
        and exception-handling judgements must be grounded in that document.
     2. Read `.agents/skills/my-code-review/SKILL.md` and locate the evaluation criteria
        for <Dimension Name>.
     3. Read EVERY file in the scope completely. Do not sample or skip files.
     4. For each finding, quote the relevant code snippet and explain why it is an issue,
        citing the specific guideline it violates.
     5. Minimum depth standard: surface at least one finding per 100 lines of code reviewed,
        OR explicitly state "No issues found in <file>" after reading it.
     6. Save your results to: .agents/docs/my-code-review/<YYYYMMDD_HHMMSS>/<dimension-name>.md

     Do not review other dimensions. Do not summarize or skip — read every line.
     ```

3. **Save Individual Findings**:
   - Each subagent writes its findings to: `.agents/docs/my-code-review/<YYYYMMDD_HHMMSS>/<dimension-name>.md`
   - `<dimension-name>` is one of: `execution-logic`, `code-errors`, `code-quality`, `duplicate-code`, `fail-fast`
   - Each file must use the following format:

     ```
     # <Dimension Name> Review
     Scope: <agreed scope>

     ## Files Reviewed
     - path/to/file.py — <line count> lines
     - path/to/clean.py — <line count> lines — ✅ No issues found

     ## Findings

     ### [🔴/🟡/🔵] Finding Title
     - **Location**: file path + line number or function name
     - **Issue**: what is wrong and why
     - **Guideline**: which my-coding-guidelines rule was violated (for dimensions 3, 4, 5)
     - **Suggestion**: concrete fix or direction
     ```

   - **Coverage rule**: Every file in scope must appear under `## Files Reviewed`, even if no issues were found.
   - **Evidence rule**: Every finding must quote the exact code snippet. No vague claims.

4. **Consolidate Findings**:
   - Read all generated dimension files from `.agents/docs/my-code-review/<YYYYMMDD_HHMMSS>/`.
   - Consolidate and de-duplicate findings across dimensions.
   - Save the consolidated report (following the **Output Format** section) to: `.agents/docs/my-code-review/<YYYYMMDD_HHMMSS>/consolidated.md`

5. **Create & Execute Action Tasks**:
   - Translate **ALL findings** from `consolidated.md` into tasks — including low-severity ones. Do not silently drop any finding.
   - Save this checklist to: `.agents/docs/my-code-review/<YYYYMMDD_HHMMSS>/tasks.md`
   - Use the following template for each task:

     ```
     ## Tasks
     Total: <N> | Done: 0 | Skipped: 0 | Remaining: <N>

     - [ ] TODO | [🔴/🟡/🔵] <Task Title> | <file:line>
       - What: <what to fix>
       - Why: <why it matters>
       - Verify: <shell command — if not automatable, write `manual: <what to inspect>`>

     ---
     ## Verification Results
     (filled after all tasks are DONE or SKIPPED)
     ```

   - **Execution loop** — repeat until no TODO remains:
     1. Read `tasks.md` to find the next `TODO` task.
     2. Apply the fix directly to the codebase.
     3. Update the task status in `tasks.md` **before moving to the next task**:
        - `[x] DONE` — fix applied and verified.
        - `[-] SKIPPED: <reason>` — intentionally skipped. Reason is mandatory. No silent skips.
     4. Update the `Total / Done / Skipped / Remaining` counters.
   - Every task must end as either DONE or SKIPPED. No task may remain TODO at termination.

6. **Post-Review Verification**:
   - Once all tasks in `tasks.md` are marked `[x] DONE`, run the verification command listed in each task.
   - For `manual:` verify entries, perform the described inspection and record the result.
   - Confirm no regressions or side effects were introduced.
   - Document the results in the `## Verification Results` section of `tasks.md`.
