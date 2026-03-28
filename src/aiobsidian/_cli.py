from __future__ import annotations

import asyncio
import logging
import shutil
from functools import cached_property
from typing import TYPE_CHECKING

from ._constants import DEFAULT_CLI_TIMEOUT
from ._exceptions import BinaryNotFoundError, CLITimeoutError, CommandError

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


class ObsidianCLI:
    """Async wrapper for the Obsidian CLI.

    Provides access to vault operations, daily notes, search, properties,
    tags, links, tasks, commands, templates, bookmarks, plugins, themes,
    snippets, sync, publish, history, workspaces, hotkeys, outline,
    random notes, aliases, and bases through resource properties.

    Can be used as an async context manager:

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
        timeout: float | None = None,
    ) -> str:
        """Execute an Obsidian CLI command.

        Args:
            command: CLI command name (e.g. `"read"`, `"daily:path"`).
            params: Key-value parameters passed as `key=value` arguments.
            flags: Extra CLI flags (e.g. `["--overwrite"]`).
            timeout: Override the default timeout for this command.

        Returns:
            Standard output from the command as a string.

        Raises:
            CommandError: If the command exits with a non-zero status.
            CLITimeoutError: If the command exceeds the timeout.
        """
        effective_timeout = timeout if timeout is not None else self._timeout

        args: list[str] = [
            self._binary,
            command,
            f"vault={self._vault}",
            "format=json",
        ]
        if params:
            args.extend(f"{k}={v}" for k, v in params.items())
        if flags:
            args.extend(flags)

        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(), timeout=effective_timeout
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            raise CLITimeoutError(command, effective_timeout)

        stdout = stdout_bytes.decode()
        stderr = stderr_bytes.decode()

        if process.returncode != 0:
            raise CommandError(command, process.returncode or 1, stderr)

        if stderr:
            logger.warning("CLI stderr for %r: %s", command, stderr)

        return stdout

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
        pass
