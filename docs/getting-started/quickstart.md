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
| **vault** | `cli.vault` | Read, write, append, prepend, move, rename, delete, list, open |
| **daily** | `cli.daily` | Daily note: read, open, append, prepend, path |
| **search** | `cli.search` | Full-text search |
| **properties** | `cli.properties` | YAML frontmatter properties: list, read, set, remove |
| **tags** | `cli.tags` | Tags: list, get notes by tag |
| **links** | `cli.links` | Outgoing links, backlinks, unresolved, orphans |
| **tasks** | `cli.tasks` | Tasks: list, complete, reopen, toggle |
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

### Reading and writing notes

```python
# Read a note
content = await cli.vault.read("notes/hello.md")

# Create or replace a note
await cli.vault.write("notes/new.md", "# New Note\n\nContent here.")

# Append to a note
await cli.vault.append("notes/hello.md", "\n## New section")
```

### Working with tags

```python
# List all tags, most used first
tags = await cli.tags.list(sort="count")
print(tags[0].name, tags[0].count)

# Get notes with a specific tag
notes = await cli.tags.get(tags[0].name)
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

# List only the ones still open
open_tasks = await cli.tasks.list(todo=True)

# A task is addressed by its file and line number, which is what a
# listed task carries
for task in open_tasks:
    await cli.tasks.complete(task.file, task.line)

await cli.tasks.reopen("notes/todo.md", 3)
await cli.tasks.toggle("notes/todo.md", 3)

# There is no command that creates a task; append one
await cli.vault.append("notes/todo.md", "- [ ] Buy milk")
```

### Searching

```python
# Paths of the matching files
for path in await cli.search.query("python asyncio"):
    print(path)

# The same search, with the line every hit matched on
for hit in await cli.search.context("python asyncio"):
    for match in hit["matches"]:
        print(f"{hit['file']}:{match['line']}  {match['text']}")
```

### Daily notes

```python
# Read today's daily note
content = await cli.daily.read()

# Append to today's note
await cli.daily.append("- [x] Completed task")

# Get the path
path = await cli.daily.path()

# Create it if it is missing, and show it in the UI
path = await cli.daily.open()
```

Only today's daily note is reachable: no CLI command takes a date.

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
| **vault** | `client.vault` | Read, write, patch, delete and open vault files |
| **active** | `client.active` | Operate on the currently open file |
| **commands** | `client.commands` | List and execute Obsidian commands |
| **search** | `client.search` | Search vault content |
| **system** | `client.system` | Server status and OpenAPI spec |

### Reading a note

```python
# Get raw Markdown
content = await client.vault.read("Notes/hello.md")
print(content)

# Get structured JSON (with frontmatter, tags, stats)
from aiobsidian import ContentType

note = await client.vault.read("Notes/hello.md", content_type=ContentType.NOTE_JSON)
print(note.frontmatter)
print(note.tags)
```

### Writing a note

```python
await client.vault.write("Notes/new-note.md", "# My New Note\n\nHello, world!")
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
