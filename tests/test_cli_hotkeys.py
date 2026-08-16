from __future__ import annotations

import json

HOTKEYS = [
    {"id": "app:go-back", "hotkey": "⌘ ⌥ ←"},
    {"id": "app:delete-file", "hotkey": ""},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(HOTKEYS)
    result = await cli.hotkeys.list()
    assert result == HOTKEYS
    cli._execute.assert_awaited_once_with("hotkeys", output_format="json")


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
    cli._execute.return_value = "\n"
    result = await cli.hotkeys.get("app:delete-file")
    assert result == ""
