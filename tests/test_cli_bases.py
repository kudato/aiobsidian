from __future__ import annotations

import json

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.bases import BaseView

RECORDS = [
    {"name": "Task 1", "status": "done"},
    {"name": "Task 2", "status": "todo"},
]


async def test_list(cli):
    cli._execute.return_value = "databases/tasks.base\ndatabases/contacts.base\n"
    result = await cli.bases.list()
    assert result == ["databases/tasks.base", "databases/contacts.base"]
    cli._execute.assert_awaited_once_with("bases")


async def test_views(cli):
    cli._execute.return_value = "All\ttable\nActive\tcards\n"
    result = await cli.bases.views()
    assert result == [
        BaseView(name="All", type="table"),
        BaseView(name="Active", type="cards"),
    ]
    cli._execute.assert_awaited_once_with("base:views")


async def test_views_with_an_unexpected_row(cli):
    cli._execute.return_value = "All\ttable\textra\n"
    with pytest.raises(CLIParseError) as exc_info:
        await cli.bases.views()
    assert exc_info.value.command == "base:views"


async def test_views_without_any(cli):
    cli._execute.return_value = "No views defined.\n"
    result = await cli.bases.views()
    assert result == []


async def test_create(cli):
    cli._execute.return_value = "Created: databases/New Task.md\n"
    await cli.bases.create("databases/tasks.base", name="New Task")
    cli._execute.assert_awaited_once_with(
        "base:create",
        params={"path": "databases/tasks.base", "name": "New Task"},
    )


async def test_create_with_view_and_content(cli):
    cli._execute.return_value = "Created: databases/New Task.md\n"
    await cli.bases.create(
        "databases/tasks.base", view="Active", name="New Task", content="# Task"
    )
    cli._execute.assert_awaited_once_with(
        "base:create",
        params={
            "path": "databases/tasks.base",
            "view": "Active",
            "name": "New Task",
            "content": "# Task",
        },
    )


async def test_query(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.base")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query", params={"path": "databases/tasks.base"}, output_format="json"
    )


async def test_query_empty_view(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.base", view="")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query",
        params={"path": "databases/tasks.base", "view": ""},
        output_format="json",
    )


async def test_query_with_view(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.base", view="Active")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query",
        params={"path": "databases/tasks.base", "view": "Active"},
        output_format="json",
    )
