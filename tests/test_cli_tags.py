from __future__ import annotations

import json

TAGS_LIST = [
    {"tag": "#python", "count": "15"},
    {"tag": "#obsidian", "count": "8"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list()
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with(
        "tags", params=None, flags=None, output_format="json"
    )


async def test_list_sorted(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list(sort="count")
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with(
        "tags", params={"sort": "count"}, flags=None, output_format="json"
    )


async def test_list_empty_sort(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list(sort="")
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with(
        "tags", params={"sort": ""}, flags=None, output_format="json"
    )


async def test_list_with_path(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list(path="notes")
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with(
        "tags", params={"path": "notes"}, flags=None, output_format="json"
    )


async def test_list_with_counts(cli):
    cli._execute.return_value = json.dumps(TAGS_LIST)
    result = await cli.tags.list(counts=True)
    assert result == TAGS_LIST
    cli._execute.assert_awaited_once_with(
        "tags", params=None, flags=["counts"], output_format="json"
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
