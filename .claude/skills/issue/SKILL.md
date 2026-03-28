---
name: issue
description: Create a GitHub issue for tracking work. Use when the user says "issue", "create issue", "new issue", or wants to file a bug, feature request, or improvement.
allowed-tools: Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh label list:*), Bash(git log:*), Read, Grep, Glob, AskUserQuestion
---

# Issue

Create structured GitHub issues for tracking work.

## Critical Rules

**ALL issue titles and bodies must be in English.**
**NEVER create an issue without user confirmation.**

## Workflow

### 1. Classify (bug / feat / refactor / chore / docs)

Analyze the arguments passed to the skill. Suggest a type via **AskUserQuestion**.

**Example:**
```
Question: "Issue: add timeout to CLI commands. Suggested type: feat"
Options:
- "feat — new feature"
- "bug — something is broken"
- "refactor — restructure without changing behavior"
- "chore — maintenance, deps, CI"
- "docs — documentation"
```

### 2. Check for Duplicates

```bash
gh issue list --state open
```

If similar issues exist, inform the user and ask whether to continue or reference the existing one.

### 3. Gather Code Context

If the issue relates to specific code:
- Read relevant source files
- Search the codebase for related patterns
- Note current behavior and limitations

This context informs the issue body. Skip if the issue is not code-specific.

### 4. Compose Issue

Generate title and body in English.

**Title format:** concise, imperative mood (e.g., "Add timeout handling to CLI commands").

**Body format:**
```markdown
## Context
Why this is needed / what's the problem

## Proposal
What to do

## Notes
Additional context, code references
```

Omit `## Notes` section if there is no additional context.

**Label mapping:**

| Type | Label |
|------|-------|
| bug | `bug` |
| feat | `enhancement` |
| refactor | `refactor` |
| chore | `chore` |
| docs | `documentation` |

Present the composed issue to the user as text output for review.

### 5. Create

**User MUST confirm.** `gh issue create` is NOT in allowed-tools.

```bash
gh issue create --title "Issue title" --label "label" --body "$(cat <<'EOF'
## Context
...

## Proposal
...
EOF
)"
```

Report the issue URL and number to the user.
