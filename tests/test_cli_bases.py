from __future__ import annotations

import json

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
    cli._execute.return_value = "All\nActive\n"
    result = await cli.bases.views("databases/tasks.base")
    assert result == ["All", "Active"]
    cli._execute.assert_awaited_once_with(
        "base:views", params={"file": "databases/tasks.base"}
    )


async def test_create(cli):
    cli._execute.return_value = ""
    await cli.bases.create("databases/tasks.base", name="New Task", status="todo")
    cli._execute.assert_awaited_once_with(
        "base:create",
        params={"file": "databases/tasks.base", "name": "New Task", "status": "todo"},
    )


async def test_query(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.base")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query", params={"file": "databases/tasks.base"}, output_format="json"
    )


async def test_query_empty_view(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.base", view="")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query",
        params={"file": "databases/tasks.base", "view": ""},
        output_format="json",
    )


async def test_query_with_view(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.base", view="Active")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query",
        params={"file": "databases/tasks.base", "view": "Active"},
        output_format="json",
    )
