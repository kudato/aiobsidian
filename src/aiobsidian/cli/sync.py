from __future__ import annotations

from ._base import BaseCLIResource


class CLISyncResource(BaseCLIResource):
    """CLI resource for Obsidian Sync operations.

    Every command except `toggle` needs Sync to be set up for the vault
    and answers `Error: Sync is not set up for this vault.` otherwise,
    which surfaces as a `CommandError`.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def toggle(self, *, on: bool) -> None:
        """Pause or resume Obsidian Sync.

        Args:
            on: If ``True``, resume sync; if ``False``, pause sync.
        """
        await self._cli._execute("sync", flags=["on" if on else "off"])

    async def open(self) -> None:
        """Open the Sync history UI."""
        await self._cli._execute("sync:open")

    async def status(self) -> dict[str, str]:
        """Get sync status information.

        Returns:
            Status keyed by field name: ``status``, and, once the vault is
            set up, ``vault``, ``device``, ``vault size`` and
            ``account usage``. A vault without Sync answers with the
            ``status`` field alone.
        """
        output = await self._cli._execute("sync:status")
        # A vault without Sync adds a plain sentence after the status line.
        return self._parse_fields("sync:status", output, separator=":", strict=False)

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
