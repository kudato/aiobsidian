---
name: release
description: Create a new release — bump version in pyproject.toml, create PR, merge, tag, and trigger PyPI publish. Use when the user says "release", "new release", "publish", or wants to create a new version.
disable-model-invocation: true
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git describe:*), Bash(git tag -l:*), Bash(git add:*), Bash(git switch:*), Bash(git pull:*), Bash(uv run:*), Bash(gh pr view:*), Bash(gh pr checks:*), Bash(gh pr list:*), Bash(gh run view:*), Bash(gh run list:*), Read, Edit, AskUserQuestion
---

# Release

Automate the full release workflow: version bump → PR → merge → tag → PyPI publish.

## Critical Rules

- **ALL commits, pushes, PR creation, PR merges, and tag operations MUST be confirmed by the user.** These commands are intentionally NOT in allowed-tools.
- **NEVER force-push or delete branches without explicit user approval.**
- **ALWAYS verify CI passes before merging.**
- **ALL commit messages in English. No co-authors. No Claude Code mentions.**
- Version in `pyproject.toml` MUST match the tag (enforced by `release.yml`).

## State Detection

Before starting, detect where in the process we are:

```bash
git status
git branch --show-current
git tag -l --sort=-v:refname | head -5
```

Compare `pyproject.toml` version against the latest git tag.

**If working tree is dirty — STOP and inform the user.**

| State | Detection | Resume from |
|-------|-----------|-------------|
| Fresh | version == latest tag, on main | Phase 1 |
| Version bumped, not tagged | version > latest tag, no tag v\<VERSION\> | Step 1.7 if on chore/bump-\* (check if PR already exists via `gh pr list`), Phase 2 if on main |
| Tagged | Tag v\<VERSION\> exists | Step 2.3 |
| Other branch | not on main and not on chore/bump-\* | STOP and inform the user |

Resume from the appropriate step. Inform the user which state was detected.

If branch `chore/bump-<VERSION>` already exists, switch to it (`git switch chore/bump-<VERSION>`) instead of creating a new one.

---

## Phase 1: Prepare Release PR

### 1.1 Preflight Checks

```bash
git branch --show-current
git pull origin main
```

Verify:
- Currently on `main` branch
- Up to date with remote

**If not on main — STOP and inform the user.**

### 1.2 Determine Version

Read current version:

```bash
# Read pyproject.toml version with Read tool
git tag -l --sort=-v:refname | head -5
```

Review changes since the last tag to understand what was released:

```bash
git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo --root)..HEAD
```

Suggest the next version based on semver and the nature of changes:
- **patch** (X.Y.Z+1): bug fixes, chores, docs
- **minor** (X.Y+1.0): new features, backward-compatible changes
- **major** (X+1.0.0): breaking API changes

Use **AskUserQuestion** to present 3 semver bump options. Let the user choose or provide a custom version.

### 1.3 Run Local Checks

Checks run on main before creating the bump branch — if anything fails, no branch is created.

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run pytest
```

**If any check fails — STOP.** Inform the user about failures. Do not proceed with a broken codebase.

### 1.4 Create Version Bump Branch

```bash
git switch -c chore/bump-<VERSION>
```

### 1.5 Update Version and Changelog

Edit `pyproject.toml`: change `version = "X.Y.Z"` to the new version.

Update `CHANGELOG.md`:
1. Review commits since the last tag: `git log --oneline $(git describe --tags --abbrev=0 2>/dev/null || echo --root)..HEAD`
2. Add a new section at the top (after the header), following [Keep a Changelog](https://keepachangelog.com/) format:
   - **Added** — new features
   - **Changed** — changes to existing functionality
   - **Fixed** — bug fixes
   - **Removed** — removed features
   Omit empty subsections. Use the date of today for the release date.
3. Present the changelog entry to the user via **AskUserQuestion** for review before writing.

Regenerate the lock file and stage all changed files:

```bash
uv lock
git add pyproject.toml uv.lock CHANGELOG.md
```

### 1.6 Commit

**User MUST confirm.** `git commit` is NOT in allowed-tools.

```bash
git commit -m "$(cat <<'EOF'
chore: bump version to <VERSION>
EOF
)"
```

### 1.7 Push and Create PR

**User MUST confirm.** `git push` and `gh pr create` are NOT in allowed-tools.

```bash
git push -u origin chore/bump-<VERSION>
```

```bash
gh pr create --title "chore: bump version to <VERSION>" --body "$(cat <<'EOF'
Release <VERSION>
EOF
)"
```

Report the PR URL to the user.

### 1.8 Wait for CI

```bash
gh pr checks
```

If CI is still running, inform the user. Re-check when asked.
**Do NOT merge until all checks pass.**

If checks fail — inspect the failure with `gh pr checks` and `gh run view <RUN_ID>`. Inform the user about the failure. Do not attempt fixes without user approval.

### 1.9 Merge PR

**User MUST confirm.** `gh pr merge` is NOT in allowed-tools.

```bash
gh pr merge --squash --delete-branch
```

---

## Phase 2: Tag and Release

### 2.1 Update Local Main

```bash
git switch main
git pull origin main
```

### 2.2 Create and Push Tag

**User MUST confirm.** `git tag` and `git push` are NOT in allowed-tools.

Determine the version from `pyproject.toml` if not already known.

```bash
git tag v<VERSION>
git push origin v<VERSION>
```

This triggers `release.yml` which:
1. Runs full CI
2. Validates tag version matches `pyproject.toml`
3. Builds with `uv build`
4. Publishes to PyPI (trusted publisher)
5. Creates GitHub Release with auto-generated notes

### 2.3 Verify Release

```bash
gh run list --workflow=release.yml --limit=1
```

Monitor until complete. On success, report to the user:

```bash
gh run view <RUN_ID>
```

Provide the GitHub Release URL if available.

If the workflow fails — inspect with `gh run view <RUN_ID>`. Inform the user about the failure. Do not attempt fixes without user approval.

## Important Notes

- `pyproject.toml`, `uv.lock`, and `CHANGELOG.md` are the only files updated during a release
- The release CI validates tag ↔ pyproject.toml version consistency
- PyPI publish uses trusted publisher (OIDC) — no API tokens needed
- GitHub Release notes are auto-generated from commits since the last tag
