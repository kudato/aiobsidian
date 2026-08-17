from __future__ import annotations

import json

from aiobsidian.models.hotkeys import Hotkey

# The listing covers every command, bound or not, sorted by id. `verbose`
# adds the column that tells a binding the user set from one Obsidian
# ships. Several bindings on one command arrive joined by `", "` in that
# single column — and a binding can itself be a comma.
HOTKEYS = [
    {"id": "app:delete-file", "hotkey": "", "custom": "default"},
    {"id": "app:go-back", "hotkey": "⌘ ⌥ ←", "custom": "default"},
    {"id": "app:open-settings", "hotkey": "⌘ ,", "custom": "default"},
    {"id": "editor:toggle-bold", "hotkey": "⌘ B, ⌘ ⇧ B", "custom": "custom"},
    {"id": "editor:toggle-italics", "hotkey": "", "custom": "custom"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(HOTKEYS)
    result = await cli.hotkeys.list()
    assert result == [
        Hotkey(command_id="app:delete-file", keys=[], custom=False),
        Hotkey(command_id="app:go-back", keys=["⌘ ⌥ ←"], custom=False),
        Hotkey(command_id="app:open-settings", keys=["⌘ ,"], custom=False),
        Hotkey(command_id="editor:toggle-bold", keys=["⌘ B", "⌘ ⇧ B"], custom=True),
        Hotkey(command_id="editor:toggle-italics", keys=[], custom=True),
    ]
    cli._execute.assert_awaited_once_with(
        "hotkeys", flags=["verbose"], output_format="json"
    )


async def test_get(cli):
    cli._execute.return_value = "⌘ ⇧ F\n"
    result = await cli.hotkeys.get("global-search:open")
    assert result == "⌘ ⇧ F"
    cli._execute.assert_awaited_once_with(
        "hotkey", params={"id": "global-search:open"}, flags=None
    )


async def test_get_verbose(cli):
    cli._execute.return_value = "⌘ ⇧ F (default)\n"
    result = await cli.hotkeys.get("global-search:open", verbose=True)
    assert result == "⌘ ⇧ F (default)"
    cli._execute.assert_awaited_once_with(
        "hotkey", params={"id": "global-search:open"}, flags=["verbose"]
    )


async def test_get_without_hotkey(cli):
    cli._execute.return_value = "(none)\n"
    result = await cli.hotkeys.get("app:delete-file")
    assert result == "(none)"
