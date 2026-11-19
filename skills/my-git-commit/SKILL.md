---
name: my-git-commit
description: >
  Analyze modified files, split them into logical groups, and commit them sequentially with descriptive Conventional Commit messages.
  Use when the user directly requests committing changes ("git commit", "commit changes", "커밋해줘"),
  when cleaning pre-existing dirty files in my-sess-open, or as the fallback commit analyzer when active conversation context is insufficient (e.g., post-/compact, resumed dirty state, external edits).
  When full change context is already in active conversation, commit logical groups directly without loading this skill.
---

# Git Smart Commit

Inspect dirty files (reading untracked files directly), partition changes by cohesive purpose/domain, and commit sequentially. Never squash unrelated changes into `git add -A`.

Commit **timing** follows `AGENTS.md` SSoT (never commit before user completion declaration, except `my-sess-open` dirty cleanup, `my-sess-close`, or explicit commit requests). Callers with active conversation context apply `Commit Message Rules` and `Exclusions` directly without loading this skill.

## Execution Modes

- **Autonomous Logical-Split (default)**: Workflow callers, context-recovery fallbacks, and `my-sess-open` Option 1. Apply `Exclusions` and `Commit Message Rules`, stage and commit logical groups sequentially without confirmation, and report SHAs and titles.
- **Single-Unit**: `my-sess-open` Single commit or explicit user request. Stage all eligible files into one Conventional Commit directly.
- **Interactive Logical-Split**: Only when user explicitly asks to preview/approve before committing. Present grouped commit titles with target files and commit only after approval.

## Commit Message Rules (SSoT)

- Follow Conventional Commits (`feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`, `style`); categorize multi-purpose files by primary intent.
- Keep titles under 50 characters; match the codebase's primary language (English default, Korean if Korean repo).
- Enumerate multiple changes as bullet points in the commit body.
- Verify resulting commits with `git log --oneline -5`.

## Edge Cases (Fail-Fast)

- **Clean tree**: Report `"No changes to commit."` and stop.
- **Pre-existing staged files**: Respect existing staged state and notify user.
- **Single logical group**: Execute one commit under the active mode.
- **Merge conflicts / unresolved paths**: Halt immediately and request manual resolution.

## Exclusions (SSoT)

- Exclude ephemeral artifacts under `.agents/plans/`, `.agents/docs/`, and `.agents/scratch/` unless explicitly requested by the user.
- Persistent project markdown (`README.md`, `SKILL.md`, `STATE.md`, `rules/*.md`, `memory/*.md`) remains normal commit targets.
