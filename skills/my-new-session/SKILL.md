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
3. **Harness Question-Answering Guidelines**:
   - Whenever you need to ask for user input, preference, or confirmation (e.g., confirming task name, committing changes, syncing remote, checking out branch), check if the `ask_question` tool is available in your tool declaration.
   - If `ask_question` is available, **always use it** instead of relying solely on plain text questions.
   - Design options that represent the user's direct response (e.g., "(Recommended) Yes, create and switch to branch '<task-name>'").
   - The UI automatically provides a write-in ("Other") option, so the user can type a custom response if none of the suggested choices fit.

---

## Step 2: Prepare Git Repository

Perform the following git workspace checks and operations:

1. **Check for Uncommitted Changes**:
   - Run `git status --porcelain` to check if there are uncommitted modifications.
   - If there are uncommitted changes, ask the user what to do. If the `ask_question` tool is available, use it with options like:
     - `(Recommended) Commit the changes first`
     - `Stash the changes`
     - `Proceed without committing`
   - If they choose to commit, write a clear, conventional commit message and commit the changes.

2. **Check for Remote Sync (Pull & Push)**:
   - Check if the repository has a remote configured (`git remote`).
   - If a remote exists:
     - Fetch remote branch state (`git fetch`) or run `git status -uno` to see if the branch is ahead or behind.
     - **If local is ahead of remote**: The local repository has newer commits that need to be pushed. Offer to run `git push`.
     - **If local is behind remote**: The remote has newer commits. Offer to run `git pull`.
     - If the `ask_question` tool is available, present the appropriate synchronization options based on the sync status:
       - `(Recommended) Push local changes to remote` (if local is ahead)
       - `(Recommended) Pull remote changes to local` (if local is behind)
       - `Sync both (pull then push)` (if applicable)
       - `Skip sync and proceed`
     - Run the approved command (`git push`, `git pull`, or both) depending on the user's selection.

3. **Checkout Task Branch**:
   - Recommend creating and switching to a new branch for the task: `git checkout -b <task-name>`.
   - If the `ask_question` tool is available, use it to confirm the checkout:
     - `(Recommended) Create and switch to '<task-name>' branch`
     - `Keep working on the current branch`
   - If approved, run the command to checkout the branch.

---

## Step 3: Configure Communication Style & Session Settings

1. **Activate Caveman Mode**:
   - Check if the `/caveman` slash command or the `caveman` skill is available in the current environment.
   - If available, automatically run the command:
     ```
     /caveman full Korean
     ```
     to switch communication style to Korean Caveman Mode as preferred by the user.
2. **Model Selection**:
   - Ask the user whether they want to change the active model before starting work.
   - If the `ask_question` tool is available, use it to check if they want to change the model, and if so, what they want to change it to. Example question & options:
     - **Question**: "Would you like to change the model before we begin?"
     - **Options**:
       - `(Recommended) Keep using the current model`
       - `Change model to Gemini 1.5 Pro`
       - `Change model to Gemini 1.5 Flash`
       - `Change model to Gemini 3.5 Flash (High)`
3. **Apply Other Custom Session Settings**:
   - Verify and apply any other session-start configurations, workspace preferences, or automation tools as requested by the user.
4. **Response & Execution Strategy**:
   - If the user asks a question, answer it fully and propose relevant actions.
   - **CRITICAL**: Do not begin modifying the codebase or writing code changes without explicit, direct approval from the user.

---

## Step 4: Core Development Principles

Always adhere to the core development principles defined in the [my-coding-guidelines](../my-coding-guidelines/SKILL.md) skill. Ensure that all codebase modifications, architecture designs, naming patterns, and error handling mechanisms conform strictly to those guidelines.
---

## Example Interaction Flow

### Example 1: Starting a session with uncommitted changes & unpushed commits

1. **Agent**: Let's get your new session started! Could you please briefly describe the task you want to work on?
2. **User**: I want to optimize the database query latency for the dashboard.
3. **Agent**: 
   - Generates a task name: `optimize-db-latency`.
   - Runs `git status --porcelain` and finds uncommitted changes in `src/db.py`.
   - Calls `ask_question`:
     - **Question**: "I found uncommitted changes in [db.py](file:///absolute/path/to/src/db.py). How would you like to handle them?"
     - **Options**:
       - `(Recommended) Commit the changes first`
       - `Stash the changes`
       - `Proceed without committing`
4. **User** selects: `Commit the changes first` (or writes a custom message)
5. **Agent**: 
   - Runs `git commit` with a conventional message.
   - Runs `git status` or `git cherry -v` and finds that the local branch is ahead of the remote repository by 1 commit.
   - Calls `ask_question`:
     - **Question**: "Your local branch is ahead of the remote repository. Would you like to push the changes?"
     - **Options**:
       - `(Recommended) Push local changes to remote`
       - `Skip sync and proceed`
6. **User** selects: `Push local changes to remote`
7. **Agent**:
   - Runs `git push`
   - Calls `ask_question` to confirm branch checkout:
     - **Question**: "I recommend switching to a new branch for this task. Shall I create and checkout to branch `optimize-db-latency`?"
     - **Options**:
       - `(Recommended) Create and switch to 'optimize-db-latency' branch`
       - `Keep working on the current branch`
8. **User** selects: `Create and switch to 'optimize-db-latency' branch`
9. **Agent**:
   - Runs `git checkout -b optimize-db-latency`
   - Activates caveman mode: `/caveman full Korean`
   - Calls `ask_question` to ask about model selection:
     - **Question**: "Would you like to change the model before we begin?"
     - **Options**:
       - `(Recommended) Keep using the current model`
       - `Change model to Gemini 1.5 Pro`
       - `Change model to Gemini 1.5 Flash`
       - `Change model to Gemini 3.5 Flash (High)`
