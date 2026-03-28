from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLITagsResource(BaseCLIResource):
    """CLI resource for tag operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def get(self, name: str) -> list[dict[str, Any]]:
        """Get notes that contain a specific tag.

        Args:
            name: Tag name (without ``#`` prefix).

        Returns:
            List of matching note objects.
        """
        output = await self._cli._execute("tag", params={"tagname": name})
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def rename(self, old: str, new: str) -> None:
        """Rename a tag across the entire vault.

        Args:
            old: Current tag name.
            new: New tag name.
        """
        await self._cli._execute("tags:rename", params={"old": old, "new": new})

    async def list(
        self,
        *,
        sort: str | None = None,
        path: str | None = None,
        counts: bool = False,
    ) -> list[dict[str, Any]]:
        """List all tags in the vault.

        Args:
            sort: Sort order (e.g. ``"count"`` to sort by frequency).
            path: Restrict to tags found under this path.
            counts: If ``True``, include usage counts per tag.

        Returns:
            List of tag objects.
        """
        params: dict[str, str] = {}
        if sort:
            params["sort"] = sort
        if path is not None:
            params["path"] = path
        flags = ["--counts"] if counts else None
        output = await self._cli._execute("tags", params=params or None, flags=flags)
        result: list[dict[str, Any]] = json.loads(output)
        return result
