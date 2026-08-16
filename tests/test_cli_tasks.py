from __future__ import annotations

import json

TASKS = [
    {"status": " ", "text": "- [ ] Buy milk", "file": "todo.md", "line": "3"},
    {"status": "x", "text": "- [x] Write docs", "file": "todo.md", "line": "4"},
]

DONE_TASKS = [TASKS[1]]
TODO_TASKS = [TASKS[0]]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list()
    assert result == TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=None, output_format="json"
    )


async def test_list_no_tasks(cli):
    cli._execute.return_value = "No tasks found.\n"
    result = await cli.tasks.list(path="notes/empty.md")
    assert result == []


async def test_list_with_path(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(path="notes")
    assert result == TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params={"path": "notes"}, flags=None, output_format="json"
    )


async def test_list_daily(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(daily=True)
    assert result == TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["daily"], output_format="json"
    )


async def test_list_done_returns_completed_only(cli):
    cli._execute.return_value = json.dumps(DONE_TASKS)
    result = await cli.tasks.list(done=True)
    assert result == DONE_TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["done"], output_format="json"
    )


async def test_list_todo(cli):
    cli._execute.return_value = json.dumps(TODO_TASKS)
    result = await cli.tasks.list(todo=True)
    assert result == TODO_TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["todo"], output_format="json"
    )


async def test_list_all_flags(cli):
    cli._execute.return_value = json.dumps(DONE_TASKS)
    result = await cli.tasks.list(path="notes", daily=True, done=True)
    assert result == DONE_TASKS
    cli._execute.assert_awaited_once_with(
        "tasks",
        params={"path": "notes"},
        flags=["daily", "done"],
        output_format="json",
    )


async def test_toggle(cli):
    cli._execute.return_value = "todo.md:5 [x] Buy milk\n"
    await cli.tasks.toggle("todo.md", 5)
    cli._execute.assert_awaited_once_with(
        "task", params={"path": "todo.md", "line": "5"}, flags=["toggle"]
    )


async def test_complete(cli):
    cli._execute.return_value = "todo.md:5 [x] Buy milk\n"
    await cli.tasks.complete("todo.md", 5)
    cli._execute.assert_awaited_once_with(
        "task", params={"path": "todo.md", "line": "5"}, flags=["done"]
    )


async def test_reopen(cli):
    cli._execute.return_value = "todo.md:5 [ ] Buy milk\n"
    await cli.tasks.reopen("todo.md", 5)
    cli._execute.assert_awaited_once_with(
        "task", params={"path": "todo.md", "line": "5"}, flags=["todo"]
    )
