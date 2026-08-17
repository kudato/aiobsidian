from __future__ import annotations

import json

from aiobsidian.models.hotkeys import Hotkey

# The listing covers every command, bound or not, sorted by id. `verbose`
# adds the column that tells a binding the user set from one Obsidian
# ships. Several bindings on one command arrive joined by `", "` in that
# single column — `workspace:next-tab` ships with two — and a binding can
# itself be a comma. The last row is a default the user cleared, which is
# the only way a binding reads as the user's while having no keys.
HOTKEYS = [
    {"id": "app:delete-file", "hotkey": "", "custom": "default"},
    {"id": "app:go-back", "hotkey": "⌘ ⌥ ←", "custom": "default"},
    {"id": "app:open-settings", "hotkey": "⌘ ,", "custom": "default"},
    {"id": "workspace:next-tab", "hotkey": "⌃ Tab, ⌘ ⇧ ]", "custom": "default"},
    {"id": "editor:toggle-bold", "hotkey": "", "custom": "custom"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(HOTKEYS)
    result = await cli.hotkeys.list()
    assert result == [
        Hotkey(command_id="app:delete-file", keys=[], custom=False),
        Hotkey(command_id="app:go-back", keys=["⌘ ⌥ ←"], custom=False),
        Hotkey(command_id="app:open-settings", keys=["⌘ ,"], custom=False),
        Hotkey(command_id="workspace:next-tab", keys=["⌃ Tab", "⌘ ⇧ ]"], custom=False),
        Hotkey(command_id="editor:toggle-bold", keys=[], custom=True),
    ]
    cli._execute.assert_awaited_once_with(
        "hotkeys", flags=["verbose"], output_format="json"
    )


async def test_get(cli):
    cli._execute.return_value = "⌘ ⇧ F\n"
    result = await cli.hotkeys.get("global-search:open")
    assert result == ["⌘ ⇧ F"]
    cli._execute.assert_awaited_once_with("hotkey", params={"id": "global-search:open"})


async def test_get_several_bindings(cli):
    cli._execute.return_value = "⌃ Tab, ⌘ ⇧ ]\n"
    result = await cli.hotkeys.get("workspace:next-tab")
    assert result == ["⌃ Tab", "⌘ ⇧ ]"]


async def test_get_binding_that_is_a_comma(cli):
    cli._execute.return_value = "⌘ ,\n"
    result = await cli.hotkeys.get("app:open-settings")
    assert result == ["⌘ ,"]


async def test_get_without_hotkey(cli):
    cli._execute.return_value = "(none)\n"
    result = await cli.hotkeys.get("app:delete-file")
    assert result == []
