from __future__ import annotations

from ..models import SyncStatus
from ._base import BaseCLIResource


class CLISyncResource(BaseCLIResource):
    """CLI resource for Obsidian Sync operations.

    Only `is_paused`, `set_paused` and `status` work whatever Sync is
    doing. The rest want it set up for the vault and running, and answer
    `Error: Sync is not set up for this vault.` or, once it is set up, a
    sentence naming the state — paused, or in error — that stops them.
    Both surface as a `CommandError`, so pausing Sync closes its history
    to you until you resume it.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def is_paused(self) -> bool:
        """Check whether Obsidian Sync is paused.

        Returns:
            ``True`` if Sync is paused, ``False`` if it is running.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("sync")
        return self._parse_yes_or_no(
            "sync", output, yes="Sync is paused.", no="Sync is running."
        )

    async def set_paused(self, value: bool) -> bool:
        """Pause or resume Obsidian Sync.

        Args:
            value: ``True`` pauses sync, ``False`` resumes it.

        Returns:
            ``True`` if this call changed anything, ``False`` if Sync
            was already the way it was asked to be.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        # Inverted on purpose: the CLI names the flags after the state
        # it puts sync into, so `on` resumes and `off` pauses.
        output = await self._cli._execute("sync", flags=["off" if value else "on"])
        return self._parse_yes_or_no(
            "sync",
            output,
            yes="Sync paused." if value else "Sync resumed.",
            no="Sync is already paused." if value else "Sync is already running.",
        )

    async def open(self) -> None:
        """Open the Sync history UI."""
        await self._cli._execute("sync:open")

    async def status(self) -> SyncStatus:
        """Get sync status information.

        A vault without Sync is answered rather than refused: the status
        arrives on its own and every other field is `None`.

        Returns:
            What Sync is doing, and what it knows about this vault.

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        output = await self._cli._execute("sync:status")
        # A vault without Sync adds a plain sentence after the status line.
        return self._parse_fields_as(
            "sync:status", output, SyncStatus, separator=": ", strict=False
        )

    async def history(self, path: str) -> list[str]:
        """List sync version history for a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            One line per version, each starting with the version number to
            pass to `read()` and `restore()`. Version ``0`` is the current
            one. Empty if the file has no sync history.
        """
        output = await self._cli._execute("sync:history", params={"path": path})
        return self._parse_lines(output)

    async def read(self, path: str, *, version: int) -> str:
        """Read a specific sync version of a file.

        Args:
            path: Path to the file relative to the vault root.
            version: Version number as printed by `history()`, counting
                from ``0`` for the current version.

        Returns:
            File content at that version, without the header line the CLI
            prints before it.
        """
        output = await self._cli._execute(
            "sync:read", params={"path": path, "version": str(version)}
        )
        return self._strip_content_header(output)

    async def restore(self, path: str, *, version: int) -> None:
        """Restore a file to a specific sync version.

        Args:
            path: Path to the file relative to the vault root.
            version: Version number as printed by `history()`. Version
                ``0`` is the current one and cannot be restored.
        """
        await self._cli._execute(
            "sync:restore", params={"path": path, "version": str(version)}
        )

    async def deleted(self) -> list[str]:
        """List files deleted via sync.

        Returns:
            One line per deleted file, newest first, each starting with the
            timestamp of the deletion. Empty if none were deleted.
        """
        output = await self._cli._execute("sync:deleted")
        return self._parse_lines(output)
