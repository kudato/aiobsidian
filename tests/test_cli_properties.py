from __future__ import annotations

import json

import pytest

from aiobsidian import PropertyType
from aiobsidian._exceptions import CLIParseError


async def test_list(cli):
    props = {"title": "My Note", "rating": 4, "tags": ["a", "b"], "done": True}
    cli._execute.return_value = json.dumps(props)
    result = await cli.properties.list("note.md")
    assert result == props
    cli._execute.assert_awaited_once_with(
        "properties", params={"path": "note.md"}, output_format="json"
    )


async def test_list_without_properties(cli):
    cli._execute.return_value = "No frontmatter found.\n"
    result = await cli.properties.list("note.md")
    assert result == {}


async def test_list_of_something_that_is_not_a_note_s_properties(cli):
    # Valid JSON of the wrong shape used to come back as it arrived,
    # typed as the mapping it is not.
    cli._execute.return_value = json.dumps(["title", "rating"])
    with pytest.raises(CLIParseError) as exc_info:
        await cli.properties.list("note.md")
    assert exc_info.value.command == "properties"


async def test_read(cli):
    cli._execute.return_value = "Welcome\n"
    result = await cli.properties.read("note.md", "title")
    assert result == "Welcome"
    cli._execute.assert_awaited_once_with(
        "property:read", params={"path": "note.md", "name": "title"}
    )


async def test_read_number_comes_back_as_text(cli):
    cli._execute.return_value = "4\n"
    result = await cli.properties.read("note.md", "rating")
    assert result == "4"


async def test_read_checkbox_comes_back_as_text(cli):
    cli._execute.return_value = "true\n"
    result = await cli.properties.read("note.md", "done")
    assert result == "true"


async def test_read_list(cli):
    cli._execute.return_value = "draft\npython\n"
    result = await cli.properties.read("note.md", "tags")
    assert result == ["draft", "python"]


async def test_read_empty_value(cli):
    cli._execute.return_value = "(empty)\n"
    result = await cli.properties.read("note.md", "summary")
    assert result is None


async def test_set_string(cli):
    cli._execute.return_value = "Set title: New Title\n"
    await cli.properties.set("note.md", "title", "New Title")
    cli._execute.assert_awaited_once_with(
        "property:set",
        params={
            "path": "note.md",
            "name": "title",
            "value": "New Title",
            "type": "text",
        },
    )


async def test_set_number(cli):
    cli._execute.return_value = "Set rating: 4\n"
    await cli.properties.set("note.md", "rating", 4)
    cli._execute.assert_awaited_once_with(
        "property:set",
        params={"path": "note.md", "name": "rating", "value": "4", "type": "number"},
    )


async def test_set_boolean(cli):
    cli._execute.return_value = "Set done: true\n"
    await cli.properties.set("note.md", "done", True)
    cli._execute.assert_awaited_once_with(
        "property:set",
        params={
            "path": "note.md",
            "name": "done",
            "value": "true",
            "type": "checkbox",
        },
    )


async def test_set_list_travels_as_json(cli):
    cli._execute.return_value = "Set tags: draft, a, b\n"
    await cli.properties.set("note.md", "tags", ["draft", "a, b"])
    cli._execute.assert_awaited_once_with(
        "property:set",
        params={"path": "note.md", "name": "tags", "value": '["draft", "a, b"]'},
    )


async def test_set_with_explicit_type(cli):
    cli._execute.return_value = "Set due: 2026-08-16\n"
    await cli.properties.set(
        "note.md", "due", "2026-08-16", property_type=PropertyType.DATE
    )
    cli._execute.assert_awaited_once_with(
        "property:set",
        params={
            "path": "note.md",
            "name": "due",
            "value": "2026-08-16",
            "type": "date",
        },
    )


async def test_set_rejects_none(cli):
    with pytest.raises(TypeError, match="cannot be NoneType"):
        await cli.properties.set("note.md", "title", None)
    cli._execute.assert_not_awaited()


async def test_set_rejects_mapping(cli):
    with pytest.raises(TypeError, match="cannot be dict"):
        await cli.properties.set("note.md", "title", {"a": 1})
    cli._execute.assert_not_awaited()


async def test_remove(cli):
    cli._execute.return_value = "Removed: title\n"
    await cli.properties.remove("note.md", "title")
    cli._execute.assert_awaited_once_with(
        "property:remove", params={"path": "note.md", "name": "title"}
    )
