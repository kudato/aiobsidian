# aiobsidian

**Async Python client for the [Obsidian](https://obsidian.md) Local REST API plugin.**

aiobsidian provides a clean, fully-typed async interface to interact with your Obsidian vault programmatically — read and write notes, search content, execute commands, and more.

## Features

- **Async/await** — built on [httpx](https://www.python-httpx.org/) for high-performance async HTTP
- **Fully typed** — complete type annotations and a `py.typed` marker
- **Resource-based API** — intuitive access through `client.vault`, `client.search`, etc.
- **Pydantic v2 models** — structured, validated response objects
- **Multiple content formats** — Markdown, JSON, and document maps
- **Flexible search** — simple text, Dataview DQL, and JsonLogic queries

## Quick example

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient(api_key="your-api-key") as client:
        # Check server status
        status = await client.system.status()
        print(f"Obsidian v{status.versions.obsidian}")

        # Read a note
        content = await client.vault.get("Notes/hello.md")
        print(content)

        # Search the vault
        results = await client.search.simple("python")
        for result in results:
            print(result.filename)

asyncio.run(main())
```

## Next steps

- [Installation](getting-started/installation.md) — install aiobsidian and set up the Obsidian plugin
- [Quick Start](getting-started/quickstart.md) — get up and running in minutes
- [User Guide](guide/vault.md) — learn all the operations available
- [API Reference](reference/client.md) — full API documentation
