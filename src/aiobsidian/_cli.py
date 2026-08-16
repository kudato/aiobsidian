from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import re
import shutil
import signal
from functools import cached_property
from typing import TYPE_CHECKING

from ._constants import DEFAULT_CLI_TIMEOUT
from ._exceptions import (
    BinaryNotFoundError,
    CLINotFoundError,
    CLITimeoutError,
    CommandError,
)

if TYPE_CHECKING:
    from .cli.aliases import CLIAliasesResource
    from .cli.bases import CLIBasesResource
    from .cli.bookmarks import CLIBookmarksResource
    from .cli.commands import CLICommandsResource
    from .cli.daily import CLIDailyResource
    from .cli.dev import CLIDevResource
    from .cli.history import CLIHistoryResource
    from .cli.hotkeys import CLIHotkeysResource
    from .cli.links import CLILinksResource
    from .cli.outline import CLIOutlineResource
    from .cli.plugins import CLIPluginsResource
    from .cli.properties import CLIPropertiesResource
    from .cli.publish import CLIPublishResource
    from .cli.random_note import CLIRandomResource
    from .cli.search import CLISearchResource
    from .cli.snippets import CLISnippetsResource
    from .cli.sync import CLISyncResource
    from .cli.system import CLISystemResource
    from .cli.tabs import CLITabsResource
    from .cli.tags import CLITagsResource
    from .cli.tasks import CLITasksResource
    from .cli.templates import CLITemplatesResource
    from .cli.themes import CLIThemesResource
    from .cli.vault import CLIVaultResource
    from .cli.web import CLIWebResource
    from .cli.workspaces import CLIWorkspacesResource

logger = logging.getLogger(__name__)

_ERROR_PREFIX = "Error: "
_NOT_FOUND_PATTERN = re.compile(r"\bnot found\b", re.IGNORECASE)
_UNKNOWN_COMMAND_PATTERN = re.compile(r'^Error: Command "[^"]*" not found')


