from __future__ import annotations

import json

TASKS = [
    {"id": "1", "content": "Buy milk", "completed": False},
    {"id": "2", "content": "Write docs", "completed": True},
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list()
    assert result == TASKS
    cli._execute.assert_awaited_once_with("tasks", params=None, flags=None)


async def test_list_with_path(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(path="notes")
    assert result == TASKS
    cli._execute.assert_awaited_once_with("tasks", params={"path": "notes"}, flags=None)


async def test_list_daily(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(daily=True)
    assert result == TASKS
    cli._execute.assert_awaited_once_with("tasks", params=None, flags=["--daily"])


async def test_list_done(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(done=True)
    assert result == TASKS
    cli._execute.assert_awaited_once_with("tasks", params=None, flags=["--done"])


async def test_list_all_flags(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(path="notes", daily=True, done=True)
    assert result == TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params={"path": "notes"}, flags=["--daily", "--done"]
    )


async def test_create(cli):
    cli._execute.return_value = ""
    await cli.tasks.create("Buy milk")
    cli._execute.assert_awaited_once_with("task:create", params={"content": "Buy milk"})


async def test_create_with_tags(cli):
    cli._execute.return_value = ""
    await cli.tasks.create("Buy milk", tags="shopping,errands")
    cli._execute.assert_awaited_once_with(
        "task:create", params={"content": "Buy milk", "tags": "shopping,errands"}
    )


async def test_complete(cli):
    cli._execute.return_value = ""
    await cli.tasks.complete("1")
    cli._execute.assert_awaited_once_with("task:complete", params={"task": "1"})
