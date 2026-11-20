---
name: my-git-commit
description: >
  Analyze modified files, split them into logical groups, and commit them sequentially with descriptive Conventional Commit messages.
  Use when the user directly requests committing changes ("git commit", "commit changes", "커밋해줘"),
  when cleaning pre-existing dirty files in my-sess-open, or as the fallback commit analyzer when active conversation context is insufficient (e.g., post-/compact, resumed dirty state, external edits).
  When full change context is already in active conversation, commit logical groups directly without loading this skill.
---

# Git Smart Commit

Partition dirty files (reading untracked files directly) by cohesive intent and commit sequentially (avoid `git add -A` bundling). Inherit commit timing, `Conventional Commits` rules/verification (`git log --oneline -5`), and path exclusions from `AGENTS.md` Auto Multi-Commit and Shared Conventions SSoT. Callers with active conversation context apply those `AGENTS.md` rules directly without loading this skill.

## Execution Modes

- **Autonomous Logical-Split (default)**: Workflow callers, context-recovery fallbacks, and `my-sess-open` Option 1. Stage and commit logical groups sequentially without confirmation, then report SHAs and titles.
- **Single-Unit**: `my-sess-open` Single commit or explicit single-commit request. Stage all eligible files into one commit directly.
- **Interactive Logical-Split**: Only when user explicitly requests preview/approval. Present grouped commit titles with target files and commit only after approval.

## Edge Cases (Fail-Fast)

- **Clean tree**: Report `"No changes to commit."` and stop.
- **Pre-existing staged files**: Respect existing staged state and notify user.
- **Single logical group**: Execute one commit under the active mode.
- **Merge conflicts / unresolved paths**: Halt immediately and request manual resolution.
