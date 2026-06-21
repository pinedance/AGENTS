# Personal Skill Management & Sync Workflow Documentation

This document explains the architecture, design principles, and automated workflow for managing personal AI Agent skills in this repository. Future agents must read and follow this guide to understand how skills are developed and synchronized.

---

## 1. Directory Structure & Symlink Architecture

To ensure all skills behave consistently, even personal skills must follow the remote-first SSoT (Single Source of Truth) architecture:

```
[my skills SSoT] (Local Source)
~/Labs/AGENTS/skills/ <skill_name>
       │
   git push
       ▼
[GitHub Remote] (Absolute SSoT)
https://github.com/pinedance/AGENTS
       │
  zip download (by manager.py sync)
       ▼
[Global skills SSoT] (Build Target)
~/Labs/AGENTS/skills-library/pinedance/AGENTS/<skill_name>
       │
    symlink
       ▼
[System Core Skills]
~/.agents/skills/<skill_name>
       │
    symlink
       ▼
[Project-level Skills]
proj/.agents/skills/<skill_name>
```

- **Ephemeral Path**: Editing a skill inside a project (`proj/.agents/skills/...`) directly mutates the extracted global library folder (`skills-library/pinedance/AGENTS/...`) via the symlink chain.
- **Local Source of Truth**: The original, trackable files belong to `skills/` in the local `AGENTS` repository.

---

## 2. Dynamic Versioning with `commit: latest`

To avoid entering a recursive "chicken-and-egg" git commit loop where updating `.skills.yaml` with a commit hash produces a new commit hash, we use the `latest` dynamic tag:

```yaml
library:
- repoId: pinedance/AGENTS
  commit: latest
```

- When running `sync`, `manager.py` dynamically queries the remote GitHub default branch HEAD using `git ls-remote` and compares it against the local ZIP comments.
- Overwrite protection logic inside `manager.py` guarantees that `"latest"` is never overwritten with static hashes in `.skills.yaml` during configuration updates or network failures.

---

## 3. The Sync-Back & Publish Loop (`myskills`)

When a skill is modified inside a project folder, the changes are local to the extracted library. To easily publish these changes without manual copying/pasting, run the following command in the `AGENTS` repository:

```bash
uv run manager.py myskills -m "Conventional commit message"
```

### Behind the Scenes:
1. **Auto-Detection**: `manager.py` parses `git remote get-url origin` to identify if the current local repo matches `.skills.yaml` (e.g. `pinedance/AGENTS`).
2. **Reverse Sync (Import)**: It runs `filecmp.dircmp` to compare files in the extraction folder (`skills-library/pinedance/AGENTS/<skill>`) against the local source (`skills/<skill>`). It propagates all file additions, edits, and deletions back to the source directory (`skills/`).
3. **Library Revert**: It deletes `skills-library/pinedance/AGENTS/` to discard local uncommitted file footprints from the library directory.
4. **Git Commit & Push**: It stages `skills/`, commits the changes, and pushes them to GitHub.
5. **Auto-refresh**: It runs `sync()`, which resolves the new remote HEAD commit, downloads the fresh ZIP containing the changes, and extracts it cleanly back to `skills-library/`.
