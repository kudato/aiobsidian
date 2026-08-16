# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- `ObsidianCLI.aclose()`, so either client can be released without an `isinstance` check
- `ObsidianCLI.run()` for commands the library does not wrap, the CLI counterpart of `ObsidianClient.request()`
- Resource and model classes are importable from `aiobsidian.cli`, `aiobsidian.rest` and `aiobsidian.models`

### Changed
- **Breaking**: leaving an `ObsidianCLI` context manager now closes the client. It was a no-op before, so one instance could be used across several `async with` blocks; the second one now raises `RuntimeError`
- Closing an `ObsidianCLI` kills every command still running, and the command's own children with it

### Fixed
- Cancelling or timing out a command left the processes it had started behind, holding the vault and the caller's pipe. Commands now run in their own process group
- Every resource declares `__slots__`; only the base classes did, so instances carried a `__dict__`

## [0.4.0] — 2026-03-29

### Added
- 4 new CLI resources: system, tabs, web, dev
- Full Obsidian CLI v1.12+ coverage with all flags and parameters across all resources
- New methods in existing resources: vault.open, search.open, tasks.toggle, templates.insert, plugins.info, plugins.restrict, history.versions, history.open, history.diff, sync.toggle, sync.open, publish.open, random.open

## [0.3.0] — 2026-03-22

### Added
- CLI-first architecture with `ObsidianCLI` async subprocess wrapper
- 22 CLI resources: vault, daily, search, properties, tags, links, tasks, commands, templates, bookmarks, plugins, themes, snippets, sync, publish, history, workspaces, hotkeys, outline, random, aliases, bases
- Migrated to `uv audit` for dependency vulnerability scanning

### Changed
- Primary interface is now `ObsidianCLI` (CLI-based); REST via `ObsidianClient` is optional

## [0.2.0] — 2026-03-15

### Added
- Optional date parameter for accessing periodic notes by date

## [0.1.1] — 2026-02-15

### Fixed
- Add `__repr__` to `ObsidianClient` to prevent API key leakage in logs

### Changed
- Add `from __future__ import annotations` to all modules (project convention compliance)

### Added
- Tests for file paths with special characters (spaces, unicode, deep nesting)
- Dependency auditing (`pip-audit`) in CI pipeline
- Dependabot configuration for automated dependency updates

## [0.1.0] — 2026-01-01

### Added
- Initial release: async client for Obsidian Local REST API
- Resources: vault, active, periodic, commands, search, open, system
- Pydantic v2 models for typed API responses
- Exception hierarchy: APIError, AuthenticationError, NotFoundError
