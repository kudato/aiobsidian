---
name: commit
description: Generates Conventional Commits messages with Why/What context, then commits changes. Use when the user says "commit", "git commit", or asks to commit changes, wants to create a commit, or when work is complete and ready to commit.
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git add:*), Bash(git branch:*), Bash(git switch:*), Bash(git log:*), AskUserQuestion
---

# Commit

Generate Conventional Commits messages with Why/What context.

## Critical Rules

**IMPORTANT: NEVER EVER ADD CO-AUTHOR TO THE GIT COMMIT MESSAGE**
**NEVER mention Claude Code in commit messages**
**ALL commit messages must be in English.**

## Workflow

### 1. Gather and Analyze Context

First, collect information about the current state:

```bash
# Current git status
git status

# Current git diff (staged and unstaged)
git diff --staged
git diff

# Recent commits for context
git log --oneline -5

# Current branch
git branch --show-current
```

**If there are no staged or unstaged changes — inform the user and stop.**

**If there are unstaged changes but nothing is staged — use AskUserQuestion to ask the user which files to stage.**

Analyze the collected diff to understand WHAT changed technically:
- Files modified
- Functions added/updated
- Dependencies changed
- Configuration updates

### 2. Branch Safety Check

After gathering context, verify the current branch is appropriate for the changes:

- **If on `main`**: STOP. Do not commit directly to main.
  Use **AskUserQuestion** to ask the user:
  - "Create a new branch for these changes?" (suggest a name based on the diff, e.g. `feat/add-timeout-handling`)
  - "I know what I'm doing, commit to main anyway"
  If the user chooses to create a branch, run `git switch -c <branch-name>` before proceeding.

- **If on a feature branch**: Verify the branch name is consistent with the changes.
  For example, committing a `fix(auth)` change to a branch named `feat/add-search` is suspicious.
  If there's a mismatch, **warn the user** via AskUserQuestion and ask whether to continue or switch/create a different branch.

### 3. Human-in-the-Loop - Classify and Ask for Context

Analyze the diff and present a brief summary of changes to the user via **AskUserQuestion**. Ask whether this is a trivial change.

**Example:**
```
Question: "Changes: fixed typo in vault.read() docstring ('retuns' → 'returns'). Is this a trivial change (single-line commit without body)?"
Options:
- "Yes, trivial — single-line commit"
- "No, I want to describe in detail"
```

**If trivial** — skip to Step 5, use single-line format.

**If non-trivial** — ask WHY the change was made via AskUserQuestion. Generate 3-4 plausible options based on the technical analysis from Step 1.

**Example:**
```
Question: "Why did you make these changes?"
Options:
- "Fix bug where X was causing Y"
- "Add new feature for Z"
- "Refactor to improve maintainability"
- (User can always select "Other" to provide custom explanation)
```

Wait for their response and incorporate their explanation into the commit message.

### 4. Create Enhanced Commit Message

Generate a commit message that tells a complete story for future code archeology.

Scope is optional — use it when it clarifies which module is affected (e.g., `feat(periodic):` vs `feat:`). Omit when obvious from the subject line.

**For trivial changes** (typos, single-line fixes, dependency bumps, formatting) — use a single-line message without body:
```
type[(scope)]: concise subject line
```

**For non-trivial changes** — use the full format:
```
type[(scope)]: concise subject line describing what changed

Why this change was needed:
[Incorporate the user's explanation]

What changed:
[Technical summary of the modifications]
```

**Conventional Commits Types:**
- **feat**: new features
- **fix**: bug fixes
- **docs**: documentation changes
- **style**: formatting, missing semicolons, etc.
- **refactor**: code restructuring without changing functionality
- **test**: adding or updating tests
- **chore**: maintenance tasks, dependencies, build process
- **perf**: performance improvements
- **ci**: continuous integration changes

### 5. Execute Commit

**IMPORTANT: Do not use `git add -A` or `git add .`**
Commit only the files that are already staged and understood.

**CRITICAL: The user MUST confirm before executing `git commit`, don't use `git push`.**
These commands are intentionally NOT in the allowed-tools list, so the user will be prompted for approval.

After receiving the user's approval of the commit message:

1. **Single-line commit** (for trivial changes):
```bash
git commit -m "docs: fix typo in vault.read docstring"
```

2. **Commit with heredoc** (for multi-line messages):
```bash
git commit -m "$(cat <<'EOF'
type[(scope)]: subject line

Why this change was needed:
[explanation]

What changed:
[technical summary]
EOF
)"
```

## Examples

### Example 1: Feature

```
feat(mcp): add tool execution timeout handling

Why this change was needed:
Tools were hanging indefinitely when external APIs failed to respond,
blocking the entire MCP server. This was causing user-facing timeouts
in the chat interface.

What changed:
- Added configurable timeout wrapper around tool execution
- Implemented graceful timeout error messages
- Updated tool registry to support per-tool timeout configuration
```

### Example 2: Bug Fix

```
fix(auth): prevent token refresh race condition

Why this change was needed:
Multiple simultaneous requests were triggering concurrent token refresh
attempts, causing some requests to fail with stale tokens.

What changed:
- Added mutex lock around token refresh logic
- Implemented token refresh deduplication
- Added retry logic for failed requests during refresh
```

### Example 3: Refactoring

```
refactor(api): extract validation logic to shared module

Why this change was needed:
Input validation was duplicated across 7 different API endpoints,
making it difficult to maintain consistent validation rules.

What changed:
- Created shared validation utilities in packages/validation
- Updated all API endpoints to use shared validators
- Removed 200+ lines of duplicated validation code
```

## Important Notes

- **Never skip the trivial/non-trivial question** - Let the user decide the commit format
- **Use heredoc for multi-line commits** - Ensures proper formatting
- **Be specific** in technical summaries
- **Think about the reader** - someone debugging this code in 6 months
- **No co-authors** - Never add "Co-Authored-By" or mention Claude Code
