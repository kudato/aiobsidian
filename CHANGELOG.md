# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

This release is the result of auditing both transports against a live
Obsidian 1.13.7 and against the CLI command definitions inside the app
itself. Much of the surface was wrong rather than missing, so most of
the entries below are breaking.

### Added
- `ObsidianCLI.aclose()`, so either client can be released without an `isinstance` check
- `ObsidianCLI.run()` for commands the library does not wrap, the CLI counterpart of `ObsidianClient.request()`
- Resource and model classes are importable from `aiobsidian.cli`, `aiobsidian.rest` and `aiobsidian.models`
- `PropertyType` and `PropertyValue` for typed frontmatter, and `JsonValue` for what `patch()` accepts
- `APIStatusError`, `APIRequestError`, `APIConnectionError`, `APITimeoutError` and `APIProtocolError`
- `CLINotFoundError` and `CLIParseError` are public, so a missing note and unparseable output can be told apart from any other command failure
- `tasks.reopen()`, to undo `tasks.complete()`

### Removed
- **Breaking**: the REST `periodic` resource, `ObsidianClient.periodic` and `Period` — the plugin has no such endpoints
- **Breaking**: `SearchResource.dataview()` and `ContentType.DATAVIEW_DQL`, for the same reason
- **Breaking**: `tasks.create()`, `tags.rename()` and `daily.create()` — no such CLI commands exist
- **Breaking**: parameters the CLI does not accept, including `search.query(matches=)`, `search.context(lines=)`, `daily.read(date=)`, `vault.create(silent=)` and `bases.views(path=)`

### Changed
- **Breaking**: `APIError` is now the REST transport root and no longer carries `status_code`, `message` or `error_code`. Catch `APIStatusError` for those; `AuthenticationError` and `APINotFoundError` are unchanged in behaviour
- **Breaking**: CLI resources address notes by exact path. They sent `file=`, which resolves like a wikilink, so a name matching two notes picked one at random and a path that did not exist still resolved
- **Breaking**: CLI resources send the parameter names the CLI requires — `name=` rather than `property=` or `new-name=`, `path=` rather than `file=`
- **Breaking**: `properties.read()` returns `str | list[str] | None` parsed from the CLI's text output instead of JSON that never arrives, and `properties.set()` sends the value's type
- **Breaking**: `search.query()` returns `list[str]` of paths; the CLI reports no match counts
- **Breaking**: `sync`, `publish`, `bases`, `daily` and `dev` methods return what those commands actually print
- **Breaking**: `tasks.complete()` takes the note and the line, not a task id the CLI has no notion of
- **Breaking**: leaving an `ObsidianCLI` context manager now closes the client. It was a no-op before, so one instance could serve several `async with` blocks; entering a closed one now raises `RuntimeError`
- **Breaking**: a request the HTTP layer refuses to send — an unparseable `host`, a `scheme` that is not HTTP, a `port` out of range, an illegal header — raises `ValueError` instead of surfacing as a transport failure or an `ExceptionGroup`
- **Breaking**: patching against Local REST API 5.x sends the 1.x patch protocol, and `DocumentMap` reports targets in the spelling `patch()` accepts
- Closing an `ObsidianCLI` kills every command still running, and the command's own children with it

### Fixed
- The CLI exits `0` on failure and prints `Error: ...`, which the library returned as content. Failures now raise
- Cancelling or timing out a command left the processes it had started behind, holding the vault and the caller's pipe. Commands run in their own process group
- `httpx` exceptions escaped the REST client, so catching "Obsidian is not running" meant importing an optional dependency
- Content containing `\n` or `\t` was corrupted on the way through the CLI
- Boolean options were sent with a `--` prefix the CLI does not use, so none of them ever took effect
- `vault.append()` wrote to the wrong note, and `api_key` was ignored when an external `http_client` was supplied
- Every resource declares `__slots__`; only the base classes did, so instances carried a `__dict__`
- Output is returned as stored: `history.read()`, `sync.read()` and `random.read()` no longer include the header the CLI prints above it, and `templates.read()` keeps its whitespace

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
