# Open Files

The `client.open` resource opens files in the Obsidian UI.

## Opening a file

```python
await client.open.open("Notes/hello.md")
```

This will focus the file in the Obsidian editor.

!!! warning
    Opening is not read-only. If the file does not exist, Obsidian creates an
    empty note at that path and opens it — the call succeeds instead of raising
    `NotFoundError`. Check with `client.vault.get()` first if you need to know
    whether the note was already there.

## Opening in a new tab

```python
await client.open.open("Notes/hello.md", new_leaf=True)
```

Setting `new_leaf=True` opens the file in a new tab (leaf) instead of replacing the current one.
