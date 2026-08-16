from __future__ import annotations

COMMANDS_OUTPUT = "app:delete-file\napp:go-back\neditor:toggle-bold\n"
COMMAND_IDS = ["app:delete-file", "app:go-back", "editor:toggle-bold"]


async def test_list(cli):
    cli._execute.return_value = COMMANDS_OUTPUT
    result = await cli.commands.list()
    assert result == COMMAND_IDS
    cli._execute.assert_awaited_once_with("commands", params=None)


async def test_list_filtered(cli):
    cli._execute.return_value = "editor:toggle-bold\n"
    result = await cli.commands.list(filter="editor")
    assert result == ["editor:toggle-bold"]
    cli._execute.assert_awaited_once_with("commands", params={"filter": "editor"})


async def test_list_empty(cli):
    cli._execute.return_value = ""
    result = await cli.commands.list()
    assert result == []


async def test_execute(cli):
    cli._execute.return_value = ""
    await cli.commands.execute("editor:toggle-bold")
    cli._execute.assert_awaited_once_with(
        "command", params={"id": "editor:toggle-bold"}
    )
