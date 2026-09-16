---
name: feature-dev
description: >-
  A comprehensive, structured 7-phase workflow for feature development:
  discovery, codebase exploration, clarifying questions, architecture design,
  implementation, quality review, and summary. Use this skill when the user
  wants to build a new feature, implement a significant change, or follow a
  structured development workflow. Especially useful for changes that touch
  multiple files, require architectural decisions, or have somewhat unclear
  requirements.
---

# Feature Development Workflow

A systematic 7-phase approach to building new features. Instead of jumping
straight into code, this workflow guides through understanding the codebase,
asking clarifying questions, designing architecture, and ensuring quality.

## Core Principles

- **Ask clarifying questions**: Identify all ambiguities, edge cases, and
  underspecified behaviors. Ask specific, concrete questions rather than making
  assumptions. Wait for user answers before proceeding.
- **Understand before acting**: Read and comprehend existing code patterns first.
- **Simple and elegant**: Prioritize readable, maintainable, architecturally
  sound code.
- **Track progress**: Use task lists to track all progress throughout.

---

## Phase 1: Discovery

**Goal**: Understand what needs to be built.

1. If the feature request is unclear, ask the user:
   - What problem are they solving?
   - What should the feature do?
   - Any constraints or requirements?
2. Summarize understanding and confirm with user.

---

## Phase 2: Codebase Exploration

**Goal**: Understand relevant existing code and patterns.

Use the **code-explorer** skill approach:
1. Explore 2–3 different aspects of the codebase in relation to the feature:
   - Similar existing features and their implementations
   - Architecture and abstractions in the relevant area
   - Current implementation of related functionality
2. Identify 5–10 key files to read for deep understanding.
3. Present comprehensive summary of findings and patterns discovered.

---

## Phase 3: Clarifying Questions

**Goal**: Fill in gaps and resolve all ambiguities before designing.

**CRITICAL — DO NOT SKIP THIS PHASE.**

1. Review the codebase findings and original feature request.
2. Identify underspecified aspects:
   - Edge cases and error handling
   - Integration points and scope boundaries
   - Design preferences and backward compatibility
   - Performance requirements
3. **Present all questions in a clear, organized list.**
4. **Wait for answers before proceeding to architecture design.**

---

## Phase 4: Architecture Design

**Goal**: Design implementation approaches with different trade-offs.

Use the **code-architect** skill approach:
1. Consider 2–3 approaches with different focuses:
   - **Minimal changes**: Smallest change, maximum reuse
   - **Clean architecture**: Maintainability, elegant abstractions
   - **Pragmatic balance**: Speed + quality
2. Form an opinion on which fits best for this specific task.
3. Present to user: brief summary, trade-offs, **your recommendation**.
4. **Ask user which approach they prefer.**

---

## Phase 5: Implementation

**Goal**: Build the feature.

**DO NOT START WITHOUT USER APPROVAL.**

1. Wait for explicit user approval of the chosen approach.
2. Read all relevant files identified in previous phases.
3. Implement following chosen architecture.
4. Follow codebase conventions strictly.
5. Write clean, well-documented code.
6. Update progress as you go.

---

## Phase 6: Quality Review

**Goal**: Ensure code is simple, DRY, elegant, and functionally correct.

Use the **code-reviewer** skill approach:
1. Review with different focuses:
   - Simplicity / DRY / elegance
   - Bugs / functional correctness
   - Project conventions / abstractions
2. Consolidate findings and identify highest severity issues.
3. **Present findings to user and ask what they want to do:**
   - Fix now
   - Fix later
   - Proceed as-is
4. Address issues based on user decision.

---

## Phase 7: Summary

**Goal**: Document what was accomplished.

1. Summarize:
   - What was built
   - Key decisions made
   - Files modified
   - Suggested next steps

---

## When to Use This Workflow

**Use for:**
- New features that touch multiple files
- Features requiring architectural decisions
- Complex integrations with existing code
- Features where requirements are somewhat unclear

**Don't use for:**
- Single-line bug fixes
- Trivial changes
- Well-defined, simple tasks
- Urgent hotfixes
