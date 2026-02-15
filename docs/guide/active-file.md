# Active File

The `client.active` resource operates on the file currently open (focused) in the Obsidian editor.

## Reading the active file

### Markdown content

```python
content = await client.active.get()
print(content)
```

### Structured JSON

```python
from aiobsidian import ContentType

note = await client.active.get(content_type=ContentType.NOTE_JSON)
print(note.frontmatter)
print(note.tags)
print(note.path)
```

### Document map

```python
from aiobsidian import ContentType

doc_map = await client.active.get(content_type=ContentType.DOCUMENT_MAP)
print(doc_map.headings)
print(doc_map.blocks)
```

## Replacing content

Replace the entire content of the active file:

```python
await client.active.update("# Updated Title\n\nNew content here.")
```

## Appending content

```python
await client.active.append("\n\n---\n\nAppended at the end.")
```

## Patching sections

Works the same as [vault patching](vault.md#patching-specific-sections):

```python
from aiobsidian import PatchOperation, TargetType

await client.active.patch(
    "Content to add under heading",
    operation=PatchOperation.APPEND,
    target_type=TargetType.HEADING,
    target="My Section",
)
```

## Deleting the active file

```python
await client.active.delete()
```

!!! warning
    This permanently deletes the currently active file from the vault.
