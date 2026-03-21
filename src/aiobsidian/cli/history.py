from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIHistoryResource(BaseCLIResource):
    """CLI resource for local file history operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def read(self, path: str, *, version: str) -> str:
        """Read a specific version from local history.

        Args:
            path: Path to the file relative to the vault root.
            version: Version identifier.

        Returns:
            File content at the specified version.
        """
        return await self._cli._execute(
            "history:read", params={"path": path, "version": version}
        )

    async def restore(self, path: str, *, version: str) -> None:
        """Restore a file from local history.

        Args:
            path: Path to the file relative to the vault root.
            version: Version identifier to restore.
        """
        await self._cli._execute(
            "history:restore", params={"path": path, "version": version}
        )

    async def list(self) -> list[dict[str, Any]]:
        """List files that have local history.

        Returns:
            List of file objects with local history.
        """
        output = await self._cli._execute("history:list")
        result: list[dict[str, Any]] = json.loads(output)
        return result
