from __future__ import annotations


async def test_read(cli):
    cli._execute.return_value = "# Daily note"
    result = await cli.daily.read()
    assert result == "# Daily note"
    cli._execute.assert_awaited_once_with("daily:read", params=None)


async def test_read_with_date(cli):
    cli._execute.return_value = "# March 15"
    result = await cli.daily.read(date="2026-03-15")
    assert result == "# March 15"
    cli._execute.assert_awaited_once_with(
        "daily:read", params={"date": "2026-03-15"}
    )


async def test_path(cli):
    cli._execute.return_value = "Daily Notes/2026-03-09.md\n"
    result = await cli.daily.path()
    assert result == "Daily Notes/2026-03-09.md"
    cli._execute.assert_awaited_once_with("daily:path")


async def test_create(cli):
    cli._execute.return_value = ""
    await cli.daily.create()
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
