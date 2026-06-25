---
name: my-skill-updater
description: Automates updating, refactoring, and refining existing agent skills (SKILL.md documents) in the workspace customization root.
---

# My Skill Updater

This skill defines the protocol for updating and refining existing coding guidelines or other workspace agent skills (`SKILL.md` files). It ensures updates are concise, logically structured, and formatted using LLM-native technical jargon.

---

## 1. Analysis & Pre-requisites

*   **Target Read**: Always read the existing `SKILL.md` file using `view_file` before suggesting or performing any modifications.
*   **Style & Language Consistency**: Detect the dominant language (English/Korean) and formatting patterns of the target file. All additions must match these exactly.
*   **Skip Duplicates (DRY)**: Scan for existing guidelines that already cover the user's request. Skip or merge instead of adding duplicate items.

---

## 2. Abstraction & Rephrasing

*   **LLM-Native Jargon**: Translate conversational or verbose human instructions into precise, high-density industry standard terms (e.g., *SRP*, *YAGNI*, *SLAP*, *Fail-Fast*, *SSoT*, *DIP*, *Exception Swallowing*, *Pure Functions*).
*   **Conciseness over Explanation**: Minimize prose. AI models understand standard software engineering terms directly. Write rules as actionable constraints, not tutorials.

---

## 3. Cohesive Insertion & Editing

*   **Logical Mapping**: Do not append new rules to the bottom of the file by default. Analyze the document structure and insert the rules into the most appropriate thematic section (e.g., *Architecture*, *Clean Code*, *Naming Conventions*).
*   **Precise replacement**: Use `replace_file_content` to swap existing lines rather than overwriting the entire file, reducing diff footprints and preserving git history.
