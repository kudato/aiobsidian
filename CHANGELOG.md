# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

This release is the result of auditing both transports against a live
Obsidian 1.13.7 and against the CLI command definitions inside the app
itself. Much of the surface was wrong rather than missing, so most of
the entries below are breaking, and 49 CLI methods changed what they
return.

### Added
- `ObsidianCLI.aclose()`, so either client can be released without an `isinstance` check
- `ObsidianCLI.run()` for commands the library does not wrap, the CLI counterpart of `ObsidianClient.request()`
- Resource and model classes are importable from `aiobsidian.cli`, `aiobsidian.rest` and `aiobsidian.models`
- `PropertyType` and `PropertyValue` for typed frontmatter, and `JsonValue` for what `patch()` and `properties.set()` accept
- `APIStatusError`, `APIRequestError`, `APIConnectionError`, `APITimeoutError` and `APIProtocolError`
- `APINotFoundError`, `CLINotFoundError` and `CLIParseError`, so a missing note and unparseable output can be told apart from any other failure of that transport
- `PartialWriteError`, for a write the CLI forces into several commands failing part-way: it names the file the earlier parts landed in — for `vault.create_unique()` the note whose path the exception would otherwise have cost the caller — counts them, and carries the failure as its cause. A first command failing raises itself, as before, since nothing has landed yet
- `tasks.reopen()` to undo `tasks.complete()`, `tasks.list(todo=)`, `daily.open()`, `publish.add(changed=)` and `CommandError.stdout`
- `vault.create_unique()`, the Unique note creator's command: it names a note after the moment it was created, puts it where that plugin says, and reports the path it landed on
- `vault.resolve()`, which looks a note up by name the way a wikilink does and hands back its record, so a name can be turned into the path every other method takes
- `vault.file_count()`, `vault.folder_count()` and `tabs.recent_count()`, which ask the CLI for the number rather than count a listing that had to be printed and read back first
- `vault.open(new_tab=)`, `vault.write(open=, new_tab=)` and `vault.prepend(inline=)`
- `sync.is_paused()`, `plugins.is_restricted()` and `dev.is_attached()`, the read side of the on/off switches. Mobile emulation has no counterpart to give: asked for neither state its command flips the emulation instead of reporting it
- `Tag`, `Task`, `Backlink`, `Bookmark`, `Hotkey`, `Plugin`, `Heading`, `MatchedFile`, `MatchedLine`, `BaseView`, `FileVersion` and `PublishChange`, the models the CLI list commands return
- `VaultInfo`, `FolderInfo`, `FileInfo`, `WordCount`, `PluginInfo`, `SyncStatus` and `PublishSite`, the models the CLI commands that describe one thing return

### Removed
- **Breaking**: the REST `periodic` resource, `ObsidianClient.periodic` and `Period` — the plugin has no such endpoints
- **Breaking**: `SearchResource.dataview()` and `ContentType.DATAVIEW_DQL`, for the same reason
- **Breaking**: `tasks.create()`, `tags.rename()` and `daily.create()` — no such CLI commands exist
- **Breaking**: parameters the CLI does not accept — `search.query(matches=)`, `search.context(lines=)`, `daily.read(date=)`, `vault.write(silent=)`, `bases.views(path=)`, `publish.status(path=)` and `bases.create(**fields)`
- **Breaking**: `tags.list(counts=)`, `plugins.list(versions=)` and `links.incoming(counts=)`. Those flags widen the table the CLI prints and nothing else, so the library asks for the whole of it and the count and the version are always there
- **Breaking**: `hotkeys.get(verbose=)`, which marks a binding as the user's or Obsidian's but says nothing for a command that has none. `hotkeys.list()` reports it for every command

