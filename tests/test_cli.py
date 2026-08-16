from __future__ import annotations

import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aiobsidian._cli import ObsidianCLI
from aiobsidian._exceptions import (
    BinaryNotFoundError,
    CLINotFoundError,
    CLITimeoutError,
    CommandError,
    NotFoundError,
)

SPAWN_KWARGS = {
    "stdin": asyncio.subprocess.DEVNULL,
    "stdout": asyncio.subprocess.PIPE,
    "stderr": asyncio.subprocess.PIPE,
    "start_new_session": True,
}


@pytest.fixture(autouse=True)
def guard_killpg(request):
    """Keep os.killpg away from process groups the tests do not own.

    A mocked process answers `.pid` with a MagicMock, and MagicMock
    coerces to 1 through `__index__`, so an unguarded `_kill` would ask
    the OS to SIGKILL process group 1. A desktop refuses that; a
    container running as root would not.
    """
    if "real_processes" in request.keywords:
        yield None
        return
    with patch("aiobsidian._cli.os.killpg") as killpg:
        yield killpg


def _mock_process(
    stdout: bytes = b"",
    stderr: bytes = b"",
    returncode: int = 0,
) -> AsyncMock:
    process = AsyncMock()
    process.communicate.return_value = (stdout, stderr)
    process.returncode = returncode
    return process


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

    async def test_leaving_the_block_closes_the_client(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        async with cli:
            pass

        with pytest.raises(RuntimeError, match="has been closed"):
            await cli._execute("version")


class TestClose:
    async def test_command_after_aclose_raises(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        await cli.aclose()

        with pytest.raises(RuntimeError, match="'version'"):
            await cli._execute("version")

    async def test_aclose_is_idempotent(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        await cli.aclose()
        await cli.aclose()

    async def test_a_finished_command_is_not_tracked(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"1.13.7\n")

        with patch("asyncio.create_subprocess_exec", return_value=process):
            await cli._execute("version")

        assert cli._running == set()

    async def test_a_timed_out_command_is_not_tracked(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"", returncode=None)
        process.communicate.side_effect = TimeoutError
        process.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLITimeoutError):
                await cli._execute("read", params={"path": "slow.md"})

        assert cli._running == set()

    @pytest.mark.real_processes
    async def test_aclose_kills_a_command_in_flight(self, tmp_path):
        # Real processes, and two of them: the guarantee under test is
        # that nothing survives the close, and a mock cannot show that.
        # The backgrounded `sleep` inherits stdout, so killing only its
        # parent would leave the pipe open and `communicate()` blocked.
        binary = tmp_path / "slow-obsidian"
        binary.write_text("#!/bin/sh\nsleep 30 &\nwait\n")
        binary.chmod(0o755)

        cli = ObsidianCLI("TestVault", binary=str(binary))
        task = asyncio.create_task(cli._execute("read", params={"path": "big.md"}))
        while not cli._running:
            await asyncio.sleep(0.01)
        process = next(iter(cli._running))

        await cli.aclose()

        async with asyncio.timeout(5):
            with pytest.raises(RuntimeError, match="closed while it ran"):
                await task
        assert process.returncode is not None
        assert cli._running == set()


class TestRun:
    async def test_passes_everything_through(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"[]")

        with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
            await cli.run(
                "tags",
                params={"path": "note.md"},
                flags=["counts"],
                output_format="json",
            )

        mock_exec.assert_awaited_once_with(
            "/usr/bin/obsidian",
            "tags",
            "vault=TestVault",
            "format=json",
            "path=note.md",
            "counts",
            **SPAWN_KWARGS,
        )

    async def test_returns_output_unparsed(self):
        # The point of the escape hatch: no stripping, no parsing, no
        # guessing at a shape.
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"words: 3\ncharacters: 24\n")

        with patch("asyncio.create_subprocess_exec", return_value=process):
            output = await cli.run("wordcount", params={"path": "note.md"})

        assert output == "words: 3\ncharacters: 24\n"

    async def test_timeout_override(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian", timeout=30.0)
        process = _mock_process(b"")
        process.communicate.side_effect = TimeoutError
        process.returncode = None
        process.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLITimeoutError) as exc_info:
                await cli.run("dev:screenshot", timeout=0.5)

        assert exc_info.value.timeout == 0.5

    async def test_a_failing_command_raises(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b'Error: Command "nope" not found\n')

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CommandError) as exc_info:
                await cli.run("nope")

        assert exc_info.value.command == "nope"

    async def test_after_aclose_raises(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        await cli.aclose()

        with pytest.raises(RuntimeError, match="has been closed"):
            await cli.run("version")


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
            "path=note.md",
            **SPAWN_KWARGS,
        )

    async def test_output_format(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"[]")

        with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
            await cli._execute("tags", output_format="json")

        mock_exec.assert_awaited_once_with(
            "/usr/bin/obsidian",
            "tags",
            "vault=TestVault",
            "format=json",
            **SPAWN_KWARGS,
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
        mock_process.returncode = None
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
                flags=["overwrite"],
            )

        mock_exec.assert_awaited_once_with(
            "/usr/bin/obsidian",
            "create",
            "vault=TestVault",
            "path=note.md",
            "overwrite",
            **SPAWN_KWARGS,
        )

    async def test_timeout_override(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian", timeout=30.0)

        mock_process = AsyncMock()
        mock_process.communicate.side_effect = TimeoutError
        mock_process.returncode = None
        mock_process.kill = MagicMock()
        mock_process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=mock_process):
            with pytest.raises(CLITimeoutError) as exc_info:
                await cli._execute("read", timeout=5.0)

        assert exc_info.value.timeout == 5.0


