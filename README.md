# aiobsidian

[![CI](https://github.com/kudato/aiobsidian/actions/workflows/ci.yml/badge.svg)](https://github.com/kudato/aiobsidian/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aiobsidian)](https://pypi.org/project/aiobsidian/)
[![Python](https://img.shields.io/pypi/pyversions/aiobsidian)](https://pypi.org/project/aiobsidian/)
[![License](https://img.shields.io/github/license/kudato/aiobsidian)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://kudato.github.io/aiobsidian)

Async Python client for [Obsidian](https://obsidian.md). CLI-first: works out of the box with the [Obsidian CLI](https://obsidian.md/cli) (v1.12+). Optional REST support via the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin.

---

## Installation

```bash
pip install aiobsidian
```

For REST API support (requires [httpx](https://www.python-httpx.org/)):

```bash
pip install aiobsidian[rest]
```

## Quick start

### CLI (primary)

```python
import asyncio
from aiobsidian import ObsidianCLI

async def main():
    async with ObsidianCLI("MyVault") as cli:
        # Read a note
        content = await cli.vault.read("notes/hello.md")
        print(content)

        # Search the vault
        results = await cli.search.query("python")

        # List tags
        tags = await cli.tags.list()

        # Daily note
        await cli.daily.append("- [ ] New task")

asyncio.run(main())
```

### REST (optional)

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient("your-api-key") as client:
        status = await client.system.status()
        print(status.versions.obsidian)

        content = await client.vault.get("notes/hello.md")
        print(content)

asyncio.run(main())
```

## Features

### CLI resources

| Resource | Access | Description |
|----------|--------|-------------|
| **vault** | `cli.vault` | Read, create, append, prepend, move, rename, delete, list |
| **daily** | `cli.daily` | Daily note operations |
| **search** | `cli.search` | Full-text search |
| **properties** | `cli.properties` | YAML frontmatter properties |
| **tags** | `cli.tags` | Tag listing, lookup, rename |
| **links** | `cli.links` | Outgoing links, backlinks, unresolved, orphans |
| **tasks** | `cli.tasks` | Task listing, creation, completion, toggle |
| **commands** | `cli.commands` | List and execute Obsidian commands |
| **templates** | `cli.templates` | List, read, insert templates |
| **bookmarks** | `cli.bookmarks` | List and add bookmarks |
| **plugins** | `cli.plugins` | Plugin management |
| **themes** | `cli.themes` | Theme management |
| **snippets** | `cli.snippets` | CSS snippet management |
| **sync** | `cli.sync` | Obsidian Sync operations |
| **publish** | `cli.publish` | Obsidian Publish operations |
| **history** | `cli.history` | Local file history |
| **workspaces** | `cli.workspaces` | Workspace management |
| **hotkeys** | `cli.hotkeys` | Hotkey operations |
| **outline** | `cli.outline` | Document outline (headings) |
| **random** | `cli.random` | Random note |
| **aliases** | `cli.aliases` | Note aliases |
| **bases** | `cli.bases` | Obsidian Bases / databases |
| **system** | `cli.system` | Version, reload, restart, vaults |
| **tabs** | `cli.tabs` | Tab management, recents |
| **web** | `cli.web` | Open URLs in web viewer |
| **dev** | `cli.dev` | Developer/debugging tools |

### REST resources

| Resource | Access | Description |
|----------|--------|-------------|
| **vault** | `client.vault` | CRUD operations on any file |
| **active** | `client.active` | Operations on the currently open file |
| **periodic** | `client.periodic` | Daily, weekly, monthly, quarterly, yearly notes |
| **commands** | `client.commands` | List and execute Obsidian commands |
| **search** | `client.search` | Simple text search, Dataview DQL, JsonLogic |
| **open** | `client.open` | Open files in Obsidian UI |
| **system** | `client.system` | Server status, OpenAPI spec |

### General

- **Full async/await** support
- **Pydantic v2** models for type-safe responses
- **Custom exception hierarchy** for both CLI and REST errors
- **Context manager** lifecycle management
- **No external dependencies** for CLI (only stdlib)

## Documentation

Full documentation is available at [kudato.github.io/aiobsidian](https://kudato.github.io/aiobsidian).

## Contributing

Contributions are welcome! Please see the [Contributing Guide](CONTRIBUTING.md) for details.

## License

[MIT](LICENSE)
