# Open Files

The `client.open` resource opens files in the Obsidian UI.

## Opening a file

```python
await client.open.open("Notes/hello.md")
```

This will focus the file in the Obsidian editor.

## Opening in a new tab

```python
await client.open.open("Notes/hello.md", new_leaf=True)
```

Setting `new_leaf=True` opens the file in a new tab (leaf) instead of replacing the current one.
