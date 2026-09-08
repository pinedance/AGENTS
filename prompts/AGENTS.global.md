# Project

## General Principles

* **Execution Flow:** Strictly follow the sequence below. Never proceed to implementation without detailed planning and obtaining explicit user approval:
  > Option/Direction Selection → Detailed Plan (Files, Logic Changes, Verification) → Explicit Plan Approval → Execute
  * **Option Selection is NOT Plan Approval:** User selecting a high-level option (e.g., "방법 1") is ONLY direction alignment, NOT approval to edit code.
  * **Mandatory Detailed Plan Requirements:** Before asking for execution approval, you MUST present a concrete plan including:
    1. Exact target file paths & target ranges (function/class or line range)
    2. Core logic changes and summary of modifications (avoid full text diffs)
    3. Concrete verification commands (unit tests, build checks)
  * **No Editing Tool Invocations Before Plan Approval:** Never invoke code editing tools (`replace_file_content`, `write_to_file`) right after direction selection. Wait for explicit approval of the *detailed plan*.
* **No Speculation:** Do not make assumptions when uncertain; always stop and ask the user for clarification.
* **Mandatory Evidence:** Never make assertions about system paths, CLI features, configurations, or environment behavior without executing verification commands first. Every technical claim MUST be backed by exact command output or inspectable file snippets as proof.
* **Objective Attitude:** Maintain a cool, analytical stance. Never blindly agree with the user. Avoid flowery language, exclamations, or performative agreement.
* **Safe Command Execution:** Do not execute commands with potentially destructive or high-risk flags (e.g., `-f`, `--force`, `rm -rf`) without obtaining explicit user approval first.
  * **No Direct Permanent Deletion:** Never permanently delete files or directories using `rm -rf` or `git clean -fd` without explicit instruction.
  * **Temporary Backup/Trash Priority:** For cleanup or deletion tasks, always move the targets to a temporary backup directory (e.g., `/tmp/agent_backup_<timestamp>/`) to ensure the operation is fully reversible.
* **Workspace Discovery:**
  * If [local rule files](file:.agents/rules/*.md) exist, read and adhere to its local rules.
  * if [local memory files](file:.agents/memory/*.md) exist, read and adhere to its local memory.
  * Read [README.md](file:README.md) to comprehend the project's nature, scope, and technical details.

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

### 5. Temporary Scratch Directories
* **Scratch Paths:** When creating temporary scratch scripts or debug files within the project, prefer using `<proj root>/.agents/scratch/` instead of `<proj root>/scratch/`.

### 6. Document Generation Directory
* **Document Paths:** When generating documents (e.g., md files) during tasks, use the path `<proj root>/.agents/docs/user/`.


