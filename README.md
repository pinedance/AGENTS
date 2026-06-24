# AGENTS - AI Agent Skill Manager

A utility for efficiently managing and synchronizing common Skills that can be immediately used in AI Agents (such as Claude Code, Gemini CLI, etc.). This utility retrieves required Skills from remote GitHub repositories or links them directly from local directories (for custom developer skills) and links them to the global agent directory (`~/.agents/skills/`).

---

## ⚙️ Architecture & Workflow

### Data Flow

```
1. REMOTE REPOS WORKFLOW:
┌─────────────────────────────────────────────────────┐
│  [Remote]  GitHub Repository                        │
│            https://github.com/<owner>/<repo>        │
└─────────────────────────────────────────────────────┘
                          │
                Remote Repository Download
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  [Local]   .skills-repos/                          │
│            └── <owner>/<repo>.zip                   │
└─────────────────────────────────────────────────────┘
                          │
                   Library Extraction
             "library add" / "library remove"
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  [Local]   skills-library/                         │
│            └── <owner>/<repo>/                      │
│                └── <skill-name>/                    │
│                    ├── SKILL.md                     │
│                    └── ...                          │
└─────────────────────────────────────────────────────┘
                          │
              Global Symlink Connection
            "workspace add" / "workspace remove"
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  [Local]   ~/.agents/skills/                       │
│            └── <skill-name>  ──▶  (symlink)        │
└─────────────────────────────────────────────────────┘

2. LOCAL REPO WORKFLOW:
┌─────────────────────────────────────────────────────┐
│  [Local]   skills/ or skills-new/ (Direct Edit)     │
│            └── <skill-name>/                        │
│                └── SKILL.md                         │
└─────────────────────────────────────────────────────┘
                          │
             Direct Symlink Connection
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│  [Local]   ~/.agents/skills/                       │
│            └── <skill-name>  ──▶  (symlink)        │
└─────────────────────────────────────────────────────┘
```

### CLI Commands

```
sync
library
├── add <owner/repo>
├── remove <owner/repo>
└── update [owner/repo]
workspace
├── add <skill_name> [--name <alias>]
└── remove <skill_name>
```

### `sync` Pipeline

```
.skills.yaml
      │
      ▼
[1] Download ──→ .skills-repos/*.zip            (skip if commit unchanged; skip for LOCAL repo)
      │
      ▼
[2] Extract  ──→ skills-library/<repo>/<skill>  (skip if commit unchanged; skip for LOCAL repo)
      │
      ▼
[3] Prune        stale zips · stale library dirs · broken symlinks
      │
      ▼
[4] Symlink  ──→ ~/.agents/skills/<skill>       (collision check · safe prune · allowed_bases check)
```

---

## 🚀 Quick Start

### 1. Requirements
This utility requires Python 3.11 or higher. Using the `uv` package manager is highly recommended.

```bash
# Install dependencies and build shortcut scripts
uv sync
```

### 2. Configuration (`.skills.yaml`)
Define your skill paths, libraries, and active workspace configurations in the `.skills.yaml` file in the project root.

```yaml
paths:
  library: skills-library

library:
  - repoId: obra/superpowers
    commit: 6fd4507659784c351abbd2bc264c7162cfd386dc
    skills:
      - name: brainstorming
        path: skills/brainstorming/SKILL.md
      - name: executing-plans
        path: skills/executing-plans/SKILL.md
  
  # Local repository configuration
  - repoId: LOCAL
    skills:
      - name: my-code-review
        path: skills/my-code-review/SKILL.md

workspace:
  - repoId: obra/superpowers
    skills:
      - name: brainstorming
        source: obra/superpowers/brainstorming
        target: sp-brainstorming
  
  # Workspace mapping for local skills (resolves relative to PROJECT_ROOT)
  - repoId: LOCAL
    skills:
      - name: my-code-review
        source: skills/my-code-review
        target: my-code-review
```

---

## 🛠️ CLI Usage

Run the tool using the `uv run <command>` shortcut.

### 1. Sync (`sync`)
Synchronizes the local filesystem with the `.skills.yaml` configuration. It downloads/extracts remote repository files and links/prunes workspace skills in `~/.agents/skills/`.

```bash
uv run sync
```
* **Optimized Sync**: Uses the Git Commit ID stored in the zip file's comment field. If the commit hash has not changed, it skips the extraction process. Skip completely for the `LOCAL` repository.
* **Safe Pruning**: Only unlinks stale symlinks created by *this* project in the global `~/.agents/skills/` directory. It does not touch files, directories, or symlinks belonging to other projects.
* **Dynamic allowed_bases**: Restricts symlinking boundaries to `skills-library` and any local root folders (e.g., `skills/`) registered under the `LOCAL` repository configuration.

---

### 2. Library Management (`library`)

Manage the remote GitHub repositories cached in your local library.

* **Add Repository (`add`)**
  Adds a remote repository to your configuration. If the zip file already exists in local cache, it skips the download.
  ```bash
  uv run library add <owner/repo>
  # Example: uv run library add obra/superpowers
  ```

* **Remove Repository (`remove`)**
  Removes the repository from the configuration and unlinks its active workspace skills.
  ```bash
  uv run library remove <owner/repo>
  ```

* **Update Library (`update`)**
  Deletes cached zip files and forces a clean download of the latest zip files from GitHub.
  ```bash
  # Update a specific repository
  uv run library update <owner/repo>
  
  # Update all repositories in the library
  uv run library update
  ```

---

### 3. Workspace Management (`workspace`)

Manage which skills are active and symlinked in the global folder `~/.agents/skills/`.

* **Add Workspace Skill (`add`)**
  Symlinks a skill from the library (or from local directory if `LOCAL` repo is used) to the global directory.
  ```bash
  uv run workspace add <skill_name> [--name <custom_symlink_name>]
  # Example: uv run workspace add brainstorming --name sp-brainstorming
  ```
  *If a symlink with the same target name already exists but is a broken symlink, it is safely unlinked and overwritten. Active symlinks pointing to other destinations will raise a `ValueError` collision conflict.*

* **Remove Workspace Skill (`remove`)**
  Removes the skill from the workspace configuration and deletes its symlink.
  ```bash
  uv run workspace remove <skill_name>
  ```

---

## 🧪 Testing

Run pytest to verify the codebase integrity.

```bash
uv run pytest
```