---
name: my-code-review
description: >
   Review project codebase thoroughly across multiple dimensions: execution logic correctness, code errors, code quality, duplicate code, and excessive exception handling that violates fast-fail principles. Use this skill whenever the user asks to review code, check code quality, find bugs, audit a codebase, look for duplicates, evaluate exception handling, or wants any kind of systematic code analysis — even if they don't explicitly say "code review".
---

# Code Review

Perform a comprehensive, multi-dimensional review of the target codebase or file(s). The goal is to surface real, actionable issues — not to produce a checklist of minor nitpicks. Think like a senior engineer who owns this code and must maintain it.

## Review Dimensions

Perform the review across the following five dimensions. For dimensions 3, 4, and 5, evaluate the code strictly against the standards defined in the [my-coding-guidelines](../my-coding-guidelines/SKILL.md) skill.

### 1. Execution Logic Evaluation (실행 로직 평가)

Trace the actual execution flow and reason about correctness:

- Are algorithms producing the intended result for all inputs, including edge cases?
- Are data transformations preserving meaning at each step?
- Are state mutations happening in the right order?
- Are async operations (promises, threads, coroutines) sequenced correctly?
- Are boundary conditions handled (empty collections, null inputs, off-by-one)?
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

Assess maintainability, readability, and naming conventions strictly against the standards defined in the [my-coding-guidelines](../my-coding-guidelines/SKILL.md) skill.

### 4. Duplicate Code Evaluation (중복 코드 평가)

Identify repetition that increases maintenance burden:

- **Near-identical blocks**: Differ only by a variable or constant → suggest extracting into a parameterized function.
- **Copy-pasted logic**: Duplicated code that should be shared → suggest extracting to a utility or base class.
- **Multiple implementations**: Same concept implemented in different parts of the codebase → suggest consolidating.
- **Similar data structures**: Structures representing the same domain concept → suggest unifying.
- **DRY (Don't Repeat Yourself) principle**: Evaluate compliance against the SSoT guidelines in [my-coding-guidelines](../my-coding-guidelines/SKILL.md).

When flagging duplication, point to *all* locations and suggest the consolidation target.

### 5. Fast-Fail & Exception Handling Review (fast fail 위배 / 과도한 예외처리 검토)

Evaluate the exception handling design and state validation flow strictly against the **Fast-Fail & Exception Safety** guidelines in [my-coding-guidelines](../my-coding-guidelines/SKILL.md).

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

### 5. Fast-Fail & Exception Handling
[findings or omit section]

### Priority Action Items
Numbered list: most impactful fixes first. Each item: what to fix, where, why it matters.
```

For each finding, include:
- **Location**: file path + line number or function name
- **Issue**: what is wrong and why
- **Suggestion**: concrete fix or direction

---

## Review Process

1. **Allocate Dimensions to Subagents**:
   - Assign each of the 5 Review Dimensions to an independent subagent.
   - Each subagent performs a focused review for its assigned dimension on the target codebase/files.

2. **Save Individual Findings**:
   - Each subagent writes its findings to a markdown file at: `.skills/docs/my-code-review/YYYYMMDD_HHMMSS/<dimension-name>.md`
   - Path format:
     - `YYYYMMDD_HHMMSS`: Current local timestamp of review start (e.g., `20260625_132000`)
     - `<dimension-name>`: One of `execution-logic`, `code-errors`, `code-quality`, `duplicate-code`, `fast-fail`
   - Each file must list the findings with location, issue detail, suggested fix, and severity (🔴 Critical, 🟡 Warning, 🔵 Suggestion).

3. **Consolidate Findings**:
   - Read all generated markdown files from `.skills/docs/my-code-review/YYYYMMDD_HHMMSS/`.
   - Consolidate and summarize the findings. Remove overlaps.
   - Format the final output according to the **Output Format** section.

4. **Create & Execute Action Tasks**:
   - Divide the priority action items into discrete, step-by-step tasks.
   - Implement the fix for each task and verify correctness individually.

5. **Post-Review Verification**:
   - Once all tasks are completed, verify all modifications to ensure correctness and that no regressions or side effects were introduced.
