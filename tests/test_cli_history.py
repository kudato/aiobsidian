from __future__ import annotations

import json

HISTORY_FILES = [
    {"path": "notes/todo.md", "versions": 3},
    {"path": "notes/ideas.md", "versions": 1},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(HISTORY_FILES)
    result = await cli.history.list()
    assert result == HISTORY_FILES
    cli._execute.assert_awaited_once_with("history:list")


async def test_read(cli):
    cli._execute.return_value = "# Old content"
    result = await cli.history.read("notes/todo.md", version="v1")
    assert result == "# Old content"
    cli._execute.assert_awaited_once_with(
        "history:read", params={"path": "notes/todo.md", "version": "v1"}
    )


async def test_read_latest(cli):
    cli._execute.return_value = "# Latest content"
    result = await cli.history.read("notes/todo.md")
    assert result == "# Latest content"
    cli._execute.assert_awaited_once_with(
        "history:read", params={"path": "notes/todo.md"}
    )


async def test_restore(cli):
    cli._execute.return_value = ""
    await cli.history.restore("notes/todo.md", version="v1")
    cli._execute.assert_awaited_once_with(
        "history:restore", params={"path": "notes/todo.md", "version": "v1"}
    )
