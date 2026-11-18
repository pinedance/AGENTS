---
name: my-plan-execute
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the my-plan-execute skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. **Branch Safety Check**: Ensure an active task branch per `my-sess-open` / `AGENTS.md` SSoT (if invoked standalone on `main`/`master` or an unrelated prior branch, automatically create `git checkout -b <prefix>/<slug> <base-branch>` without asking before executing plan tasks).
3. Review critically - identify any questions or concerns about the plan
4. If concerns: Raise them with your human partner before starting
5. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Verification Report & User Completion Gate

After all tasks in the current plan pass verification:
- **Do NOT auto-commit and do NOT auto-invoke `my-sess-close`.** Output a concise verification summary with command evidence and **wait for the user's completion declaration**.
- Once the user declares completion (or next-phase transition / `/my-sess-close`), follow `AGENTS.md` SSoT (`Autonomous Context-Driven Multi-Commit` + `Phase Boundary Gate`: mark `[x]` in `macro-plan.md` and recommend `/compact` if `[ ]` phases remain, or guide toward [my-sess-close](../my-sess-close/SKILL.md) on final/standalone completion).

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - Ensures isolated workspace (creates one or verifies existing)
- **[my-plan-write](../my-plan-write/SKILL.md)** - Creates the plan this skill executes
- **[my-sess-close](../my-sess-close/SKILL.md)** - User-triggered (or user-guided) session wrap-up after final Phase / standalone completion per `AGENTS.md` SSoT
- **my-git-commit** - Fallback commit analyzer (SSoT for message rules and exclusions) invoked after user completion declaration when conversation context is insufficient
