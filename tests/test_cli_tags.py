from __future__ import annotations

import json

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.tags import Tag

# The CLI sorts by tag name unless `sort=count` asks otherwise, and these
# two happen to fall the same way under both orders. It prints the tag
# with its sigil, and the count as a string.
TAGS = [
    {"tag": "#obsidian", "count": "15"},
    {"tag": "#python", "count": "8"},
]

PARSED_TAGS = [Tag(name="obsidian", count=15), Tag(name="python", count=8)]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TAGS)
    result = await cli.tags.list()
    assert result == PARSED_TAGS
    cli._execute.assert_awaited_once_with(
        "tags", params=None, flags=["counts"], output_format="json"
    )


async def test_list_drops_the_sigil(cli):
    cli._execute.return_value = json.dumps([{"tag": "#project/cli", "count": "3"}])
    result = await cli.tags.list()
    assert result[0].name == "project/cli"


async def test_list_without_a_string_tag(cli):
    cli._execute.return_value = json.dumps([{"tag": 7, "count": "3"}])
    with pytest.raises(CLIParseError):
        await cli.tags.list()


async def test_list_sorted(cli):
    cli._execute.return_value = json.dumps(TAGS)
    result = await cli.tags.list(sort="count")
    assert result == PARSED_TAGS
    cli._execute.assert_awaited_once_with(
        "tags", params={"sort": "count"}, flags=["counts"], output_format="json"
    )


async def test_list_with_path(cli):
    cli._execute.return_value = json.dumps(TAGS)
    result = await cli.tags.list(path="notes/setup.md")
    assert result == PARSED_TAGS
    cli._execute.assert_awaited_once_with(
        "tags",
        params={"path": "notes/setup.md"},
        flags=["counts"],
        output_format="json",
    )


async def test_list_without_tags(cli):
    cli._execute.return_value = "No tags found.\n"
    result = await cli.tags.list()
    assert result == []


async def test_get(cli):
    cli._execute.return_value = "projects/cli.md\nnotes/setup.md\n"
    result = await cli.tags.get("python")
    assert result == ["projects/cli.md", "notes/setup.md"]
    cli._execute.assert_awaited_once_with("tag", params={"name": "python"})
