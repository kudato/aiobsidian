from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLIPublishResource(BaseCLIResource):
    """CLI resource for Obsidian Publish operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def site(self) -> dict[str, Any]:
        """Get Publish site information.

        Returns:
            Site configuration details.
        """
        output = await self._cli._execute("publish:site")
        result: dict[str, Any] = json.loads(output)
        return result

    async def status(self, path: str | None = None) -> dict[str, Any]:
        """Get publication status.

        Args:
            path: Optional file path to check status for.

        Returns:
            Publication status details.
        """
        params = {"path": path} if path else None
        output = await self._cli._execute("publish:status", params=params)
        result: dict[str, Any] = json.loads(output)
        return result

    async def add(self, path: str) -> None:
        """Publish a file.

        Args:
            path: Path to the file to publish.
        """
        await self._cli._execute("publish:add", params={"path": path})

    async def remove(self, path: str) -> None:
        """Unpublish a file.

        Args:
            path: Path to the file to unpublish.
        """
        await self._cli._execute("publish:remove", params={"path": path})

    async def list(self) -> list[dict[str, Any]]:
        """List published files.

        Returns:
            List of published file objects.
        """
        output = await self._cli._execute("publish:list")
        result: list[dict[str, Any]] = json.loads(output)
        return result
