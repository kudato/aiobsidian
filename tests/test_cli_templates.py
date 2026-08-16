from __future__ import annotations


async def test_insert(cli):
    cli._execute.return_value = ""
    await cli.templates.insert("Daily Note")
    cli._execute.assert_awaited_once_with(
        "template:insert", params={"name": "Daily Note"}
    )


async def test_list(cli):
    cli._execute.return_value = "Daily\nMeeting\n"
    result = await cli.templates.list()
    assert result == ["Daily", "Meeting"]
    cli._execute.assert_awaited_once_with("templates")


async def test_read_keeps_whitespace(cli):
    cli._execute.return_value = "# Template content\n\n- [ ] \n"
    result = await cli.templates.read("Daily Note")
    assert result == "# Template content\n\n- [ ] \n"
    cli._execute.assert_awaited_once_with(
        "template:read", params={"name": "Daily Note"}, flags=None
    )


async def test_read_with_title(cli):
    cli._execute.return_value = "# My Title"
    result = await cli.templates.read("Daily Note", title="My Title")
    assert result == "# My Title"
    cli._execute.assert_awaited_once_with(
        "template:read",
        params={"name": "Daily Note", "title": "My Title"},
        flags=None,
    )


async def test_read_empty_title(cli):
    cli._execute.return_value = "# Template content"
    result = await cli.templates.read("Daily Note", title="")
    assert result == "# Template content"
    cli._execute.assert_awaited_once_with(
        "template:read",
        params={"name": "Daily Note", "title": ""},
        flags=None,
    )


async def test_read_with_resolve(cli):
    cli._execute.return_value = "# 2025-01-01"
    result = await cli.templates.read("Daily Note", resolve=True)
    assert result == "# 2025-01-01"
    cli._execute.assert_awaited_once_with(
        "template:read",
        params={"name": "Daily Note"},
        flags=["resolve"],
    )
