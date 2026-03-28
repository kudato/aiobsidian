from __future__ import annotations

import json

HISTORY_FILES = [
    {"path": "notes/todo.md", "versions": 3},
    {"path": "notes/ideas.md", "versions": 1},
]


async def test_versions(cli):
    versions = [
        {"version": "v1", "date": "2026-03-16T09:00:00Z"},
        {"version": "v2", "date": "2026-03-16T10:00:00Z"},
    ]
    cli._execute.return_value = json.dumps(versions)
    result = await cli.history.versions("notes/todo.md")
    assert result == versions
    cli._execute.assert_awaited_once_with("history", params={"path": "notes/todo.md"})


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.history.open("notes/todo.md")
    cli._execute.assert_awaited_once_with(
        "history:open", params={"path": "notes/todo.md"}
    )


async def test_diff(cli):
    cli._execute.return_value = "- old line\n+ new line"
    result = await cli.history.diff("notes/todo.md")
    assert result == "- old line\n+ new line"
    cli._execute.assert_awaited_once_with("diff", params={"path": "notes/todo.md"})


async def test_diff_all_params(cli):
    cli._execute.return_value = "- old\n+ new"
    result = await cli.history.diff(
        "notes/todo.md", from_version="v1", to_version="v2", filter="added"
    )
    assert result == "- old\n+ new"
    cli._execute.assert_awaited_once_with(
        "diff",
        params={
            "path": "notes/todo.md",
            "from": "v1",
            "to": "v2",
            "filter": "added",
        },
    )


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
