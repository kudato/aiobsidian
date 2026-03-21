from __future__ import annotations

import json

BASES = [
    {"path": "databases/tasks.md", "name": "Tasks"},
    {"path": "databases/contacts.md", "name": "Contacts"},
]

VIEWS = [
    {"name": "All", "type": "table"},
    {"name": "Active", "type": "board"},
]

RECORDS = [
    {"name": "Task 1", "status": "done"},
    {"name": "Task 2", "status": "todo"},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(BASES)
    result = await cli.bases.list()
    assert result == BASES
    cli._execute.assert_awaited_once_with("bases")


async def test_views(cli):
    cli._execute.return_value = json.dumps(VIEWS)
    result = await cli.bases.views("databases/tasks.md")
    assert result == VIEWS
    cli._execute.assert_awaited_once_with(
        "base:views", params={"file": "databases/tasks.md"}
    )


async def test_create(cli):
    cli._execute.return_value = ""
    await cli.bases.create("databases/tasks.md", name="New Task", status="todo")
    cli._execute.assert_awaited_once_with(
        "base:create",
        params={"file": "databases/tasks.md", "name": "New Task", "status": "todo"},
    )


async def test_query(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.md")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query", params={"file": "databases/tasks.md"}
    )


async def test_query_with_view(cli):
    cli._execute.return_value = json.dumps(RECORDS)
    result = await cli.bases.query("databases/tasks.md", view="Active")
    assert result == RECORDS
    cli._execute.assert_awaited_once_with(
        "base:query",
        params={"file": "databases/tasks.md", "view": "Active"},
    )
