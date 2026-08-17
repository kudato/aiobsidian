# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

This release is the result of auditing both transports against a live
Obsidian 1.13.7 and against the CLI command definitions inside the app
itself. Much of the surface was wrong rather than missing, so most of
the entries below are breaking, and 39 CLI methods changed what they
return.

### Added
- `ObsidianCLI.aclose()`, so either client can be released without an `isinstance` check
- `ObsidianCLI.run()` for commands the library does not wrap, the CLI counterpart of `ObsidianClient.request()`
- Resource and model classes are importable from `aiobsidian.cli`, `aiobsidian.rest` and `aiobsidian.models`
- `PropertyType` and `PropertyValue` for typed frontmatter, and `JsonValue` for what `patch()` and `properties.set()` accept
- `APIStatusError`, `APIRequestError`, `APIConnectionError`, `APITimeoutError` and `APIProtocolError`
- `APINotFoundError`, `CLINotFoundError` and `CLIParseError`, so a missing note and unparseable output can be told apart from any other failure of that transport
- `tasks.reopen()` to undo `tasks.complete()`, `tasks.list(todo=)`, `daily.open()`, `publish.add(changed=)` and `CommandError.stdout`

### Removed
- **Breaking**: the REST `periodic` resource, `ObsidianClient.periodic` and `Period` — the plugin has no such endpoints
- **Breaking**: `SearchResource.dataview()` and `ContentType.DATAVIEW_DQL`, for the same reason
- **Breaking**: `tasks.create()`, `tags.rename()` and `daily.create()` — no such CLI commands exist
- **Breaking**: parameters the CLI does not accept — `search.query(matches=)`, `search.context(lines=)`, `daily.read(date=)`, `vault.write(silent=)`, `bases.views(path=)`, `publish.status(path=)` and `bases.create(**fields)`

### Changed
- **Breaking**: `NotFoundError` hangs off `ObsidianError` rather than `APIError` and carries no `status_code`. It is what both transports now raise for something that does not exist, through `APINotFoundError` and `CLINotFoundError`, so `issubclass(NotFoundError, APIError)` is `False` and an `except NotFoundError` written for REST also catches a missing note over the CLI
- **Breaking**: `APIError` is the REST transport root and no longer carries `status_code`, `message` or `error_code`. Catch `APIStatusError` for those; `AuthenticationError` moves under it, unchanged in behaviour
- **Breaking**: CLI methods return what the command prints. The `list[dict[str, Any]]` and `dict[str, Any]` annotations described JSON that never arrives: 21 methods across `bases`, `commands`, `dev`, `history`, `links`, `publish`, `search`, `snippets`, `sync`, `system`, `tabs`, `tags`, `templates`, `themes` and `workspaces` return `list[str]`, the record-shaped ones return `dict[str, str]` — `dict[str, int]` for `vault.wordcount()` — and `hotkeys.get()`, `system.help()`, `themes.current()` and `workspaces.current()` return `str`
- **Breaking**: CLI resources address notes by exact path. They sent `file=`, which resolves like a wikilink, so a name matching two notes picked one at random and a path that did not exist still resolved. `bookmarks.add()` and `tabs.open()` keep `file=`, where the CLI takes it as one of several alternatives to `folder=`, `url=` or `view=`
- **Breaking**: CLI resources send the parameter names the CLI requires — `name=` rather than `property=` or `new-name=`
- **Breaking**: `properties.read()` returns `PropertyValue` parsed from the CLI's text output, and `properties.set()` takes any `JsonValue` and sends the value's type
- **Breaking**: `search.query()` returns `list[str]` of paths; the CLI reports no match counts
- **Breaking**: `tasks.complete()` takes the note and the line, not a task id the CLI has no notion of
- **Breaking**: every on/off switch is spelled `set_<thing>(value)`, so `sync.toggle(on=)`, `plugins.restrict(on=)`, `dev.mobile(on=)` and `dev.debug(on=)` are `sync.set_paused()`, `plugins.set_restricted()`, `dev.set_mobile()` and `dev.set_debugger()`. `toggle` is left to mean what it says, as in `tasks.toggle()`. Mind that `set_paused(True)` pauses, where `toggle(on=True)` resumed
- **Breaking**: one name per operation, whichever transport you are holding. REST `vault.get()`, `vault.update()`, `active.get()` and `active.update()` are `read()` and `write()`. `read()` is what the CLI already called it; `write()` is new to both transports, because CLI `vault.create()` named the command it runs rather than the operation it performs. `write()` means create-or-replace everywhere, so the CLI's `overwrite` defaults to `True`; `overwrite=False` still refuses a file that exists, which is the one thing REST cannot do
- **Breaking**: `client.open.open(filename)` is `client.vault.open(path)`, and `OpenResource` is gone with the `client.open` property. Opening is something you do to a vault file, and the CLI had already put it there
- **Breaking**: `client.vault.list()` returns `list[str]` and calls its argument `folder`. `VaultDirectory` is gone with it: it wrapped a single list in a single field, so every call ended in `.files`. The two transports still list different things, and now say so — REST answers with one level and marks a subfolder with a trailing slash, while the CLI walks the tree, reports only files, and leaves folders to `folders()`
- **Breaking**: CLI `vault.list()` and `vault.folders()` call their first argument `folder`, and it now does something. Both sent `path=`, which `files` and `folders` ignore, so `vault.list("Notes")` listed the whole vault
- **Breaking**: `sync.read()` and `sync.restore()` take `version` as an `int`
- **Breaking**: `dev.dom()` takes `match_all=` rather than shadowing `all`, `dev.screenshot()` returns `None` because the CLI writes the file and prints nothing, `vault.write()` defaults `content` to `""`, and `publish.add()` and `publish.open()` return the CLI's reply instead of `None`
- **Breaking**: leaving an `ObsidianCLI` context manager now closes the client. It was a no-op before, so one instance could serve several `async with` blocks; entering a closed one now raises `RuntimeError`
- **Breaking**: a request the HTTP layer refuses to send — an unparseable `host`, a `scheme` that is not HTTP, a `port` out of range, an illegal header — raises `ValueError` instead of surfacing as a transport failure or an `ExceptionGroup`
- **Breaking**: patching against Local REST API 5.x sends the 1.x patch protocol, and `DocumentMap` reports targets in the spelling `patch()` accepts
- `SearchResult.result` accepts the strings, numbers and booleans a query returns, not only objects and arrays
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
