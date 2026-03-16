from __future__ import annotations

import json

SYNC_STATUS = {"enabled": True, "syncing": False, "lastSync": "2026-03-16T10:00:00Z"}

SYNC_HISTORY = [
    {"version": "abc123", "date": "2026-03-16T09:00:00Z"},
    {"version": "def456", "date": "2026-03-15T15:00:00Z"},
]

DELETED_FILES = [
    {"path": "archive/old-note.md", "deletedAt": "2026-03-15T12:00:00Z"},
]


async def test_status(cli):
    cli._execute.return_value = json.dumps(SYNC_STATUS)
    result = await cli.sync.status()
    assert result == SYNC_STATUS
    cli._execute.assert_awaited_once_with("sync:status")


async def test_history(cli):
    cli._execute.return_value = json.dumps(SYNC_HISTORY)
    result = await cli.sync.history("notes/todo.md")
    assert result == SYNC_HISTORY
    cli._execute.assert_awaited_once_with(
        "sync:history", params={"path": "notes/todo.md"}
    )


async def test_read(cli):
    cli._execute.return_value = "# Old version content"
    result = await cli.sync.read("notes/todo.md", version="abc123")
    assert result == "# Old version content"
    cli._execute.assert_awaited_once_with(
        "sync:read", params={"path": "notes/todo.md", "version": "abc123"}
    )


async def test_restore(cli):
    cli._execute.return_value = ""
    await cli.sync.restore("notes/todo.md", version="abc123")
    cli._execute.assert_awaited_once_with(
        "sync:restore", params={"path": "notes/todo.md", "version": "abc123"}
    )


async def test_deleted(cli):
    cli._execute.return_value = json.dumps(DELETED_FILES)
    result = await cli.sync.deleted()
    assert result == DELETED_FILES
    cli._execute.assert_awaited_once_with("sync:deleted")
