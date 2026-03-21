from __future__ import annotations

import json


async def test_list(cli):
    props = {"title": "My Note", "tags": ["a", "b"]}
    cli._execute.return_value = json.dumps(props)
    result = await cli.properties.list("note.md")
    assert result == props
    cli._execute.assert_awaited_once_with("properties", params={"path": "note.md"})


async def test_read(cli):
    cli._execute.return_value = json.dumps("My Note")
    result = await cli.properties.read("note.md", "title")
    assert result == "My Note"
    cli._execute.assert_awaited_once_with(
        "property:read", params={"path": "note.md", "property": "title"}
    )


async def test_set(cli):
    cli._execute.return_value = ""
    await cli.properties.set("note.md", "title", "New Title")
    cli._execute.assert_awaited_once_with(
        "property:set",
        params={"path": "note.md", "property": "title", "value": "New Title"},
    )


async def test_remove(cli):
    cli._execute.return_value = ""
    await cli.properties.remove("note.md", "title")
    cli._execute.assert_awaited_once_with(
        "property:remove", params={"path": "note.md", "property": "title"}
    )
