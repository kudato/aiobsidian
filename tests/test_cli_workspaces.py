from __future__ import annotations

WORKSPACE_TREE = """main
└── tabs
    ├── [markdown] welcome
    └── [markdown] notes
left
└── tabs
    └── [search] Search
"""


async def test_list(cli):
    cli._execute.return_value = "Default\nWriting\n"
    result = await cli.workspaces.list()
    assert result == ["Default", "Writing"]
    cli._execute.assert_awaited_once_with("workspaces")


async def test_list_none_saved(cli):
    cli._execute.return_value = "No workspaces saved.\n"
    result = await cli.workspaces.list()
    assert result == []


async def test_current(cli):
    cli._execute.return_value = WORKSPACE_TREE
    result = await cli.workspaces.current()
    assert result == WORKSPACE_TREE.strip()
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
