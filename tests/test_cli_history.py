from __future__ import annotations

from datetime import datetime

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.history import FileVersion

# The CLI names the file on its own line and then numbers the versions
# from 1, newest first. The timestamp is printed to the minute with no
# timezone, and the size is already rounded and carries its unit.
VERSIONS_OUTPUT = (
    "notes/todo.md\n1\t2026-08-16 02:38\t431 B\n2\t2026-08-15 21:04\t402 B\n"
)


async def test_versions(cli):
    cli._execute.return_value = VERSIONS_OUTPUT
    result = await cli.history.versions("notes/todo.md")
    assert result == [
        FileVersion(version=1, modified=datetime(2026, 8, 16, 2, 38), size="431 B"),
        FileVersion(version=2, modified=datetime(2026, 8, 15, 21, 4), size="402 B"),
    ]
    cli._execute.assert_awaited_once_with("history", params={"path": "notes/todo.md"})


async def test_versions_number_what_read_takes(cli):
    cli._execute.return_value = VERSIONS_OUTPUT
    result = await cli.history.versions("notes/todo.md")
    await cli.history.read("notes/todo.md", version=result[1].version)
    cli._execute.assert_awaited_with(
        "history:read", params={"path": "notes/todo.md", "version": "2"}
    )


async def test_versions_with_an_unreadable_timestamp(cli):
    cli._execute.return_value = "notes/todo.md\n1\tyesterday\t431 B\n"
    with pytest.raises(CLIParseError):
        await cli.history.versions("notes/todo.md")


async def test_versions_with_an_unexpected_row(cli):
    cli._execute.return_value = "notes/todo.md\n1\t2026-08-16 02:38\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.history.versions("notes/todo.md")
    assert exc_info.value.command == "history"


async def test_versions_in_a_language_that_renumbers_the_digits(cli):
    # Obsidian formats the timestamp under the locale of its own UI
    # language, and an Arabic one prints Arabic-Indic digits.
    cli._execute.return_value = (
        "notes/todo.md\n1\t\u0662\u0660\u0662\u0666-\u0660\u0668-"
        "\u0661\u0666 \u0660\u0662:\u0663\u0668\t431 B\n"
    )
    result = await cli.history.versions("notes/todo.md")
    assert result[0].modified == datetime(2026, 8, 16, 2, 38)


async def test_versions_without_any(cli):
    cli._execute.return_value = "No history found for this file.\n"
    result = await cli.history.versions("notes/fresh.md")
    assert result == []


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.history.open("notes/todo.md")
    cli._execute.assert_awaited_once_with(
        "history:open", params={"path": "notes/todo.md"}
    )


# With neither version given the command lists the versions instead of
# diffing, local and synced ones together, padded into columns.
DIFF_LISTING = (
    "notes/todo.md\n"
    "1   Local 2026-08-16 02:38:11       431 B  \n"
    "2   Sync  2026-08-15 21:04:57       402 B  [MacBook]\n"
)

# `---` names the version diffed from and `+++` the one diffed to, so
# these follow the arguments `test_diff_all_params` sends.
DIFF_OUTPUT = (
    "--- notes/todo.md (Local #1, 2026-08-16 02:38:11)\n"
    "+++ notes/todo.md (Local #2, 2026-08-15 21:04:57)\n"
    "- new line\n"
    "+ old line\n"
)


async def test_diff_without_versions_passes_the_listing_through(cli):
    cli._execute.return_value = DIFF_LISTING
    result = await cli.history.diff("notes/todo.md")
    assert result == DIFF_LISTING
    cli._execute.assert_awaited_once_with("diff", params={"path": "notes/todo.md"})


async def test_diff_all_params(cli):
    cli._execute.return_value = DIFF_OUTPUT
    result = await cli.history.diff(
        "notes/todo.md", from_version=1, to_version=2, filter="local"
    )
    assert result == DIFF_OUTPUT
    cli._execute.assert_awaited_once_with(
        "diff",
        params={
            "path": "notes/todo.md",
            "from": "1",
            "to": "2",
            "filter": "local",
        },
    )


async def test_list(cli):
    cli._execute.return_value = "notes/todo.md\nnotes/ideas.md\n"
    result = await cli.history.list()
    assert result == ["notes/todo.md", "notes/ideas.md"]
    cli._execute.assert_awaited_once_with("history:list")


async def test_read_drops_the_version_header(cli):
    cli._execute.return_value = (
        "notes/todo.md (version 1, 2026-08-16 02:38)\n"
        "---\n"
        "---\ntitle: Todo\n---\n\n# Old content\n"
    )
    result = await cli.history.read("notes/todo.md", version=1)
    assert result == "---\ntitle: Todo\n---\n\n# Old content\n"
    cli._execute.assert_awaited_once_with(
        "history:read", params={"path": "notes/todo.md", "version": "1"}
    )


async def test_read_latest(cli):
    cli._execute.return_value = (
        "notes/todo.md (version 1, 2026-08-16 02:38)\n---\n# Latest content\n"
    )
    result = await cli.history.read("notes/todo.md")
    assert result == "# Latest content\n"
    cli._execute.assert_awaited_once_with(
        "history:read", params={"path": "notes/todo.md"}
    )


async def test_restore(cli):
    cli._execute.return_value = ""
    await cli.history.restore("notes/todo.md", version=2)
    cli._execute.assert_awaited_once_with(
        "history:restore", params={"path": "notes/todo.md", "version": "2"}
    )
