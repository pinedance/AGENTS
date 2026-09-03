---
name: my-begin
description: >
  Initializes workspace context at the start of a session or task.
  Loads, parses, and strictly follows project directives from AGENTS.md, AGENTS.local.md, and memory files.
  Trigger this skill at the beginning of any session, when starting a new task, or whenever foundational project context and rules need to be loaded and applied.
---

# My Begin — Workspace Context Initialization & Directive Enforcement

This skill loads foundational project context and ensures the agent strictly internalizes and adheres to all project rules, guidelines, and active memories before taking further action.

---

## STEP 0: MANDATORY FIRST TOOL CALL (CRITICAL)

**DO NOT output any text response to the user until Step 0 tool calls are completed.**

1. **Locate and Read Project Directives**:
   - Check and execute `view_file` on `<project_root>/.agents/AGENTS.md` or `<project_root>/AGENTS.md`.
   - If `<project_root>/.agents/AGENTS.local.md` (or `<project_root>/AGENTS.local.md`) exists, call `view_file` on it as well.
   - If `<project_root>/.agents/memory/*.md` exists, read all active memory files.

2. **Strictly Internalize & Follow Directives**:
   - **Do not just read the files — actively enforce every rule, constraint, coding guideline, architectural pattern, and workflow defined within them.**
   - All subsequent reasoning, tool executions, suggestions, and responses throughout the entire session must strictly comply with the loaded directives.
   - If a directive conflicts with a default assumption, the project directive in `AGENTS.md` / `AGENTS.local.md` takes absolute precedence.

---

## Usage Protocol for Calling Skills

When invoking this skill from other skills (such as `my-new-session`):

```markdown
**Context Initialization Gate**: Invoke `my-begin` skill protocol first to load and enforce all project directives before proceeding to downstream tasks.
```
