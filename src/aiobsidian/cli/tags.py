from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLITagsResource(BaseCLIResource):
    """CLI resource for tag operations.

    The CLI can read tags but not rewrite them: renaming a tag across the
    vault is a UI-only operation.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def get(self, name: str) -> list[str]:
        """Get notes that contain a specific tag.

        Args:
            name: Tag name (without ``#`` prefix).

        Returns:
            List of paths of notes carrying the tag.
        """
        output = await self._cli._execute("tag", params={"name": name})
        return self._parse_lines(output)

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
        if sort is not None:
            params["sort"] = sort
        if path is not None:
            params["path"] = path
        flags = ["counts"] if counts else None
        output = await self._cli._execute(
            "tags", params=params or None, flags=flags, output_format="json"
        )
        result: list[dict[str, Any]] = self._parse_json("tags", output)
        return result
