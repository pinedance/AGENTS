---
name: my-models
description: >
  Handles model selection and switching for any skill that needs to offer the user a model change.
  Use this skill whenever a workflow step requires asking the user to select or change the active LLM model.
  Triggered by: my-new-session (Step 3), brainstorming (pre-execution model check), or any skill needing a model selection gate.
---

# My Models — Model Selection Gate

This skill provides a standardized model selection step for use inside other skills.
It is NOT a standalone session skill — it is invoked as a sub-step from `my-new-session`, `brainstorming`, and any workflow that needs a model selection gate.

---

## Why This Skill Exists

The harness does not expose a programmatic API to list available models.
The agent cannot know in advance which models are available to the user.
Therefore, the agent defers model selection to the user via the `/model` slash command,
rather than presenting a hardcoded list that may be stale or incorrect.

---

## Protocol

### Step 1: Ask if the user wants to change the model

Use `ask_question` if available:

- **Question**: "Would you like to change the active model before we proceed?"
- **Options**:
  - `(Recommended) Keep using the current model — proceed`
  - `I want to change the model — I'll use /model to switch`

If the user selects **Keep**: proceed immediately to the next step in the calling skill.

If the user selects **Change model**:

### Step 2: Instruct the user to switch using /model

Display this message (do NOT compress into caveman — model switching is a critical multi-step UI action):

> **To change the model:**
> 1. Type `/model` in the chat input and press Enter
> 2. Select your desired model from the list
> 3. Once switched, reply **"done"** (or any message) to continue

Then **stop calling tools and wait** for the user's next message. Do not proceed until the user replies.

### Step 3: Resume

When the user replies (any message), acknowledge the model change and immediately
hand control back to the calling skill's next step. Do not ask again.

---

## Usage Pattern for Calling Skills

When invoking this skill from another skill, insert it as an explicit named step:

```
**Model Selection Gate**: Invoke my-models skill protocol before proceeding.
Wait for user response before continuing to next step.
```

---

## Notes

- Never hardcode a specific model list — the available models depend on the user's
  account, region, and harness version.
- The `/model` slash command is user-facing only; the agent cannot execute it.
- If `ask_question` is unavailable, display the question as plain text and wait for reply.
- This protocol is idempotent — if the user says "done" without switching, that is fine.
