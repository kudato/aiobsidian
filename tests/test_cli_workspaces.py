from __future__ import annotations

import json

WORKSPACES = [
    {"name": "Default"},
    {"name": "Writing"},
    {"name": "Coding"},
]

CURRENT_WORKSPACE = {
    "type": "split",
    "children": [{"type": "leaf", "file": "note.md"}],
}


async def test_list(cli):
    cli._execute.return_value = json.dumps(WORKSPACES)
    result = await cli.workspaces.list()
    assert result == WORKSPACES
    cli._execute.assert_awaited_once_with("workspaces")


async def test_current(cli):
    cli._execute.return_value = json.dumps(CURRENT_WORKSPACE)
    result = await cli.workspaces.current()
    assert result == CURRENT_WORKSPACE
    cli._execute.assert_awaited_once_with("workspace")


async def test_save(cli):
    cli._execute.return_value = ""
    await cli.workspaces.save("Writing")
    cli._execute.assert_awaited_once_with("workspace:save", params={"name": "Writing"})


async def test_load(cli):
    cli._execute.return_value = ""
    await cli.workspaces.load("Writing")
    cli._execute.assert_awaited_once_with("workspace:load", params={"name": "Writing"})


async def test_delete(cli):
    cli._execute.return_value = ""
    await cli.workspaces.delete("Writing")
    cli._execute.assert_awaited_once_with(
        "workspace:delete", params={"name": "Writing"}
    )
