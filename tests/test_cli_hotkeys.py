from __future__ import annotations

import json

HOTKEYS = [
    {"command": "editor:toggle-bold", "keys": ["Mod+B"]},
    {"command": "editor:toggle-italic", "keys": ["Mod+I"]},
]

HOTKEY = {"command": "editor:toggle-bold", "keys": ["Mod+B"]}


async def test_list(cli):
    cli._execute.return_value = json.dumps(HOTKEYS)
    result = await cli.hotkeys.list()
    assert result == HOTKEYS
    cli._execute.assert_awaited_once_with("hotkeys")


async def test_get(cli):
    cli._execute.return_value = json.dumps(HOTKEY)
    result = await cli.hotkeys.get("editor:toggle-bold")
    assert result == HOTKEY
    cli._execute.assert_awaited_once_with("hotkey", params={"id": "editor:toggle-bold"})
