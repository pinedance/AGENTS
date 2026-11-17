---
name: my-git-commit
description: >
  Analyze modified files, split them into logical groups, and commit them sequentially with descriptive Conventional Commit messages.
  Use when the user directly requests committing changes ("git commit", "commit changes", "커밋해줘"),
  or when delegated as the commit strategy by a session or plan workflow (my-sess-open, my-sess-close, executing-plans, subagent-driven-development).
---

# Git Smart Commit

Analyze changes, group them logically, and commit sequentially.
Do not squash all changes into a single `git add -A && git commit` unless it represents a single logical unit.

## Process

### Step 1: Analyze Status

```bash
git status --short
git diff --stat
git diff          # Tracked files changes
git diff --cached # Staged files changes
```

For untracked files, manually read their content to understand their purpose since they do not appear in `git diff`.

### Step 2: Categorization & Grouping

Determine the **purpose and domain** of each change, then group files accordingly.

**Grouping Criteria**:
- Files belonging to the same feature/bugfix → Single commit
- Distinct modifications with different goals → Separate commits

**Standard Prefixes**:

| Prefix | Description | Example Files |
|-----------|------------------|-------------------|
| `feat:` | New feature | New modules, components |
| `fix:` | Bug fix | Logic error fixes |
| `docs:` | Documentation | README.md, comments |
| `ci:` | CI/CD pipeline | `.github/workflows/`, `Dockerfile` |
| `chore:` | Build/Config/Deps| `pyproject.toml`, `package.json`, `.gitignore` |
| `refactor:`| Code refactoring | Structural change without behavior change |
| `style:` | Code style/format| CSS, Prettier formatting |
| `test:` | Testing | Test scripts |

If a file contains changes for multiple purposes, categorize it under the primary purpose.

### Step 3: Establish Commit Plan & Execution Modes

Select the execution mode matching the caller context:

- **Interactive Logical-Split Mode (default — direct user request, or `Logical group commits` selected in `my-sess-open` or `my-sess-close`)**:
  Present the grouped commit plan in the format below and obtain explicit user approval before Step 4. If adjustments are requested, revise the grouping or messages and re-confirm.

```
I will proceed with the following commits. Do you approve?

Commit 1: ci: enable schedule/push triggers
  → .github/workflows/deploy.yml

Commit 2: feat: add Amplify build config and on_post_build hook
  → amplify.yml, hooks/copy_amplify.py, mkdocs.yml

Commit 3: docs: revamp README
  → README.md
```

- **Single-Unit Mode (when `Single commit` is explicitly selected in `my-sess-open` or `my-sess-close`)**:
  Apply `Exclusions` and `Commit Message Rules`, stage all eligible modified/untracked files as a single unit, and execute one Conventional Commit directly (the user's explicit menu choice authorizes the single commit).

- **Pre-Approved Plan Execution Mode (`executing-plans`, `subagent-driven-development`)**:
  When committing a task whose scope was already approved in an implementation plan (whether executed inline via `executing-plans` or inside an isolated task subagent via `subagent-driven-development`), apply `Exclusions` and `Commit Message Rules` to stage and commit only task-scoped logical groups directly without a second interactive approval gate, and report resulting commit SHAs and titles.

### Step 4: Sequential Execution

For each group:

```bash
git add <file1> <file2> ...
git commit -m "<prefix>: <title>

<Optional description of what was changed and why>"
```

**Commit Message Rules**:
- Enforce Conventional Commits specification (e.g., `feat:`, `fix:`, `refactor:`, `test:`, `chore:`)
- Keep titles under 50 characters.
- Match the primary language of the codebase (English by default, Korean if project language is Korean).
- Enumerate multiple changes as bullet points in the commit body.

**Verification**:

```bash
git log --oneline -5
```

Show a summary of the resulting commits to the user.

## Exception Handling

- **No Changes**: If `git status` is clean, notify the user: "No changes to commit."
- **Pre-existing Staged Files**: Respect current staged state, but notify the user.
- **Single Logical Group**: If all changes belong to a single logical group, perform a single commit (following the active Step 3 approval mode and notifying the user).
- **Merge Conflicts / Unresolved Files**: Halt execution, notify the user, and request manual resolution.

## Exclusions

- **Ephemeral Design, Plan & Scratch Artifacts**: Working design specs, implementation plans, and temporary files under `.agents/docs/` and `.agents/scratch/` are excluded from commits unless explicitly requested by the user. Persistent project markdown files (`README.md`, `SKILL.md`, `STATE.md`, `rules/*.md`, `memory/*.md`) remain normal commit targets.
