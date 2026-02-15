# Quick Start

This guide walks you through the most common operations with aiobsidian.

## Creating a client

Use `ObsidianClient` as an async context manager to ensure the HTTP connection is properly closed:

```python
import asyncio
from aiobsidian import ObsidianClient

async def main():
    async with ObsidianClient(api_key="your-api-key") as client:
        status = await client.system.status()
        print(status.authenticated)  # True

asyncio.run(main())
```

## Available resources

The client provides access to several resource groups:

| Resource | Access | Description |
|----------|--------|-------------|
| **vault** | `client.vault` | Read, create, update, and delete vault files |
| **active** | `client.active` | Operate on the currently open file |
| **periodic** | `client.periodic` | Access daily, weekly, monthly, quarterly, yearly notes |
| **commands** | `client.commands` | List and execute Obsidian commands |
| **search** | `client.search` | Search vault content |
| **open** | `client.open` | Open files in the Obsidian UI |
| **system** | `client.system` | Server status and OpenAPI spec |

## Reading a note

```python
# Get raw Markdown
content = await client.vault.get("Notes/hello.md")
print(content)

# Get structured JSON (with frontmatter, tags, stats)
from aiobsidian import ContentType

note = await client.vault.get("Notes/hello.md", content_type=ContentType.NOTE_JSON)
print(note.frontmatter)
print(note.tags)
```

## Creating a note

```python
await client.vault.update("Notes/new-note.md", "# My New Note\n\nHello, world!")
```

## Searching

```python
results = await client.search.simple("python asyncio")
for result in results:
    print(f"{result.filename} (score: {result.score})")
    for match in result.matches or []:
        print(f"  ...{match.context}...")
```

## Executing commands

```python
commands = await client.commands.list()
for cmd in commands[:5]:
    print(f"{cmd.id}: {cmd.name}")

# Execute a specific command
await client.commands.execute("editor:toggle-bold")
```

## Next steps

- [Configuration](configuration.md) — customize connection settings
- [Vault Operations](../guide/vault.md) — full guide on vault file operations
- [Error Handling](../guide/error-handling.md) — handle API errors gracefully
