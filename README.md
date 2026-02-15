# aiobsidian

[![CI](https://github.com/kudato/aiobsidian/actions/workflows/ci.yml/badge.svg)](https://github.com/kudato/aiobsidian/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aiobsidian)](https://pypi.org/project/aiobsidian/)
[![Python](https://img.shields.io/pypi/pyversions/aiobsidian)](https://pypi.org/project/aiobsidian/)
[![License](https://img.shields.io/github/license/kudato/aiobsidian)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-mkdocs-blue)](https://kudato.github.io/aiobsidian)

Async Python client for the [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin.

---

## Installation

```bash
pip install aiobsidian
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add aiobsidian
```

## Quick start

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient("your-api-key") as client:
        # Server status
        status = await client.system.status()
        print(status.versions.obsidian)

        # Read a note
        content = await client.vault.get("notes/hello.md")
        print(content)

        # Create a note
        await client.vault.update("notes/new.md", "# New Note\n\nContent here.")

        # Search
        results = await client.search.simple("hello")
        for r in results:
            print(r.filename, r.score)

        # Execute a command
        await client.commands.execute("daily-notes")

asyncio.run(main())
```

## Features

- **Full async/await** support via [httpx](https://www.python-httpx.org/)
- **Complete API coverage** — all Obsidian Local REST API endpoints:

  | Resource | Description |
  |----------|-------------|
  | **Vault** | CRUD operations on any file |
  | **Active** | Operations on the currently open file |
  | **Periodic** | Daily, weekly, monthly, quarterly, yearly notes |
  | **Commands** | List and execute Obsidian commands |
  | **Search** | Simple text search, Dataview DQL, JsonLogic |
  | **Open** | Open files in Obsidian UI |
  | **System** | Server status, OpenAPI spec |

- **Pydantic v2** models for type-safe responses
- **Custom exception hierarchy** with error codes
- **Bring-your-own `httpx.AsyncClient`** support
- **Context manager** lifecycle management

## Configuration

```python
client = ObsidianClient(
    "your-api-key",
    host="127.0.0.1",      # default
    port=27124,             # default (HTTPS)
    scheme="https",         # default
    timeout=30.0,           # default
    verify_ssl=False,       # default (self-signed cert)
)
```

### External HTTP client

You can provide your own `httpx.AsyncClient` for full control over transport settings:

```python
import httpx
from aiobsidian import ObsidianClient

async with httpx.AsyncClient(timeout=60.0, verify=False) as http:
    async with ObsidianClient("your-api-key", http_client=http) as client:
        status = await client.system.status()
```

When an external client is provided, `aiobsidian` will not close it — you manage its lifecycle.

## Documentation

Full documentation is available at [kudato.github.io/aiobsidian](https://kudato.github.io/aiobsidian).

## Contributing

Contributions are welcome! Please see the [Contributing Guide](CONTRIBUTING.md) for details.

## License

[MIT](LICENSE)
