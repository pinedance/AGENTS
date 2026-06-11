---
name: my-code-review
description: Review project codebase thoroughly across multiple dimensions: execution logic correctness, code errors, code quality, duplicate code, and excessive exception handling that violates fast-fail principles. Use this skill whenever the user asks to review code, check code quality, find bugs, audit a codebase, look for duplicates, evaluate exception handling, or wants any kind of systematic code analysis — even if they don't explicitly say "code review".
---

# Code Review

Perform a comprehensive, multi-dimensional review of the target codebase or file(s). The goal is to surface real, actionable issues — not to produce a checklist of minor nitpicks. Think like a senior engineer who owns this code and must maintain it.

## Review Dimensions

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

Assess maintainability and readability:

- **Naming**: Do names communicate intent without needing comments to explain them?
- **Function size and responsibility**: Is each function doing one thing? Functions longer than ~30–40 lines are worth scrutinizing.
- **Abstraction level consistency**: Does a single function mix high-level orchestration with low-level detail?
- **Coupling**: Are modules unnecessarily aware of each other's internals?
- **Magic values**: Are raw literals scattered through logic where named constants belong?
- **Dead code**: Are there unreachable branches, unused variables, or imports?
- **Testability**: Is the code structured so that units can be tested in isolation?

Distinguish between must-fix issues (correctness, security) and nice-to-have improvements (style, naming). Don't treat style opinions as bugs.

### 4. Duplicate Code Evaluation (중복 코드 평가)

Identify repetition that increases maintenance burden:

- Near-identical blocks that differ only by a variable or constant → extract into a parameterized function
- Copy-pasted logic that should be shared → extract to a utility or base class
- Multiple implementations of the same concept in different parts of the codebase → consolidate
- Similar data structures that represent the same domain concept → unify

When flagging duplication, point to *all* locations and suggest the consolidation target.

### 5. Fast-Fail & Exception Handling Review (fast fail 위배 / 과도한 예외처리 검토)

Fast-fail means: detect invalid state as early as possible and stop loudly, rather than silently carrying bad state forward.

Look for violations:

- **Swallowing exceptions**: `catch` blocks that log (or do nothing) and continue — the caller never knows something went wrong
- **Over-broad catches**: `catch (Exception e)` or `except:` that mask unexpected errors, hiding bugs
- **Silent fallbacks**: returning a default value on error when the caller has no way to distinguish success from failure
- **Deferred validation**: inputs validated deep in the call stack rather than at entry points
- **Excessive nesting**: defensive checks that wrap every operation in try/catch when only specific errors are expected
- **Suppressed stack traces**: re-throwing as a generic error that loses origin context

Also flag the opposite — code that *should* have a try/catch but doesn't, leaving the caller exposed to unhandled exceptions.

The principle: fail loud, fail early, fail with enough context to diagnose.

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

1. **Understand scope first.** If the user specifies a file, module, or feature, focus there. If the scope is the entire project, start with entry points and high-traffic paths.

2. **Read before writing.** Scan the full target before making any judgments. Patterns that look wrong in isolation may be intentional.

3. **Be proportionate.** A 50-line utility script and a 5,000-line service have different thresholds. Calibrate severity accordingly.

4. **Distinguish severity:**
   - 🔴 **Critical** — bugs, security issues, data loss risk
   - 🟡 **Warning** — maintainability problems, latent risks
   - 🔵 **Suggestion** — improvements worth considering

5. **Back claims with evidence.** Quote code when flagging an issue. Don't make vague claims like "this could be improved."

6. **If scope is unclear**, ask the user which files or features to prioritize rather than guessing.
