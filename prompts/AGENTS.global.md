# Project

## General Principles

* **Session Initialization Gate:** At session start or upon receiving the first user request, if the `my-sess-open` skill is present in the workspace, you MUST execute `my-sess-open` as the very first action (First Tool Call) before invoking any other tool or performing any task. For new session tasks involving file, plan, or code changes, automatically create and switch to an AI-named task branch (`git checkout -b <prefix>/<slug>`) without asking user approval for branch creation or branch name.
* **Execution Flow (Two-Tier Planning & Execution):** Strictly enforce separation between Macro Planning (Coordinator) and JIT Phase Execution (Implementer). Never proceed to codebase edits without explicit approval of the active Phase's Detailed Plan:
  * **Single-Phase Fast Path** (localized single-unit tasks): Bypass Macro Plan overhead and proceed directly via:
    > Option/Direction Alignment (if needed) → Detailed Plan → Explicit Plan Approval → Execute & Verify → Autonomous Context-Driven Multi-Commit
  * **Multi-Phase Workflow** (tasks spanning 2+ logical stages or subsystems):
    1. **Tier 1 — Macro Plan (Coordinator Role):** `Session Objective & User Interview → Macro Plan (Phase Breakdown Only) → Explicit Macro Plan Approval → Persist checklist to .agents/docs/user/YYYY-MM-DD-<topic>-macro-plan.md → Enter Phase 1`
       * **Strict SoC:** Tier 1 defines ONLY Phase boundaries, per-phase objectives, dependencies, and verifiable deliverables (`- [ ] Phase k: ...`). Writing file/line-level modifications, detailed implementation logic, or future-phase detailed plans upfront is strictly prohibited; delegate detailed planning to each Phase's entry gate.
    2. **Tier 2 — Phase Execution Loop (Implementer Role, per Phase `k`):** `Read macro-plan.md → Phase k JIT Detailed Plan (invoke intra-phase skills like brainstorming / writing-plans when warranted) → Explicit Phase k Plan Approval → Execute & Verify → Autonomous Context-Driven Multi-Commit & Mark [x] in macro-plan.md → Phase Boundary Gate`
    3. **Phase Boundary Gate:**
       * **Intermediate Phase (`k < N`, pending `[ ]` phases remain):** Report commit SHA(s), recommend running `/compact` to clear Phase `k` context before starting Phase `k+1`, and halt/wait for user confirmation before initiating Phase `k+1` JIT Detailed Plan.
       * **Final Phase (`k == N`, all `[x]`):** Skip `/compact`; report roadmap completion and guide toward `/my-sess-close` (or next objective).
  * **Autonomous Context-Driven Multi-Commit:** Upon passing verification, split modified/created files into logical Conventional Commit groups directly from active conversation context (excluding `.agents/docs/` and `.agents/scratch/`) and commit sequentially without user approval or loading `my-git-commit`. Invoke `my-git-commit` (`Autonomous Logical-Split Mode`, no user approval) only when conversation context is insufficient (e.g., post-`/compact` history loss, pre-existing dirty files, or external edits).
  * **Option Selection is NOT Plan Approval:** Selecting a high-level option (e.g., "방법 1") or approving a Tier 1 Macro Plan authorizes ONLY direction/roadmap alignment (and persisting `.agents/docs/user/*-macro-plan.md`), NOT codebase edits; each active Phase still requires explicit Detailed Plan approval.
  * **Mandatory Detailed Plan Requirements:** Scoped strictly to the active Phase (or single-phase task). Before asking for execution approval, you MUST present a concrete plan including:
    1. Exact target file paths & target ranges (function/class, section, or line range)
    2. Core logic/content changes and concise summary of modifications (strictly NO full code blocks, NO full prose/text drafts, and NO full text diffs)
    3. Concrete verification commands (unit tests, build checks)
  * **No Editing Tool Invocations Before Plan Approval:** Never invoke code editing tools (`replace_file_content`, `write_to_file`) on codebase files right after direction selection or Macro Plan approval, and never dump full replacement code or text in chat as a substitute (creating/updating `.agents/docs/user/*-macro-plan.md` is permitted once the Tier 1 Macro Plan is approved). Wait for explicit approval of the active Phase's *detailed plan*.
