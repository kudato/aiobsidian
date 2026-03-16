from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aiobsidian._cli import ObsidianCLI
from aiobsidian._exceptions import (
    BinaryNotFoundError,
    CLITimeoutError,
    CommandError,
)


class TestResolveBinary:
    def test_auto_found(self):
        with patch("shutil.which", return_value="/usr/bin/obsidian"):
            cli = ObsidianCLI("TestVault")
        assert cli._binary == "/usr/bin/obsidian"

    def test_auto_not_found(self):
        with patch("shutil.which", return_value=None):
            with pytest.raises(BinaryNotFoundError):
                ObsidianCLI("TestVault")

    def test_explicit_path(self):
        cli = ObsidianCLI("TestVault", binary="/custom/obsidian")
        assert cli._binary == "/custom/obsidian"


class TestRepr:
    def test_repr(self):
        cli = ObsidianCLI("MyVault", binary="/usr/bin/obsidian")
        assert repr(cli) == ("ObsidianCLI(vault='MyVault', binary='/usr/bin/obsidian')")


class TestContextManager:
    async def test_context_manager(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        async with cli as c:
            assert c is cli


class TestExecute:
    async def test_success(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            result = await cli._execute("read", params={"path": "note.md"})

        assert result == "output"
        mock_exec.assert_awaited_once_with(
            "/usr/bin/obsidian",
            "read",
            "vault=TestVault",
            "format=json",
            "path=note.md",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def test_command_error(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"file not found")
        mock_process.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(CommandError) as exc_info:
                await cli._execute("read", params={"path": "missing.md"})

        assert exc_info.value.command == "read"
        assert exc_info.value.exit_code == 1
        assert exc_info.value.stderr == "file not found"

    async def test_timeout(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian", timeout=1.0)

        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(CLITimeoutError) as exc_info:
                await cli._execute("read", params={"path": "slow.md"})

        assert exc_info.value.command == "read"
        assert exc_info.value.timeout == 1.0
        mock_process.kill.assert_called_once()

    async def test_stderr_warning(self, caplog):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"some warning")
        mock_process.returncode = 0

        with (
            patch("asyncio.create_subprocess_exec", return_value=mock_process),
            caplog.at_level(logging.WARNING),
        ):
            result = await cli._execute("read")

        assert result == "output"
        assert "some warning" in caplog.text

    async def test_with_flags(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")

        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"")
        mock_process.returncode = 0

        with patch(
            "asyncio.create_subprocess_exec", return_value=mock_process
        ) as mock_exec:
            await cli._execute(
                "create",
                params={"path": "note.md"},
                flags=["--overwrite"],
            )

        mock_exec.assert_awaited_once_with(
            "/usr/bin/obsidian",
            "create",
            "vault=TestVault",
            "format=json",
            "path=note.md",
            "--overwrite",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

    async def test_timeout_override(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian", timeout=30.0)

        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(CLITimeoutError) as exc_info:
                await cli._execute("read", timeout=5.0)

        assert exc_info.value.timeout == 5.0


class TestResources:
    def test_vault_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.vault import CLIVaultResource

        assert isinstance(cli.vault, CLIVaultResource)

    def test_daily_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.daily import CLIDailyResource

        assert isinstance(cli.daily, CLIDailyResource)

    def test_search_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.search import CLISearchResource

        assert isinstance(cli.search, CLISearchResource)

    def test_properties_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.properties import CLIPropertiesResource

        assert isinstance(cli.properties, CLIPropertiesResource)

    def test_tags_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.tags import CLITagsResource

        assert isinstance(cli.tags, CLITagsResource)

    def test_links_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.links import CLILinksResource

        assert isinstance(cli.links, CLILinksResource)

    def test_tasks_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.tasks import CLITasksResource

        assert isinstance(cli.tasks, CLITasksResource)

    def test_commands_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.commands import CLICommandsResource

        assert isinstance(cli.commands, CLICommandsResource)

    def test_templates_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.templates import CLITemplatesResource

        assert isinstance(cli.templates, CLITemplatesResource)

    def test_bookmarks_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.bookmarks import CLIBookmarksResource

        assert isinstance(cli.bookmarks, CLIBookmarksResource)
