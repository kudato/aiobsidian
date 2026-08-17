from __future__ import annotations

import json

from aiobsidian.models.tasks import Task

# `text` is the task's line with its indentation trimmed off and its
# marker kept, and the line number arrives as a string. The status is
# whatever stands between the brackets, so a theme's custom status shows
# up as itself.
TASKS = [
    {"status": " ", "text": "- [ ] Buy milk", "file": "todo.md", "line": "3"},
    {"status": "x", "text": "- [x] Write docs", "file": "todo.md", "line": "4"},
    {"status": "/", "text": "- [/] Read the RFC", "file": "todo.md", "line": "5"},
]

# `done` selects everything whose box is not blank, custom statuses
# included; `todo` selects only the blank ones.
DONE_TASKS = [TASKS[1], TASKS[2]]
TODO_TASKS = [TASKS[0]]

PARSED_TASKS = [
    Task(status=" ", text="- [ ] Buy milk", file="todo.md", line=3),
    Task(status="x", text="- [x] Write docs", file="todo.md", line=4),
    Task(status="/", text="- [/] Read the RFC", file="todo.md", line=5),
]


async def test_list(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list()
    assert result == PARSED_TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=None, output_format="json"
    )


async def test_list_reports_the_line_as_a_number(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list()
    assert result[0].line == 3
    await cli.tasks.complete(result[0].file, result[0].line)
    cli._execute.assert_awaited_with(
        "task", params={"path": "todo.md", "line": "3"}, flags=["done"]
    )


async def test_list_tells_an_open_task_from_any_other(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list()
    assert [task.done for task in result] == [False, True, True]
    assert result[0].model_dump()["done"] is False


async def test_list_no_tasks(cli):
    cli._execute.return_value = "No tasks found.\n"
    result = await cli.tasks.list(path="notes/empty.md")
    assert result == []


async def test_list_with_path(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(path="todo.md")
    assert result == PARSED_TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params={"path": "todo.md"}, flags=None, output_format="json"
    )


async def test_list_daily(cli):
    cli._execute.return_value = json.dumps(TASKS)
    result = await cli.tasks.list(daily=True)
    assert result == PARSED_TASKS
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["daily"], output_format="json"
    )


async def test_list_done_returns_every_filled_box(cli):
    cli._execute.return_value = json.dumps(DONE_TASKS)
    result = await cli.tasks.list(done=True)
    assert result == [PARSED_TASKS[1], PARSED_TASKS[2]]
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["done"], output_format="json"
    )


async def test_list_todo(cli):
    cli._execute.return_value = json.dumps(TODO_TASKS)
    result = await cli.tasks.list(todo=True)
    assert result == [PARSED_TASKS[0]]
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["todo"], output_format="json"
    )


async def test_list_daily_and_done(cli):
    cli._execute.return_value = json.dumps(DONE_TASKS)
    result = await cli.tasks.list(daily=True, done=True)
    assert result == [PARSED_TASKS[1], PARSED_TASKS[2]]
    cli._execute.assert_awaited_once_with(
        "tasks", params=None, flags=["daily", "done"], output_format="json"
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
