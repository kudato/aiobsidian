from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLISyncResource(BaseCLIResource):
    """CLI resource for Obsidian Sync operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def status(self) -> dict[str, Any]:
        """Get sync status information.

        Returns:
            Sync status details.
        """
        output = await self._cli._execute("sync:status")
        result: dict[str, Any] = json.loads(output)
        return result

    async def history(self, path: str) -> list[dict[str, Any]]:
        """List sync version history for a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            List of version objects.
        """
        output = await self._cli._execute("sync:history", params={"path": path})
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def read(self, path: str, *, version: str) -> str:
        """Read a specific sync version of a file.

        Args:
            path: Path to the file relative to the vault root.
            version: Version identifier.

        Returns:
            File content at the specified version.
        """
        return await self._cli._execute(
            "sync:read", params={"path": path, "version": version}
        )

    async def restore(self, path: str, *, version: str) -> None:
        """Restore a file to a specific sync version.

        Args:
            path: Path to the file relative to the vault root.
            version: Version identifier to restore.
        """
        await self._cli._execute(
            "sync:restore", params={"path": path, "version": version}
        )

    async def deleted(self) -> list[dict[str, Any]]:
        """List files deleted via sync.

        Returns:
            List of deleted file objects.
        """
        output = await self._cli._execute("sync:deleted")
        result: list[dict[str, Any]] = json.loads(output)
        return result
