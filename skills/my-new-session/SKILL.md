---
name: my-new-session
description: Automates workspace and git setup at the start of a new coding session. Trigger this skill whenever starting a new task, initializing a coding session, setting up a git branch for a feature or bugfix, or when the user mentions initializing a new session.
---

# My New Session Initialization

This skill guides the agent to automatically prepare the git repository and set up the workspace at the start of a new task or coding session.

Follow the steps below in order.

---

## Step 1: Request Task Description & Generate Task Name

1. **Ask the User**: Ask the user to briefly describe the task they plan to work on (e.g., to generate appropriate branch names, task IDs, or documentation filenames).
2. **Generate Task Name**: Based on the user's response, generate a clean `task-name` using lowercase alphanumeric characters, numbers, and hyphens (e.g., `refactor-login-auth`, `fix-db-leak`). Show this name to the user.

---

## Step 2: Prepare Git Repository

Perform the following git workspace checks and operations:

1. **Check for Uncommitted Changes**:
   - Run `git status --porcelain` to check if there are uncommitted modifications.
   - If there are uncommitted changes, ask the user if they would like to commit them before starting the new session. If they agree, write a clear, conventional commit message and commit the changes.
2. **Check for Remote Sync**:
   - Check if the repository has a remote configured (`git remote`).
   - If a remote exists, ask the user if they would like to sync and pull the latest changes (`git pull`). If approved, run `git pull`.
3. **Checkout Task Branch**:
   - Recommend creating and switching to a new branch for the task:
     ```bash
     git checkout -b <task-name>
     ```
   - Ask for confirmation before running the command. If approved, checkout the branch.

---

## Step 3: Configure Communication Style & Session Settings

1. **Activate Caveman Mode**:
   - Check if the `/caveman` slash command or the `caveman` skill is available in the current environment.
   - If available, automatically run the command:
     ```
     /caveman full Korean
     ```
     to switch communication style to Korean Caveman Mode as preferred by the user.
2. **Apply Other Custom Session Settings**:
   - Verify and apply any other session-start configurations, workspace preferences, or automation tools as requested by the user.
3. **Response & Execution Strategy**:
   - If the user asks a question, answer it fully and propose relevant actions.
   - **CRITICAL**: Do not begin modifying the codebase or writing code changes without explicit, direct approval from the user.

---

## Step 4: Core Development Principles

Always adhere to the following development principles during the session:

1. **Fast-Fail Principle**:
   - Implement code that fails immediately and visibly when an error or invalid state is encountered (e.g., validate arguments early, avoid swallowing exceptions, fast-fail on critical checks). Do not hide bugs behind excessive exception handling.
2. **Single Source of Truth (SSoT) Principle**:
   - Maintain a single, unambiguous representation of data, logic, and configuration. Avoid duplicating code, settings, or states across different parts of the system. Always reference the primary source.

---

## Example Interaction Flow

### Example 1: Starting a session with uncommitted changes
```
Agent: Let's get your new session started! Could you please briefly describe the task you want to work on?

User: I want to optimize the database query latency for the dashboard.

Agent: 
I have generated a task name: `optimize-db-latency`.
Let me check your git repository status...
I found uncommitted changes in `src/db.py`. Would you like me to commit these changes first?

User: Yes, please commit them.

Agent: [Runs git commit]
Great, I committed the changes. Next, would you like me to pull the latest changes from the remote repository?

User: Yes, please.

Agent: [Runs git pull]
Done. Now, I recommend switching to a new branch for this task: `git checkout -b optimize-db-latency`. Shall I proceed with this?

User: Yes, go ahead.

Agent: [Runs git checkout -b optimize-db-latency]
We are now on the branch `optimize-db-latency`.
Activating caveman mode...
/caveman full Korean
```
