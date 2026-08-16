from __future__ import annotations

import pytest

from aiobsidian._exceptions import CLIParseError

VERSIONS_OUTPUT = (
    "notes/todo.md\n1\t2026-08-16 02:38\t431 B\n2\t2026-08-15 21:04\t402 B\n"
)


async def test_versions(cli):
    cli._execute.return_value = VERSIONS_OUTPUT
    result = await cli.history.versions("notes/todo.md")
    assert result == [
        {"version": "1", "modified": "2026-08-16 02:38", "size": "431 B"},
        {"version": "2", "modified": "2026-08-15 21:04", "size": "402 B"},
    ]
    cli._execute.assert_awaited_once_with("history", params={"path": "notes/todo.md"})


async def test_versions_unexpected_row(cli):
    cli._execute.return_value = "notes/todo.md\n1\t2026-08-16 02:38\n"
    with pytest.raises(CLIParseError):
        await cli.history.versions("notes/todo.md")


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
    cli._execute.return_value = "notes/todo.md\nnotes/ideas.md\n"
    result = await cli.history.list()
    assert result == ["notes/todo.md", "notes/ideas.md"]
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
