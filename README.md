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
status
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
      │
      ▼
[5] Manifest ──→ ~/.agents/skills.json & ~/.gemini/config/skills.json (symlink)
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
  - repoId: LOCAL/skills
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
  - repoId: LOCAL/skills
    skills:
      - name: my-code-review
        source: skills/my-code-review
        target: my-code-review
```

---

## 🛠️ CLI Usage

Run the tool using the `uv run <command>` shortcut.

### 1. Sync (`sync`)
Synchronizes the local filesystem with `.skills.yaml` and global settings (`settings.default.yaml` / optional `settings.yaml`). It downloads/extracts remote repository files, links/prunes workspace skills in `~/.agents/skills/`, and updates global symlinks (`~/.agents/{AGENTS.md,memory,prompts,rules}` and `~/.gemini/config/skills.json`).

```bash
uv run sync
# Warn if pinned commits in .skills.yaml lag behind remote HEAD (informational; use 'library update' to re-download)
uv run sync --check-remote
```
* **Optimized Sync**: Uses the Git Commit ID stored in the zip file's comment field. If the commit hash has not changed, it skips the extraction process. Skip completely for `LOCAL/*` repositories.
* **Safe Pruning**: Only unlinks stale symlinks created by *this* project in the global `~/.agents/skills/` directory. It does not touch files, directories, or symlinks belonging to other projects.
* **Dynamic allowed_bases**: Restricts symlinking boundaries to `skills-library` and any local root folders (e.g., `skills/`) registered under `LOCAL/*` repository configurations.

---

### 2. Library Management (`library`)

Manage the remote GitHub repositories cached in your local library or scan local custom skill directories.

* **Add Repository (`add`)**
  Adds a remote GitHub repository or scans a local custom directory to your configuration.
  ```bash
  # Add remote GitHub repository
  uv run library add <owner/repo>
  # Example: uv run library add obra/superpowers

  # Add/Scan local skill directory (e.g. skills/)
  uv run library add LOCAL/<dir_name>
  # Example: uv run library add LOCAL/skills
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

### 4. Local Custom Skill Lifecycle (`LOCAL/skills`)

1. **Add & Activate a New Local Skill**:
   - Create `skills/<skill_name>/SKILL.md` (frontmatter `name:` defines the skill name; defaults to directory name if omitted).
   - Scan and register to library, then activate in workspace (pass `--name` for non-interactive automation):
     ```bash
     uv run library add LOCAL/skills
     uv run workspace add <skill_name> --name <skill_name>
     ```
2. **Edit an Existing Local Skill**:
   - Edit `skills/<skill_name>/SKILL.md` directly (live via symlink). Run `uv run library add LOCAL/skills` if frontmatter `name:` or `skills/` directory entries changed (re-scans into `.skills.yaml` and syncs); run `uv run sync` after direct `.skills.yaml` edits.
3. **Deactivate Only (Keep Source Files)**:
   - Unlink from `~/.agents/skills/` and remove from `workspace:` while keeping `skills/<skill_name>/` and the `library:` entry:
     ```bash
     uv run workspace remove <skill_name>
     ```
4. **Permanently Delete an Individual Local Skill**:
   - `library remove LOCAL/skills` removes the entire `LOCAL/skills` directory group. To delete a single skill inside `skills/`, deactivate it, delete its directory, and re-scan `LOCAL/skills` to prune its `library:` entry from `.skills.yaml` and sync manifests:
     ```bash
     uv run workspace remove <skill_name>
     rm -rf skills/<skill_name>
     uv run library add LOCAL/skills
     ```
5. **Rename an Existing Local Skill**:
   - Deactivate the old symlink, rename the directory, update `name:` in `SKILL.md`, refresh `LOCAL/skills`, and activate the new symlink:
     ```bash
     uv run workspace remove <old_name>
     git mv skills/<old_name> skills/<new_name>
     # Update 'name: <new_name>' in skills/<new_name>/SKILL.md frontmatter
     uv run library add LOCAL/skills
     uv run workspace add <new_name> --name <new_name>
     ```

---

### 5. Status Check (`status`)

Show the current state of repositories, libraries, and active workspace symlinks.

```bash
uv run status
```

* **Remote Repositories**: Compares the local cached zip comment hashes with remote commit hashes fetched via `git ls-remote` to determine if an update is required.
* **Skills Library**: Lists available skills in the library, grouped by repository (displaying paths for the `LOCAL` repo).
* **Workspace Symlinks**: Lists active symlinks in `~/.agents/skills/` and tags broken symlinks with `[BROKEN]`.



---

## 🧪 Testing

Run pytest to verify the codebase integrity.

```bash
uv run pytest
```