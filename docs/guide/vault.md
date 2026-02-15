# Vault Operations

The `client.vault` resource provides full CRUD operations on files and directories in your Obsidian vault.

## Reading files

### Markdown content

```python
content = await client.vault.get("Notes/hello.md")
print(content)  # Raw Markdown string
```

### Structured JSON

Get the note with parsed frontmatter, tags, and file stats:

```python
from aiobsidian import ContentType

note = await client.vault.get("Notes/hello.md", content_type=ContentType.NOTE_JSON)
print(note.content)      # Markdown body
print(note.frontmatter)  # {"title": "Hello", "tags": ["greeting"]}
print(note.tags)          # ["greeting"]
print(note.path)          # "Notes/hello.md"
print(note.stat.mtime)   # Last modification timestamp
```

### Document map

Discover the structure of a note — headings, blocks, and frontmatter fields:

```python
from aiobsidian import ContentType

doc_map = await client.vault.get("Notes/hello.md", content_type=ContentType.DOCUMENT_MAP)
print(doc_map.headings)           # ["Introduction", "Details"]
print(doc_map.blocks)             # ["block-id-1", "block-id-2"]
print(doc_map.frontmatter_fields) # ["title", "tags"]
```

This is useful for finding valid targets before using `patch()`.

## Creating files

```python
await client.vault.update(
    "Notes/new-note.md",
    "# My New Note\n\nThis is the content.",
)
```

!!! note
    If the file already exists, it will be overwritten.

## Appending content

```python
await client.vault.append("Notes/hello.md", "\n\n## New Section\n\nAppended text.")
```

## Patching specific sections

The `patch()` method lets you modify a specific part of a note:

### Patch a heading

```python
from aiobsidian import PatchOperation, TargetType

await client.vault.patch(
    "Notes/hello.md",
    "New content under this heading",
    operation=PatchOperation.APPEND,
    target_type=TargetType.HEADING,
    target="Introduction",
)
```

### Patch a block reference

```python
await client.vault.patch(
    "Notes/hello.md",
    "Replaced block content",
    operation=PatchOperation.REPLACE,
    target_type=TargetType.BLOCK,
    target="block-id-1",
)
```

### Patch frontmatter

```python
import json

await client.vault.patch(
    "Notes/hello.md",
    json.dumps({"status": "published"}),
    operation=PatchOperation.REPLACE,
    target_type=TargetType.FRONTMATTER,
    target="status",
)
```

### Patch operations

| Operation | Description |
|-----------|-------------|
| `PatchOperation.APPEND` | Insert content **after** the target |
| `PatchOperation.PREPEND` | Insert content **before** the target |
| `PatchOperation.REPLACE` | **Replace** the target content entirely |

### Target types

| Target type | Description |
|-------------|-------------|
| `TargetType.HEADING` | A heading section (e.g. `## My Heading`) |
| `TargetType.BLOCK` | A block reference (e.g. `^block-id`) |
| `TargetType.FRONTMATTER` | A YAML frontmatter field |

## Deleting files

```python
await client.vault.delete("Notes/old-note.md")
```

## Listing files

```python
# List all files in the vault root
directory = await client.vault.list()
for path in directory.files:
    print(path)

# List files in a subdirectory
notes = await client.vault.list("Notes")
for path in notes.files:
    print(path)
```
