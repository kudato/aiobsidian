# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [0.3.0] — 2026-03-29

### Added
- CLI-first architecture with `ObsidianCLI` async subprocess wrapper
- 26 CLI resources: vault, daily, search, properties, tags, links, tasks, commands, templates, bookmarks, plugins, themes, snippets, sync, publish, history, workspaces, hotkeys, outline, random, aliases, bases, system, tabs, web, dev
- Full Obsidian CLI v1.12+ coverage with all flags and parameters
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
