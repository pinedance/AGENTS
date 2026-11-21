# Prompt Authoring & Editing Rules

This document defines authoring and editing standards for agent instructions (`prompts/*.md`), skills (`skills/*/SKILL.md`), and user-facing interactive prompts.

---

## 1. User-Facing Prompts & Options (Headline Style)

- **Headline Format (`[subject/state] + [decision]?`)**: Write hardcoded user-facing questions (`ask_question` prompts) as concise noun-phrase headlines without polite filler or redundant lead-ins. Do not restate context already printed immediately above (e.g., `git status --short`).
- **Concise Options with Dispatch Tokens Preserved**: Shorten option labels for fast terminal scanning while preserving exact downstream mode/branch dispatch keywords (e.g., `my-git-commit`, `Single-Unit`, `Merge locally`, `Keep`, `Push`, `Push & create PR`, `Discard`) so later steps match unambiguously.
- **Ban Lossy Over-Compression**: Never collapse prompts into context-free single words (e.g., `"커밋?"`, `"push?"`) that drop scope or mode. Over-compression yields negligible token savings while risking expensive re-clarification turns and weakening conversation-history grounding.
- **Mandatory Full-Sentence Exceptions**: Keep clear full sentences for irreversible/destructive confirmations (`Discard`, `--force`, `rm -rf`, hard resets, permanent deletion) and ambiguous scope/requirements interviews.
- **Examples**:
  - Good: `"미커밋 변경 처리?"` / `"브랜치(<branch>) 마무리 방법?"` / `"<base-branch> 원격 push?"`
  - Bad (verbose): `"작업 시작 전 커밋되지 않은 변경사항이 발견되었습니다. 어떻게 처리할까요?"`
  - Bad (lossy): `"커밋?"` / `"push?"`