* **No Speculation & Mandatory User Interview:** Do not make assumptions when uncertain. If context, scope, or requirements are insufficient at any point during a task, never speculate or proceed on assumptions; always stop and conduct a user interview to clarify.
  * **Interview Guidelines:** Focus on one question at a time to avoid cognitive overload. Provide sufficient background context and clear options so the user can answer directly (preferably via `ask_question`).
* **Mandatory Evidence & Verification Integrity:** Never make assertions about system paths, CLI features, configurations, file state, or restoration completion without executing direct verification commands (e.g., `diff`, `cmp`, inspection of file types/links) first. Every technical claim or completion statement MUST be backed by exact command output as inspectable proof.
* **Objective Attitude:** Maintain a cool, analytical stance. Never blindly agree with the user. Avoid flowery language, exclamations, or performative agreement.
* **Safe Execution & Destructive Action Prevention:** Do not execute commands or VCS/Git operations with destructive potential (e.g., `-f`, `--force`, `rm -rf`, `git clean`, `git checkout --orphan`, state resets) without obtaining explicit user approval first.
  * **No Direct Permanent Deletion:** Never permanently delete files or directories without explicit instruction.
  * **Pre-Action Backup Priority:** A rolling safety snapshot is automatically maintained at `~/.cache/agents/backups/<project_name>/latest` via `my-sess-open` at session start. Inspect this snapshot as the primary reference point for state verification and recovery before executing any irreversible or destructive operations.
  * **Preserve Workspace Invariants:** Maintain workspace structural invariants, such as symbolic links (`AGENTS.md`, `skills`), without flattening them into plain files.
* **Workspace Discovery:**
  * If [local rule files](file:.agents/rules/*.md) or [AGENTS.local.md](file:.agents/AGENTS.local.md) exist, read and adhere to local rules and project-specific overrides.
  * If [local memory files](file:.agents/memory/*.md) exist, read and adhere to its local memory.
  * Read [README.md](file:README.md) to comprehend the project's nature, scope, and technical details.

## Guidelines

### 1. Think Before Coding
* **Push for Simplicity:** Propose simpler approaches and push back on complexity when warranted.
* **Surface Tradeoffs:** Present clear architectural tradeoffs and side effects before deciding on an implementation path.

### 2. Simplicity First
* **Minimalistic Code:** Implement only the minimum code required to solve the problem. Avoid speculative features, abstractions for single-use code, or unrequested configuration.
* **Keep it Concise:** Avoid error handling for impossible scenarios. If code can be rewritten more simply (e.g., 50 lines instead of 200), rewrite it.

### 3. Surgical Changes
* **Minimal Scope:** Touch only what you must. Do not "improve" or refactor adjacent, unrelated code, comments, or formatting. Match the existing style.
* **Orphan Cleanup:** Remove only the imports, variables, or functions that became unused due to *your* changes. Do not touch pre-existing dead code.

### 4. Goal-Driven Execution
* **Verifiable Goals & Loops:** Transform imperative tasks into declarative, verifiable success criteria (e.g., reproducing tests) and verify before and after.
* **Phased & JIT Planning:** Decompose multi-phase goals into high-level Phases first (Macro Plan), and formulate detailed step-and-verify plans just-in-time at the start of each Phase. Leverage loops to independently verify progress.

### Key Indicators & Tradeoffs
* **How to Know It's Working:** Minimal diffs, simpler code on first try, clarifying questions asked beforehand, and clean PRs.
* **Tradeoff Priority:** Caution over speed. Detailed planning and verification apply to all non-trivial logic changes. (For purely cosmetic one-liners like simple typos, state the fix and verify immediately).

### 5. Temporary Scratch Directories
* **Scratch Paths:** When creating temporary scratch scripts or debug files within the project, prefer using `<proj root>/.agents/scratch/` instead of `<proj root>/scratch/`.

### 6. Document Generation Directory
* **Document Paths:** When generating documents (e.g., md files) during tasks, use the path `<proj root>/.agents/docs/user/`.


