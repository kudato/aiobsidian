from __future__ import annotations

import json

TEMPLATES_LIST = [
    {"name": "Daily Note", "path": "templates/daily.md"},
    {"name": "Meeting", "path": "templates/meeting.md"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TEMPLATES_LIST)
    result = await cli.templates.list()
    assert result == TEMPLATES_LIST
    cli._execute.assert_awaited_once_with("templates")


async def test_read(cli):
    cli._execute.return_value = "# Template content"
    result = await cli.templates.read("Daily Note")
    assert result == "# Template content"
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


async def test_read_with_resolve(cli):
    cli._execute.return_value = "# 2025-01-01"
    result = await cli.templates.read("Daily Note", resolve=True)
    assert result == "# 2025-01-01"
    cli._execute.assert_awaited_once_with(
        "template:read",
        params={"name": "Daily Note"},
        flags=["--resolve"],
    )
