from __future__ import annotations

from unittest.mock import call

import pytest

from aiobsidian._exceptions import CommandError, PartialWriteError


async def test_read(cli):
    cli._execute.return_value = "# Daily note"
    result = await cli.daily.read()
    assert result == "# Daily note"
    cli._execute.assert_awaited_once_with("daily:read")


async def test_path(cli):
    cli._execute.return_value = "Daily Notes/2026-03-09.md\n"
    result = await cli.daily.path()
    assert result == "Daily Notes/2026-03-09.md"
    cli._execute.assert_awaited_once_with("daily:path")


async def test_open(cli):
    cli._execute.return_value = "Opened: daily/2026-08-16.md\n"
    result = await cli.daily.open()
    assert result == "daily/2026-08-16.md"
    cli._execute.assert_awaited_once_with("daily")


async def test_append(cli):
    cli._execute.return_value = ""
    await cli.daily.append("new content")
    cli._execute.assert_awaited_once_with(
        "daily:append", params={"content": "new content"}
    )


async def test_prepend(cli):
    cli._execute.return_value = ""
    await cli.daily.prepend("first line")
    cli._execute.assert_awaited_once_with(
        "daily:prepend", params={"content": "first line"}
    )


async def test_append_with_backslash_escapes(cli):
    cli._execute.return_value = ""
    await cli.daily.append(r"C:\notes\temp")
    assert cli._execute.await_args_list == [
        call("daily:append", params={"content": "C:\\"}),
        call("daily:append", params={"content": "notes\\"}, flags=["inline"]),
        call("daily:append", params={"content": "temp"}, flags=["inline"]),
    ]


async def test_prepend_with_backslash_escapes(cli):
    cli._execute.return_value = ""
    await cli.daily.prepend(r"C:\notes\temp")
    assert cli._execute.await_args_list == [
        call("daily:prepend", params={"content": "temp"}),
        call("daily:prepend", params={"content": "notes\\"}, flags=["inline"]),
        call("daily:prepend", params={"content": "C:\\"}, flags=["inline"]),
    ]


async def test_append_that_fails_part_way_counts_what_landed(cli):
    # The command finds the note itself, so the error carries no path —
    # only how much of the content is already in it.
    failure = CommandError("daily:append", 0, "", "Error: Obsidian quit.")
    cli._execute.side_effect = ["", failure]
    with pytest.raises(PartialWriteError) as raised:
        await cli.daily.append(r"a\tb")
    assert raised.value.path is None
    assert raised.value.written == 1
    assert raised.value.total == 2
    assert raised.value.__cause__ is failure


async def test_prepend_that_fails_part_way_counts_what_landed(cli):
    failure = CommandError("daily:prepend", 0, "", "Error: Obsidian quit.")
    cli._execute.side_effect = ["", "", failure]
    with pytest.raises(PartialWriteError) as raised:
        await cli.daily.prepend(r"C:\notes\temp")
    assert raised.value.path is None
    assert raised.value.written == 2
    assert raised.value.total == 3
