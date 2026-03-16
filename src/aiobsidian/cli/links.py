from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLILinksResource(BaseCLIResource):
    """CLI resource for link and backlink operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def outgoing(self, path: str) -> list[dict[str, Any]]:
        """Get outgoing links from a note.

        Args:
            path: Path or name of the note.

        Returns:
            List of outgoing link objects.
        """
        output = await self._cli._execute("links", params={"file": path})
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def incoming(self, path: str) -> list[dict[str, Any]]:
        """Get backlinks (incoming links) to a note.

        Args:
            path: Path or name of the note.

        Returns:
            List of backlink objects.
        """
        output = await self._cli._execute("backlinks", params={"file": path})
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def unresolved(self) -> list[dict[str, Any]]:
        """Get all unresolved (broken) links in the vault.

        Returns:
            List of unresolved link objects.
        """
        output = await self._cli._execute("unresolved")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def orphans(self) -> list[dict[str, Any]]:
        """Get orphan notes (notes with no incoming or outgoing links).

        Returns:
            List of orphan note objects.
        """
        output = await self._cli._execute("orphans")
        result: list[dict[str, Any]] = json.loads(output)
        return result