class TestErrorDetection:
    """The CLI exits 0 and reports failures as `Error: ...` on stdout.

    Error texts are taken verbatim from Obsidian 1.13.7.
    """

    async def test_missing_file_raises_not_found(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b'Error: File "missing.md" not found.\n')

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLINotFoundError) as exc_info:
                await cli._execute("read", params={"path": "missing.md"})

        error = exc_info.value
        assert error.command == "read"
        assert error.exit_code == 0
        assert error.stdout == 'Error: File "missing.md" not found.\n'
        assert 'File "missing.md" not found.' in str(error)
        assert isinstance(error, NotFoundError)
        assert isinstance(error, CommandError)

    async def test_missing_folder_raises_not_found(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b'Error: Folder "archive" not found.\n')

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLINotFoundError):
                await cli._execute("folder", params={"path": "archive"})

    async def test_missing_base_file_raises_not_found(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"Error: Base file not found: missing.base\n")

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLINotFoundError):
                await cli._execute("base:query", params={"path": "missing.base"})

    async def test_unknown_command_is_not_a_missing_resource(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(
            b'Error: Command "nosuch" not found. '
            b"It may require a plugin to be enabled.\n"
        )

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CommandError) as exc_info:
                await cli._execute("nosuch")

        assert not isinstance(exc_info.value, CLINotFoundError)

    async def test_missing_parameter_raises_command_error(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(
            b"Error: Missing required parameter: id=<command-id>\n"
            b"Usage: command id=<command-id>\n"
        )

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CommandError) as exc_info:
                await cli._execute("command")

        assert not isinstance(exc_info.value, CLINotFoundError)
        assert "Missing required parameter" in exc_info.value.stdout

    async def test_note_starting_with_error_prefix_raises(self):
        """Documented trade-off: such content is indistinguishable from a failure."""
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"Error: something went wrong yesterday\n")

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CommandError):
                await cli._execute("read", params={"path": "log.md"})

    async def test_error_prefix_inside_output_is_returned(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"# Log\n\nError: disk full\n")

        with patch("asyncio.create_subprocess_exec", return_value=process):
            result = await cli._execute("read", params={"path": "log.md"})

        assert result == "# Log\n\nError: disk full\n"

    async def test_non_zero_exit_with_missing_file_raises_not_found(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b'Error: File "missing.md" not found.\n', returncode=1)

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLINotFoundError) as exc_info:
                await cli._execute("read", params={"path": "missing.md"})

        assert exc_info.value.exit_code == 1


