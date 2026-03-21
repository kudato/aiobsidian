from __future__ import annotations

import json

TAGS_LIST = [
    {"name": "python", "count": 15},
    {"name": "obsidian", "count": 8},
]

TAG_NOTES = [
    {"path": "projects/cli.md", "name": "cli"},
    {"path": "notes/setup.md", "name": "setup"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list()
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with("tags", params=None)


async def test_list_sorted(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list(sort="count")
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with("tags", params={"sort": "count"})


async def test_get(cli):
    cli._execute.return_value = json.dumps(TAG_NOTES)
    result = await cli.tags.get("python")
    assert result == TAG_NOTES
    cli._execute.assert_awaited_once_with("tag", params={"tagname": "python"})


async def test_rename(cli):
    cli._execute.return_value = ""
    await cli.tags.rename("old-tag", "new-tag")
    cli._execute.assert_awaited_once_with(
        "tags:rename", params={"old": "old-tag", "new": "new-tag"}
    )