class ObsidianCLI:
    """Async wrapper for the Obsidian CLI.

    Provides access to vault operations, daily notes, search, properties,
    tags, links, tasks, commands, templates, bookmarks, plugins, themes,
    snippets, sync, publish, history, workspaces, hotkeys, outline,
    random notes, aliases, bases, system, tabs, web, and dev
    through resource properties.

    Can be used as an async context manager, which closes the client on
    the way out:

    ```python
    async with ObsidianCLI("MyVault") as cli:
        content = await cli.vault.read("note.md")
    ```

    Args:
        vault: Name of the Obsidian vault to operate on.
        binary: Path to the Obsidian CLI binary. Use `"auto"` to
            find it automatically via `shutil.which`.
        timeout: Default command timeout in seconds.
    """

    def __init__(
        self,
        vault: str,
        *,
        binary: str = "auto",
        timeout: float = DEFAULT_CLI_TIMEOUT,
    ) -> None:
        self._vault = vault
        self._timeout = timeout
        self._binary = self._resolve_binary(binary)
        self._running: set[asyncio.subprocess.Process] = set()
        self._closed = False

    def __repr__(self) -> str:
        return f"ObsidianCLI(vault={self._vault!r}, binary={self._binary!r})"

    @staticmethod
    def _resolve_binary(binary: str) -> str:
        """Resolve the CLI binary path.

        Args:
            binary: Explicit path or `"auto"` for automatic lookup.

        Returns:
            Resolved absolute path to the binary.

        Raises:
            BinaryNotFoundError: If `"auto"` is used and the binary
                cannot be found on ``PATH``.
        """
        if binary != "auto":
            return binary
        resolved = shutil.which("obsidian")
        if resolved is None:
            raise BinaryNotFoundError(
                "Obsidian CLI binary not found on PATH. "
                "Install Obsidian or pass binary= explicitly."
            )
        return resolved

    async def _execute(
        self,
        command: str,
        *,
        params: dict[str, str] | None = None,
        flags: list[str] | None = None,
        output_format: str | None = None,
        timeout: float | None = None,
    ) -> str:
        """Execute an Obsidian CLI command.

        The Obsidian CLI exits with status `0` even when a command fails and
        prints the failure as `Error: ...` on standard output. Output starting
        with that prefix is therefore treated as a failure and raised. As a
        consequence, reading a note whose first line starts with `Error: ` also
        raises instead of returning the text.

        Cancelling the call kills the child process before the cancellation
        propagates, so no orphan keeps writing to the vault. The command gets
        no stdin, so one waiting for input fails instead of hanging.

        Args:
            command: CLI command name (e.g. `"read"`, `"daily:path"`).
            params: Key-value parameters passed as `key=value` arguments.
            flags: Extra CLI flags (e.g. `["overwrite"]`).
            output_format: Value for the `format=` parameter. Only commands
                that document it accept one; the rest ignore it and print
                plain text.
            timeout: Override the default timeout for this command.

        Returns:
            Standard output from the command as a string.

        Raises:
            RuntimeError: If the client has been closed.
            BinaryNotFoundError: If the binary cannot be executed.
            CLINotFoundError: If the CLI reports a missing resource.
            CommandError: If the command fails for any other reason.
            CLITimeoutError: If the command exceeds the timeout.
        """
        if self._closed:
            raise RuntimeError(
                f"Cannot run {command!r}: this ObsidianCLI has been closed."
            )

        effective_timeout = timeout if timeout is not None else self._timeout

        args: list[str] = [self._binary, command, f"vault={self._vault}"]
        if output_format is not None:
            args.append(f"format={output_format}")
        if params:
            args.extend(f"{k}={v}" for k, v in params.items())
        if flags:
            args.extend(flags)

        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdin=asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Its own process group, so that stopping the command
                # stops whatever it started. See _kill.
                start_new_session=True,
            )
        except OSError as exc:
            raise BinaryNotFoundError(
                f"Obsidian CLI binary {self._binary!r} could not be executed: "
                f"{exc}. Install Obsidian v1.12+ or pass binary= explicitly."
            ) from exc

        self._running.add(process)
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=effective_timeout
            )
        except TimeoutError:
            await self._kill(process)
            raise CLITimeoutError(command, effective_timeout) from None
        except asyncio.CancelledError:
            await self._kill(process)
            raise
        finally:
            self._running.discard(process)

        # A signal we did not send is somebody else's business, but a
        # signal plus a closed client is aclose() killing this command,
        # and "exit_code=-9, no output" would not say so.
        if self._closed and (process.returncode or 0) < 0:
            raise RuntimeError(
                f"Command {command!r} was killed: this ObsidianCLI was closed "
                f"while it ran."
            )

        stdout = stdout_bytes.decode(errors="replace")
        stderr = stderr_bytes.decode(errors="replace")

        if process.returncode != 0:
            raise self._build_error(command, process.returncode or 1, stdout, stderr)

        if stderr:
            logger.warning("CLI stderr for %r: %s", command, stderr)

        if stdout.startswith(_ERROR_PREFIX):
            raise self._build_error(command, 0, stdout, stderr)

        return stdout

    @staticmethod
    async def _kill(process: asyncio.subprocess.Process) -> None:
        """Kill a running command, its own children included, and reap it.

        The whole process group goes, not just the command: a grandchild
        that outlived its parent would keep the vault open and keep the
        pipe open with it, leaving whoever awaits the output stuck in
        `communicate()` for as long as the grandchild runs.

        Args:
            process: The child process to stop.
        """
        if process.returncode is not None:
            return
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
        with contextlib.suppress(ProcessLookupError):
            process.kill()
        with contextlib.suppress(ProcessLookupError, asyncio.CancelledError):
            await asyncio.shield(process.wait())

    @staticmethod
    def _build_error(
        command: str,
        exit_code: int,
        stdout: str,
        stderr: str,
    ) -> CommandError:
        """Build the exception describing a failed command.

        Args:
            command: CLI command name.
            exit_code: Process exit code.
            stdout: Standard output of the command.
            stderr: Standard error output of the command.

        Returns:
            `CLINotFoundError` if the CLI reported a missing resource,
            `CommandError` otherwise. A command unknown to the CLI is a
            plain `CommandError`, not a missing resource.
        """
        lines = stdout.strip().splitlines()
        first_line = lines[0] if lines else ""
        if (
            first_line.startswith(_ERROR_PREFIX)
            and _NOT_FOUND_PATTERN.search(first_line)
            and not _UNKNOWN_COMMAND_PATTERN.match(first_line)
        ):
            return CLINotFoundError(command, exit_code, stderr, stdout)
        return CommandError(command, exit_code, stderr, stdout)

    # -- resources ---------------------------------------------------------

    @cached_property
    def vault(self) -> CLIVaultResource:
        """Access vault file operations (read, create, append, move, delete, list)."""
        from .cli.vault import CLIVaultResource

        return CLIVaultResource(self)

    @cached_property
    def daily(self) -> CLIDailyResource:
        """Access daily note operations (read, path, create, append, prepend)."""
        from .cli.daily import CLIDailyResource

        return CLIDailyResource(self)

    @cached_property
    def search(self) -> CLISearchResource:
        """Search vault content."""
        from .cli.search import CLISearchResource

        return CLISearchResource(self)

    @cached_property
    def properties(self) -> CLIPropertiesResource:
        """Access note properties (list, read, set, remove)."""
        from .cli.properties import CLIPropertiesResource

        return CLIPropertiesResource(self)

    @cached_property
    def tags(self) -> CLITagsResource:
        """Access tag operations (list, get, rename)."""
        from .cli.tags import CLITagsResource

        return CLITagsResource(self)

    @cached_property
    def links(self) -> CLILinksResource:
        """Access link operations (outgoing, incoming, unresolved, orphans)."""
        from .cli.links import CLILinksResource

        return CLILinksResource(self)

    @cached_property
    def tasks(self) -> CLITasksResource:
        """Access task operations (list, create, complete)."""
        from .cli.tasks import CLITasksResource

        return CLITasksResource(self)

    @cached_property
    def commands(self) -> CLICommandsResource:
        """Access Obsidian command operations (list, execute)."""
        from .cli.commands import CLICommandsResource

        return CLICommandsResource(self)

    @cached_property
    def templates(self) -> CLITemplatesResource:
        """Access template operations (list, read)."""
        from .cli.templates import CLITemplatesResource

        return CLITemplatesResource(self)

    @cached_property
    def bookmarks(self) -> CLIBookmarksResource:
        """Access bookmark operations (list, add)."""
        from .cli.bookmarks import CLIBookmarksResource

        return CLIBookmarksResource(self)

    @cached_property
    def plugins(self) -> CLIPluginsResource:
        """Access plugin management."""
        from .cli.plugins import CLIPluginsResource

        return CLIPluginsResource(self)

    @cached_property
    def themes(self) -> CLIThemesResource:
        """Access theme management (list, current, set, install, uninstall)."""
        from .cli.themes import CLIThemesResource

        return CLIThemesResource(self)

    @cached_property
    def snippets(self) -> CLISnippetsResource:
        """Access CSS snippet management (list, enabled, enable, disable)."""
        from .cli.snippets import CLISnippetsResource

        return CLISnippetsResource(self)

    @cached_property
    def sync(self) -> CLISyncResource:
        """Access Obsidian Sync operations (status, history, read, restore, deleted)."""
        from .cli.sync import CLISyncResource

        return CLISyncResource(self)

    @cached_property
    def publish(self) -> CLIPublishResource:
        """Access Obsidian Publish operations (site, list, status, add, remove)."""
        from .cli.publish import CLIPublishResource

        return CLIPublishResource(self)

    @cached_property
    def history(self) -> CLIHistoryResource:
        """Access local file history (list, read, restore)."""
        from .cli.history import CLIHistoryResource

        return CLIHistoryResource(self)

    @cached_property
    def workspaces(self) -> CLIWorkspacesResource:
        """Access workspace management (list, current, save, load, delete)."""
        from .cli.workspaces import CLIWorkspacesResource

        return CLIWorkspacesResource(self)

    @cached_property
    def hotkeys(self) -> CLIHotkeysResource:
        """Access hotkey operations (list, get)."""
        from .cli.hotkeys import CLIHotkeysResource

        return CLIHotkeysResource(self)

    @cached_property
    def outline(self) -> CLIOutlineResource:
        """Access document outline (headings)."""
        from .cli.outline import CLIOutlineResource

        return CLIOutlineResource(self)

    @cached_property
    def random(self) -> CLIRandomResource:
        """Access random note operations (read)."""
        from .cli.random_note import CLIRandomResource

        return CLIRandomResource(self)

    @cached_property
    def aliases(self) -> CLIAliasesResource:
        """Access note alias operations (get)."""
        from .cli.aliases import CLIAliasesResource

        return CLIAliasesResource(self)

    @cached_property
    def tabs(self) -> CLITabsResource:
        """Access workspace tabs management (list, open, recents)."""
        from .cli.tabs import CLITabsResource

        return CLITabsResource(self)

    @cached_property
    def system(self) -> CLISystemResource:
        """Access system commands (version, help, reload, restart, vaults)."""
        from .cli.system import CLISystemResource

        return CLISystemResource(self)

    @cached_property
    def bases(self) -> CLIBasesResource:
        """Access Obsidian Bases / database operations (list, views, create, query)."""
        from .cli.bases import CLIBasesResource

        return CLIBasesResource(self)

    @cached_property
    def web(self) -> CLIWebResource:
        """Access web viewer operations (open)."""
        from .cli.web import CLIWebResource

        return CLIWebResource(self)

    @cached_property
    def dev(self) -> CLIDevResource:
        """Access developer/debugging tools."""
        from .cli.dev import CLIDevResource

        return CLIDevResource(self)

    # -- lifecycle ---------------------------------------------------------

    async def __aenter__(self) -> ObsidianCLI:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the client and kill every command still running.

        A command started from another task is killed rather than waited
        for, so leaving an `async with` block guarantees that no
        `obsidian` process is still writing to the vault. That task gets
        a `RuntimeError` naming the close as the cause.

        Closed is final: any further command raises `RuntimeError`.
        Calling this more than once is harmless.
        """
        self._closed = True
        for process in list(self._running):
            await self._kill(process)
        self._running.clear()