class TestProcessLifecycle:
    async def test_cancellation_kills_the_child(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")

        async def hang():
            await asyncio.Event().wait()

        process = AsyncMock()
        process.communicate = hang
        process.returncode = None
        process.kill = MagicMock()
        process.wait = AsyncMock()

        with patch("asyncio.create_subprocess_exec", return_value=process):
            task = asyncio.create_task(
                cli._execute("create", params={"path": "big.md"})
            )
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        process.kill.assert_called_once()
        process.wait.assert_awaited_once()

    async def test_finished_child_is_not_killed(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")

        process = _mock_process(b"", returncode=0)
        process.communicate.side_effect = TimeoutError
        process.kill = MagicMock()

        with patch("asyncio.create_subprocess_exec", return_value=process):
            with pytest.raises(CLITimeoutError):
                await cli._execute("read", params={"path": "slow.md"})

        process.kill.assert_not_called()

    async def test_non_utf8_output_is_not_fatal(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"caf\xe9 latte")

        with patch("asyncio.create_subprocess_exec", return_value=process):
            result = await cli._execute("read", params={"path": "note.md"})

        assert result.startswith("caf")
        assert result.endswith(" latte")

    async def test_stdin_is_closed(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        process = _mock_process(b"")

        with patch("asyncio.create_subprocess_exec", return_value=process) as mock_exec:
            await cli._execute("read")

        assert mock_exec.await_args.kwargs["stdin"] == asyncio.subprocess.DEVNULL


class TestBinaryExecution:
    async def test_missing_binary_raises_binary_not_found(self):
        cli = ObsidianCLI("TestVault", binary="/nonexistent/obsidian")

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=FileNotFoundError(2, "No such file or directory"),
        ):
            with pytest.raises(BinaryNotFoundError) as exc_info:
                await cli._execute("read", params={"path": "note.md"})

        assert "/nonexistent/obsidian" in str(exc_info.value)

    async def test_non_executable_binary_raises_binary_not_found(self):
        cli = ObsidianCLI("TestVault", binary="/etc/hosts")

        with patch(
            "asyncio.create_subprocess_exec",
            side_effect=PermissionError(13, "Permission denied"),
        ):
            with pytest.raises(BinaryNotFoundError):
                await cli._execute("read", params={"path": "note.md"})


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

    def test_plugins_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.plugins import CLIPluginsResource

        assert isinstance(cli.plugins, CLIPluginsResource)

    def test_themes_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.themes import CLIThemesResource

        assert isinstance(cli.themes, CLIThemesResource)

    def test_snippets_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.snippets import CLISnippetsResource

        assert isinstance(cli.snippets, CLISnippetsResource)

    def test_sync_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.sync import CLISyncResource

        assert isinstance(cli.sync, CLISyncResource)

    def test_publish_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.publish import CLIPublishResource

        assert isinstance(cli.publish, CLIPublishResource)

    def test_history_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.history import CLIHistoryResource

        assert isinstance(cli.history, CLIHistoryResource)

    def test_workspaces_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.workspaces import CLIWorkspacesResource

        assert isinstance(cli.workspaces, CLIWorkspacesResource)

    def test_hotkeys_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.hotkeys import CLIHotkeysResource

        assert isinstance(cli.hotkeys, CLIHotkeysResource)

    def test_outline_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.outline import CLIOutlineResource

        assert isinstance(cli.outline, CLIOutlineResource)

    def test_random_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.random_note import CLIRandomResource

        assert isinstance(cli.random, CLIRandomResource)

    def test_aliases_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.aliases import CLIAliasesResource

        assert isinstance(cli.aliases, CLIAliasesResource)

    def test_bases_property(self):
        cli = ObsidianCLI("TestVault", binary="/usr/bin/obsidian")
        from aiobsidian.cli.bases import CLIBasesResource

        assert isinstance(cli.bases, CLIBasesResource)
