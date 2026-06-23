---
name: my-coding-guidelines
description: Defines the project's core coding principles, architectural standards, naming conventions, and code quality guidelines. Referenced by workspace automation and code review skills.
---

# My Coding Guidelines

This skill defines the core development principles, coding style, naming conventions, and documentation standards for this project. All code implementation, refactoring, and code review processes must adhere to these guidelines.

---

## 1. Architecture & Design Principles

*   **Single Source of Truth (SSoT)**: Maintain a single, unambiguous representation of data, logic, and configuration to prevent duplication and inconsistency.
*   **Principle of Least Surprise**: Maintain architectural and design consistency with the existing codebase to ensure predictable behavior.
*   **Single Responsibility Principle (SRP)**: Restrict each module, class, and function to a single logical responsibility.
*   **Loose Coupling**: Minimize dependencies between modules; prevent components from accessing or knowing internal states of others.
*   **Dependency Inversion (DIP)**: Decouple business logic from concrete external resources (e.g., databases, networks) using interfaces and dependency injection to enable isolated unit testing.

---

## 2. Error Handling & Reliability

*   **Fast-Fail (for Programming Errors)**: Halt execution immediately (e.g., by throwing exceptions) upon encountering invalid arguments, incorrect types, or invalid internal states at entry points to prevent corrupted state propagation.
*   **Graceful Operational Error Handling**: Wrap volatile operational tasks (e.g., network, database, I/O) in try-catch blocks to handle or propagate failures gracefully without collapsing the application state.
*   **Exception Swallowing Prevention**: Ban empty catch blocks or over-broad catches (e.g., `catch (Exception e)`) that mask unexpected runtime bugs.
*   **Explicit Failure over Silent Fallbacks**: Reject returning ambiguous default values (e.g., `null`, `-1`) on failure if they cannot be distinguished from valid successful states.
*   **Stack Trace Preservation**: Preserve the original stack trace and context when re-throwing or wrapping exceptions.
*   **Minimal Try-Catch Scope**: Keep try blocks minimal and focused to prevent wrapping unrelated lines and masking distinct errors.
*   **Defensive Design (for Boundary States)**: Handle valid but extreme boundary conditions (e.g., empty collections, null/undefined inputs, off-by-one limits) gracefully at boundaries to prevent unexpected runtime crashes.

---

## 3. Coding Style & Clean Code

*   **Explicit Typing**: Ban magic code, implicit conversions, or dynamic type tricks. Enforce strict typing and explicit declarations.
*   **Pure Functions First**: Prioritize pure, stateless functions with no side effects to ensure thread-safety and predictability.
*   **Early Return / Guard Clauses**: Limit logical nesting to a maximum of 2 levels. Use early returns and guard clauses to enhance readability.
*   **Function Size Limit**: Limit functions to a maximum of 30–40 lines. Scrutinize and refactor functions exceeding this threshold.
*   **Single Level of Abstraction Principle (SLAP)**: Ensure a single function orchestrates logic at a uniform level of abstraction; do not mix high-level orchestration with low-level implementation details.
*   **Constants over Magic Values**: Replace raw literals (numbers, strings) in logic with descriptive named constants.
*   **Dead Code Elimination**: Remove unreachable branches, unused variables, functions, and imports immediately.
*   **Top-Level Imports**: Ban inline imports inside functions or classes. Place all module imports at the very top of the file to maintain clear visibility of dependencies.
*   **No Nested Functions**: Ban declaring nested helper functions inside another function. Extract them as module-level functions with explicit parameters to ensure testability and readability.
*   **Layer-Based Layout**: Organize code blocks sequentially within a file based on their logical abstraction layer and execution flow (e.g., Constants/Regex -> Utility Helpers -> Pre-processing -> Generation/Core -> Post-processing -> Orchestration/Main). Ensure the file reads naturally from top to bottom.

---

## 4. Naming Conventions

*   **Hierarchical Naming (Left-to-Right)**: Group related variables/constants by prefixing them hierarchically (e.g., `price_daily`, `price_monthly`, `user_total`).
*   **Verb-Noun Convention**: Prefix functions and methods with an action verb (e.g., `calculate_total`, `fetch_user`).
*   **Standardized Abbreviations**: Use only universally understood abbreviations (e.g., `calc`, `init`, `config`, `stats`, `db`, `err`). Ban custom abbreviations.
*   **Structural Self-Documentation**: Reveal intent through clear names and hierarchy. Ban filler or vague words (e.g., `data`, `info`, `temp`, `my`, `value`) unless mandated by external APIs.
*   **Boolean Prefix Convention**: Prefix boolean variables, functions, and properties with status verbs (e.g., `is_`, `has_`, `can_`, `should_`).
*   **Symmetric Antonyms**: Use matching antonym pairs for opposing concepts (e.g., `open/close`, `start/stop`, `get/set`, `enable/disable`).
*   **Plural Collections**: Use plural nouns for arrays, lists, maps, and sets (e.g., `users`, `items`, `user_map`).

---

## 5. Documentation

*   **Document the "Why", Not the "What"**: Rely on self-documenting code structure and naming to explain *what* the code does. Use comments and docstrings solely to document *why* a specific approach, design constraint, or business logic was chosen.
