# Commands

The `client.commands` resource lets you list and execute Obsidian commands programmatically.

## Listing commands

```python
commands = await client.commands.list()
for cmd in commands:
    print(f"{cmd.id}: {cmd.name}")
```

Example output:

```
editor:toggle-bold: Toggle bold
editor:toggle-italic: Toggle italic
app:open-settings: Open settings
file-explorer:reveal-active-file: Reveal active file in navigation
```

## Executing a command

```python
await client.commands.execute("editor:toggle-bold")
```

## Finding a command by name

```python
commands = await client.commands.list()
cmd = next((c for c in commands if "bold" in c.name.lower()), None)
if cmd:
    await client.commands.execute(cmd.id)
```

!!! tip
    Command IDs are stable across Obsidian sessions, so you can hard-code them in your scripts once you know the ID.
