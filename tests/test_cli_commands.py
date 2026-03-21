from __future__ import annotations

import json

COMMANDS_LIST = [
    {"id": "editor:toggle-bold", "name": "Toggle bold"},
    {"id": "editor:toggle-italics", "name": "Toggle italics"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(COMMANDS_LIST)
    result = await cli.commands.list()
    assert result == COMMANDS_LIST
    cli._execute.assert_awaited_once_with("commands", params=None)


async def test_list_filtered(cli):
    cli._execute.return_value = json.dumps(COMMANDS_LIST)
    result = await cli.commands.list(filter="editor")
    assert result == COMMANDS_LIST
    cli._execute.assert_awaited_once_with("commands", params={"filter": "editor"})


async def test_execute(cli):
    cli._execute.return_value = ""
    await cli.commands.execute("editor:toggle-bold")
    cli._execute.assert_awaited_once_with(
        "command", params={"id": "editor:toggle-bold"}
    )
