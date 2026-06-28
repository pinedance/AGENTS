# Project

## General Principles

* **Execution Flow:** Strictly follow the sequence below. Never proceed to implementation without planning and obtaining explicit user approval:
  > Plan → Approval → Execute
* **No Speculation:** Do not make assumptions when uncertain; always stop and ask the user for clarification.
* **Workspace Discovery:**
  * Read [README.md](file:README.md) to comprehend the project's nature, scope, and technical details.
  * If [agents.local.md](file:.agents/agents.local.md) exists, read and adhere to its local rules.

## Guidelines

### 1. Think Before Coding
* **Avoid Assumptions:** Explicitly state assumptions and surface tradeoffs. Do not silently pick one interpretation.
* **Stop & Ask:** If something is unclear or confusing, stop and ask the user.
* **Push for Simplicity:** Propose simpler approaches and push back on complexity when warranted.

### 2. Simplicity First
* **Minimalistic Code:** Implement only the minimum code required to solve the problem. Avoid speculative features, abstractions for single-use code, or unrequested configuration.
* **Keep it Concise:** Avoid error handling for impossible scenarios. If code can be rewritten more simply (e.g., 50 lines instead of 200), rewrite it.

### 3. Surgical Changes
* **Minimal Scope:** Touch only what you must. Do not "improve" or refactor adjacent, unrelated code, comments, or formatting. Match the existing style.
* **Orphan Cleanup:** Remove only the imports, variables, or functions that became unused due to *your* changes. Do not touch pre-existing dead code.

### 4. Goal-Driven Execution
* **Verifiable Goals & Loops:** Transform imperative tasks into declarative, verifiable success criteria (e.g., reproducing tests) and verify before and after.
* **Step-by-step Planning:** Outline a brief step-and-verify plan for multi-step tasks. Leverage loops to independently verify progress.

### Key Indicators & Tradeoffs
* **How to Know It's Working:** Minimal diffs, simpler code on first try, clarifying questions asked beforehand, and clean PRs.
* **Tradeoff:** Caution over speed. Not required for trivial tasks (e.g., simple typos or obvious one-liners), but essential for non-trivial tasks.