### Changed
- **Breaking**: `NotFoundError` hangs off `ObsidianError` rather than `APIError` and carries no `status_code`. It is what both transports now raise for something that does not exist, through `APINotFoundError` and `CLINotFoundError`, so `issubclass(NotFoundError, APIError)` is `False` and an `except NotFoundError` written for REST also catches a missing note over the CLI
- **Breaking**: `APIError` is the REST transport root and no longer carries `status_code`, `message` or `error_code`. Catch `APIStatusError` for those; `AuthenticationError` moves under it, unchanged in behaviour
- **Breaking**: CLI methods return what the command prints. The `list[dict[str, Any]]` and `dict[str, Any]` annotations described JSON that never arrives: 21 methods across `bases`, `commands`, `dev`, `history`, `links`, `publish`, `search`, `snippets`, `sync`, `system`, `tabs`, `tags`, `templates`, `themes` and `workspaces` return `list[str]`, and `system.help()`, `themes.current()` and `workspaces.current()` return `str`
- **Breaking**: CLI resources address notes by exact path. They sent `file=`, which resolves like a wikilink, so a name matching two notes picked one at random and a path that did not exist still resolved. `bookmarks.add()` and `tabs.open()` keep `file=`, where the CLI takes it as one of several alternatives to `folder=`, `url=` or `view=`
- **Breaking**: CLI resources send the parameter names the CLI requires — `name=` rather than `property=` or `new-name=`
- **Breaking**: `properties.read()` returns `PropertyValue` parsed from the CLI's text output, and `properties.set()` takes any `JsonValue` and sends the value's type
- **Breaking**: `plugins.enabled()` and `links.unresolved()` return `list[str]`. Asked for JSON, the CLI prints a table, so a one-column answer arrived as a list of one-key objects — `[{"id": "dataview"}]` — and every call site ended in a comprehension over `p["id"]`
- **Breaking**: `tags.list()`, `tasks.list()`, `links.incoming()`, `bookmarks.list()`, `hotkeys.list()` and `plugins.list()` return models. Asked for JSON the CLI still prints a table, and a table holds text: a task reported its line number as `"5"` and a tag its count as `"4"`. The numbers are numbers again — so a listed task can be passed straight to `tasks.complete()` — an unversioned core plugin reads as `None` rather than `""`, `Tag.name` drops the `#` that `tags.get()` does not want, and `hotkeys.list()` hands back the several bindings a command can carry rather than the one string the CLI joins them into
- **Breaking**: `hotkeys.get()` returns `list[str]` of bindings, empty when the command has none. It answered `"(none)"` for that, and joined the several bindings a command can carry into one string
- **Breaking**: `outline.get()`, `search.context()`, `bases.views()`, `history.versions()` and `publish.status()` return models, so every list-returning CLI method does but `bases.query()`, whose columns are the base's own. `outline` and `search:context` are the two commands that really serialise, numbers included; the other three print a plain text table whose column names only ever existed in this library
- **Breaking**: `vault.info()`, `vault.folder_info()`, `vault.file_info()`, `vault.wordcount()`, `plugins.info()`, `sync.status()` and `publish.site()` return models, so no CLI method hands back a bare dictionary but `bases.query()` and `properties.list()`, whose keys belong to the vault rather than to Obsidian. These commands describe one thing as a field per line, and a line is text: a file size arrived as `"137"` and its timestamps as the milliseconds behind them, and are an `int` and two aware `datetime`s now. `PluginInfo.enabled` is a `bool` and a core plugin's missing version reads as `None` rather than as an absent key, and `SyncStatus` takes apart the one line on which Sync reports both what the account uses and what it is allowed
- **Breaking**: `history.read(version=)`, `history.restore(version=)` and `history.diff(from_version=, to_version=)` take an `int`, and `history.diff(filter=)` takes `"local"` or `"sync"`. A version is a position in the listing, counting from 1, which is what `FileVersion.version` now carries
- **Breaking**: `search.query()` returns `list[str]` of paths; the CLI reports no match counts
- **Breaking**: `tasks.complete()` takes the note and the line, not a task id the CLI has no notion of
- **Breaking**: every on/off switch is spelled `set_<thing>(value)`, so `sync.toggle(on=)`, `plugins.restrict(on=)`, `dev.mobile(on=)` and `dev.debug(on=)` are `sync.set_paused()`, `plugins.set_restricted()`, `dev.set_mobile()` and `dev.set_debugger()`, and each answers whether it changed anything rather than `None`. Restricted mode and mobile emulation reload the Obsidian window only when they really change, so that answer is what a caller waits on. `toggle` is left to mean what it says, as in `tasks.toggle()`. Mind that `set_paused(True)` pauses, where `toggle(on=True)` resumed
- **Breaking**: one name per operation, whichever transport you are holding. REST `vault.get()`, `vault.update()`, `active.get()` and `active.update()` are `read()` and `write()`. `read()` is what the CLI already called it; `write()` is new to both transports, because CLI `vault.create()` named the command it runs rather than the operation it performs. `write()` means create-or-replace everywhere, so the CLI's `overwrite` defaults to `True`; `overwrite=False` leaves a file that exists as it is and writes beside it under the next free name, since the CLI has no refusal to give — REST `write()` always replaces
- **Breaking**: `client.open.open(filename)` is `client.vault.open(path)`, and `OpenResource` is gone with the `client.open` property. Opening is something you do to a vault file, and the CLI had already put it there
- **Breaking**: `client.vault.list()` returns `list[str]` and calls its argument `folder`. `VaultDirectory` is gone with it: it wrapped a single list in a single field, so every call ended in `.files`. The two transports still list different things, and now say so — REST answers with one level and marks a subfolder with a trailing slash, while the CLI walks the tree, reports only files, and leaves folders to `folders()`
- **Breaking**: CLI `vault.list()` and `vault.folders()` call their first argument `folder`, and it now does something. Both sent `path=`, which `files` and `folders` ignore, so `vault.list("Notes")` listed the whole vault
- **Breaking**: `vault.write()` returns the path of the file it wrote, read off the command's own answer. The CLI decides that path rather than taking the arguments' word for it — `.md` is added to a path without an extension, an empty one is filed under `Untitled`, and without `overwrite` an existing file is left alone and the next free name — `note 1.md` — is created beside it. The library used to work the path out for itself to aim the rest of a split write, and in each of those cases aimed it at a file the command never touched
- **Breaking**: `sync.read()` and `sync.restore()` take `version` as an `int`
- **Breaking**: `dev.dom()` takes `match_all=` rather than shadowing `all`, `dev.screenshot()` returns `None` because the CLI writes the file and prints nothing, `vault.write()` defaults `content` to `""`, and `publish.add()` and `publish.open()` return the CLI's reply instead of `None`
- **Breaking**: leaving an `ObsidianCLI` context manager now closes the client. It was a no-op before, so one instance could serve several `async with` blocks; entering a closed one now raises `RuntimeError`
- **Breaking**: a request the HTTP layer refuses to send — an unparseable `host`, a `scheme` that is not HTTP, a `port` out of range, an illegal header — raises `ValueError` instead of surfacing as a transport failure or an `ExceptionGroup`
- **Breaking**: patching against Local REST API 5.x sends the 1.x patch protocol, and `DocumentMap` reports targets in the spelling `patch()` accepts
- **Breaking**: `tags.list(sort=)` takes `"count"` or nothing. The command compares against that one word and sorts by name for everything else, so any other value asked for an order it did not get and was told nothing
- `SearchResult.result` accepts the strings, numbers and booleans a query returns, not only objects and arrays
- Closing an `ObsidianCLI` kills every command still running, and the command's own children with it

### Fixed
- The vault a client was built for was never the one commands ran against. `vault=` was sent behind the command name, and Obsidian reads it off the front of the arguments and nowhere else, so it reached the command as a parameter no command has a use for. What ran instead was whichever vault holds the working directory or, that failing, whichever window was last in front
- Three failures the CLI reports without the `Error: ` prefix were returned as content. A `vault=` naming no vault and a CLI switched off in the settings each answer with one sentence, decided before the command reaches a vault; and `command`, `history:restore` and `workspace:save` report a parameter they cannot do without by returning `Missing required parameter: ...` rather than raising it. All three raise `CommandError` now — a vault that cannot be reached is not a missing note, so it is not a `CLINotFoundError`
- `bases.list()` handed back `No base files found in vault` as though it were the path of a base, and `bases.query()` refused `No views defined in base file` as unparseable. Obsidian ends nearly every empty-result line with a full stop and these two with nothing, so the library read them as content
- `properties.list()`, `search.query()` and `bases.query()` annotated what they hand back and never looked at it, so a command answering with valid JSON of another shape returned a list where the signature says mapping, and a mapping where it says list of paths. They raise `CLIParseError` now
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
