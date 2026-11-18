# Agent Environment SSoT & Test Isolation Rules

This document enforces path SSoT boundaries and host-environment isolation for skill management (`manager.py`) and automated tests.

---

## 1. `~/.agents/` Symlink Hub as Runtime SSoT (`1-Level` Manifest Rule)

- **Management Repo vs. Runtime Entry Point**: Treat the management repository (e.g., `~/Labs/AGENTS/`) strictly as the canonical authoring source. All agent-facing runtime paths (`AGENTS.md`, `memory/`, `prompts/`, `rules/`, `skills/`) must converge at the global symlink hub (`~/.agents/`).
- **Single Resolved Hub Entry in `skills.json`**: Vendor skill manifests (`~/.agents/skills.json`, symlinked from `~/.gemini/config/skills.json`) MUST contain only the resolved `skills_dir` entry (`{"entries": [{"path": "<resolved ~/.agents/skills>"}]}`).
  - **Ban Management Repo Paths**: Never emit source or cache directories (`~/Labs/AGENTS/skills`, `skills-library/`, etc.) into `skills.json`.
  - **Respect `1-Level` Scanner Constraint**: Antigravity scans each `entries[].path` strictly one directory deep (`<path>/<skill>/SKILL.md`). Nested cache paths (`owner/repo/<skill>`) fail discovery outside the repo, and active filtering already lives in `~/.agents/skills/` symlinks.

---

## 2. Mandatory Host-Home Sandboxing in Automated Tests

- **Always Enforce `autouse=True` `HOME` Isolation**: Any test module calling code that expands `~`, `$HOME`, `$USERPROFILE`, `$XDG_*`, or accesses global dot-directories (`~/.agents`, `~/.gemini`, `~/.claude`) MUST define a module-wide `autouse=True` fixture redirecting `HOME` and `USERPROFILE` to a `tmp_path_factory` temporary directory and clearing override environment variables (such as `SKILLS_DIR`).
- **Never Rely on Opt-In Fixtures Alone**: Relying solely on an explicit `temp_env` parameter leaves tests using plain `tmp_path` free to overwrite real host manifests or symlinks on disk.
