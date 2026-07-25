---
name: my-project-rules
description: |
  CRITICAL WORKSPACE RULES (ALWAYS ACTIVE IN SYSTEM PROMPT):
  1. Execution Flow (Plan -> Approval -> Execute): NEVER modify codebase, write code, or execute edits without step-by-step planning and obtaining EXPLICIT user approval first.
  2. No Speculation: Do not make assumptions when uncertain; always stop and ask the user for clarification.
  3. Mandatory Evidence: Never make technical claims without executing verification commands or viewing file snippets first.
  4. Safe Execution: Do not run destructive commands (rm -rf, git clean) without approval. Use backup directory first.
  5. Surgical Changes: Touch only what you must. Do not refactor adjacent code or comments.
---

# Project Core Rules

This skill injects the project's foundational guidelines directly into the agent's system prompt on session start.

## Directives

1. **Plan -> Approval -> Execute**: Always state proposed plan and wait for user's explicit approval before using code-editing tools (`replace_file_content`, `multi_replace_file_content`, `write_to_file`, etc.).
2. **No Speculation**: Stop and ask if intent or context is ambiguous.
3. **Evidence-based Diagnosis**: Base claims on actual CLI outputs or file views.
4. **Surgical Scope**: Modify only specified files without altering unrelated formatting.
