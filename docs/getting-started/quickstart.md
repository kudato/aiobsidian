# Quick Start

This guide walks you through the most common operations with aiobsidian.

## CLI

### Creating a CLI instance

Use `ObsidianCLI` as an async context manager:

```python
import asyncio
from aiobsidian import ObsidianCLI

async def main():
    async with ObsidianCLI("MyVault") as cli:
        files = await cli.vault.list()
        print(f"{len(files)} files in vault")

asyncio.run(main())
```

### Available CLI resources

| Resource | Access | Description |
|----------|--------|-------------|
| **vault** | `cli.vault` | Read, create, append, prepend, move, rename, delete, list |
| **daily** | `cli.daily` | Daily note: read, create, append, prepend, path |
| **search** | `cli.search` | Full-text search |
| **properties** | `cli.properties` | YAML frontmatter properties: list, read, set, remove |
| **tags** | `cli.tags` | Tags: list, get notes by tag, rename |
| **links** | `cli.links` | Outgoing links, backlinks, unresolved, orphans |
| **tasks** | `cli.tasks` | Tasks: list, create, complete |

### Reading and writing notes

```python
# Read a note
content = await cli.vault.read("notes/hello.md")

# Create a note
await cli.vault.create("notes/new.md", "# New Note\n\nContent here.")

# Append to a note
await cli.vault.append("notes/hello.md", "\n## New section")
```

### Working with tags

```python
# List all tags
tags = await cli.tags.list(sort="count")

# Get notes with a specific tag
notes = await cli.tags.get("python")

# Rename a tag across the vault
await cli.tags.rename("old-tag", "new-tag")
```

### Working with links

```python
# Get outgoing links from a note
links = await cli.links.outgoing("notes/hello.md")

# Get backlinks to a note
backlinks = await cli.links.incoming("notes/hello.md")

# Find broken links
broken = await cli.links.unresolved()

# Find orphan notes
orphans = await cli.links.orphans()
```

### Working with tasks

```python
# List all tasks
tasks = await cli.tasks.list()

# Create a task
await cli.tasks.create("Buy milk", tags="shopping,errands")

# Complete a task
await cli.tasks.complete("task-id")
```

### Searching

```python
results = await cli.search.query("python asyncio")
for result in results:
    print(result)
```

### Daily notes

```python
# Read today's daily note
content = await cli.daily.read()

# Append to today's note
await cli.daily.append("- [x] Completed task")

# Get the path
path = await cli.daily.path()
```

---

## REST

### Creating a REST client

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

### Available REST resources

| Resource | Access | Description |
|----------|--------|-------------|
| **vault** | `client.vault` | Read, create, update, and delete vault files |
| **active** | `client.active` | Operate on the currently open file |
| **periodic** | `client.periodic` | Access daily, weekly, monthly, quarterly, yearly notes |
| **commands** | `client.commands` | List and execute Obsidian commands |
| **search** | `client.search` | Search vault content |
| **open** | `client.open` | Open files in the Obsidian UI |
| **system** | `client.system` | Server status and OpenAPI spec |

### Reading a note

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

### Creating a note

```python
await client.vault.update("Notes/new-note.md", "# My New Note\n\nHello, world!")
```

### Searching

```python
results = await client.search.simple("python asyncio")
for result in results:
    print(f"{result.filename} (score: {result.score})")
    for match in result.matches or []:
        print(f"  ...{match.context}...")
```

### Executing commands

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
- [Error Handling](../guide/error-handling.md) — handle errors gracefully
