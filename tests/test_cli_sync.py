from __future__ import annotations

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.models.sync import SyncStatus

STATUS = (
    "status: synced\n"
    "vault: MyVault\n"
    "device: MacBook\n"
    "vault size: 3.2 MB\n"
    "account usage: 3.2 MB / 10 GB\n"
)

STATUS_NOT_SET_UP = "status: disconnected\nSync is not set up for this vault.\n"

HISTORY = (
    "0: 2026-08-16 02:38:11 (431 bytes) [MacBook]\n"
    "1: 2026-08-15 19:04:02 (388 bytes) [iPhone]\n"
)

DELETED = "2026-08-15 12:00:00: archive/old-note.md (120 bytes) [MacBook]\n"

VERSION = (
    "notes/todo.md (version 1, 2026-08-15 19:04:02)\n"
    "---\n"
    "---\ntitle: Todo\n---\n\n# Todo\n"
)


async def test_set_paused_true_pauses(cli):
    cli._execute.return_value = "Sync paused.\n"
    await cli.sync.set_paused(True)
    cli._execute.assert_awaited_once_with("sync", flags=["off"])


async def test_set_paused_false_resumes(cli):
    cli._execute.return_value = "Sync resumed.\n"
    await cli.sync.set_paused(False)
    cli._execute.assert_awaited_once_with("sync", flags=["on"])


async def test_open(cli):
    cli._execute.return_value = ""
    await cli.sync.open()
    cli._execute.assert_awaited_once_with("sync:open")


async def test_status(cli):
    cli._execute.return_value = STATUS
    result = await cli.sync.status()
    assert result == SyncStatus(
        status="synced",
        vault="MyVault",
        device="MacBook",
        vault_size="3.2 MB",
        account_used="3.2 MB",
        account_limit="10 GB",
    )
    cli._execute.assert_awaited_once_with("sync:status")


async def test_status_without_sync(cli):
    cli._execute.return_value = STATUS_NOT_SET_UP
    result = await cli.sync.status()
    assert result == SyncStatus(status="disconnected")
    assert result.vault is None
    assert result.vault_size is None
    assert result.account_used is None
    assert result.account_limit is None


async def test_status_without_the_quota(cli):
    # Obsidian asks its server for the quota and prints the vault and
    # the account sizes only once it answers.
    cli._execute.return_value = "status: syncing\nvault: MyVault\ndevice: MacBook\n"
    result = await cli.sync.status()
    assert result == SyncStatus(status="syncing", vault="MyVault", device="MacBook")


async def test_status_with_a_colon_in_the_device_name(cli):
    cli._execute.return_value = "status: synced\ndevice: MacBook: work\n"
    result = await cli.sync.status()
    assert result.device == "MacBook: work"


async def test_status_with_one_size_in_the_usage_line(cli):
    cli._execute.return_value = STATUS.replace(" / 10 GB", "")
    with pytest.raises(CLIParseError) as exc_info:
        await cli.sync.status()
    assert exc_info.value.command == "sync:status"


async def test_status_without_the_status_field(cli):
    cli._execute.return_value = "vault: MyVault\ndevice: MacBook\n"
    with pytest.raises(CLIParseError):
        await cli.sync.status()


async def test_history(cli):
    cli._execute.return_value = HISTORY
    result = await cli.sync.history("notes/todo.md")
    assert result == [
        "0: 2026-08-16 02:38:11 (431 bytes) [MacBook]",
        "1: 2026-08-15 19:04:02 (388 bytes) [iPhone]",
    ]
    cli._execute.assert_awaited_once_with(
        "sync:history", params={"path": "notes/todo.md"}
    )


async def test_history_without_versions(cli):
    cli._execute.return_value = "No sync history found for this file.\n"
    result = await cli.sync.history("notes/todo.md")
    assert result == []


async def test_read_drops_the_version_header(cli):
    cli._execute.return_value = VERSION
    result = await cli.sync.read("notes/todo.md", version=1)
    assert result == "---\ntitle: Todo\n---\n\n# Todo\n"
    cli._execute.assert_awaited_once_with(
        "sync:read", params={"path": "notes/todo.md", "version": "1"}
    )


async def test_restore(cli):
    cli._execute.return_value = "Restored notes/todo.md to version 1\n"
    await cli.sync.restore("notes/todo.md", version=1)
    cli._execute.assert_awaited_once_with(
        "sync:restore", params={"path": "notes/todo.md", "version": "1"}
    )


async def test_deleted(cli):
    cli._execute.return_value = DELETED
    result = await cli.sync.deleted()
    assert result == ["2026-08-15 12:00:00: archive/old-note.md (120 bytes) [MacBook]"]
    cli._execute.assert_awaited_once_with("sync:deleted")


async def test_deleted_when_none(cli):
    cli._execute.return_value = "No deleted files found in sync history.\n"
    result = await cli.sync.deleted()
    assert result == []
