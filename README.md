# AGENTS - AI Agent Skill Manager

A utility for efficiently managing and synchronizing common Skills that can be immediately used in AI Agents (such as Claude Code, Gemini CLI, etc.). This repository centers around the `manager.py` script, which retrieves required Skills from remote GitHub repositories and links them to the global agent directory (`~/.agents/skills/`).

---

## ⚙️ Architecture & Workflow

1. **Remote Repository Download**: Download repository zip files from GitHub to `.skills-repos/`.
2. **Library Extraction**: Extract directories containing `SKILL.md` from the downloaded zip files to the local cache directory `skills-library/`.
3. **Global Symlink Connection**: Create symbolic links for workspace-enabled skills in the system default agent directory `~/.agents/skills/`. This allows agent tools across all projects to reference them.

---

## 🚀 Quick Start

### 1. Requirements
This utility requires Python 3.11 or higher. Using the `uv` package manager is highly recommended.

```bash
# Install dependencies
uv sync
```

### 2. Configuration (`.skills.yaml`)
Define your skill library and active workspace configurations in the `.skills.yaml` file in the project root.

```yaml
library:
  - repoId: obra/superpowers
    commit: 6fd4507659784c351abbd2bc264c7162cfd386dc
    skills:
      - name: brainstorming
        path: skills/brainstorming/SKILL.md
      - name: executing-plans
        path: skills/executing-plans/SKILL.md

workspace:
  - repoId: obra/superpowers
    skills:
      - name: brainstorming
        source: obra/superpowers/brainstorming
        target: sp-brainstorming
```

---

## 🛠️ CLI Usage (`manager.py`)

Run the tool using `uv run manager.py <command>`.

### 1. Sync (`sync`)
Synchronizes the local filesystem with the `.skills.yaml` configuration. It downloads/extracts remote repository files and links/prunes workspace skills in `~/.agents/skills/`.

```bash
uv run manager.py sync
```
* **Optimized Sync**: Uses the Git Commit ID stored in the zip file's comment field. If the commit hash has not changed, it skips the extraction process.
* **Safe Pruning**: Only unlinks stale symlinks created by *this* project in the global `~/.agents/skills/` directory. It does not touch files, directories, or symlinks belonging to other projects.

---

### 2. Library Management (`library`)

Manage the remote GitHub repositories cached in your local library.

* **Add Repository (`add`)**
  Adds a remote repository to your configuration. If the zip file already exists in local cache, it skips the download.
  ```bash
  uv run manager.py library add <owner/repo>
  # Example: uv run manager.py library add obra/superpowers
  ```

* **Remove Repository (`remove`)**
  Removes the repository from the configuration and unlinks its active workspace skills.
  ```bash
  uv run manager.py library remove <owner/repo>
  ```

* **Update Library (`update`)**
  Deletes cached zip files and forces a clean download of the latest zip files from GitHub.
  ```bash
  # Update a specific repository
  uv run manager.py library update <owner/repo>
  
  # Update all repositories in the library
  uv run manager.py library update
  ```

---

### 3. Workspace Management (`workspace`)

Manage which skills are active and symlinked in the global folder `~/.agents/skills/`.

* **Add Workspace Skill (`add`)**
  Symlinks a skill from the library to the global directory.
  ```bash
  uv run manager.py workspace add <skill_name> [--name <custom_symlink_name>]
  # Example: uv run manager.py workspace add brainstorming --name sp-brainstorming
  ```
  *If a symlink with the same target name already exists but is a broken symlink, it is safely unlinked and overwritten. Active symlinks pointing to other destinations will raise a `ValueError` collision conflict.*

* **Remove Workspace Skill (`remove`)**
  Removes the skill from the workspace configuration and deletes its symlink.
  ```bash
  uv run manager.py workspace remove <skill_name>
  ```

---

## 🧪 Testing

Run pytest to verify the codebase integrity.

```bash
PYTHONPATH=. uv run pytest
```