from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLIBookmarksResource(BaseCLIResource):
    """CLI resource for bookmark operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def add(
        self,
        *,
        file: str | None = None,
        folder: str | None = None,
        url: str | None = None,
        title: str | None = None,
        search: str | None = None,
        subpath: str | None = None,
    ) -> None:
        """Add a bookmark.

        At least one of ``file``, ``folder``, ``url``, or ``search``
        must be provided.

        Args:
            file: Path to a file to bookmark.
            folder: Path to a folder to bookmark.
            url: URL to bookmark.
            title: Display title for the bookmark.
            search: Search query to bookmark.
            subpath: Subpath within the file (e.g. heading or block).
        """
        params: dict[str, str] = {}
        if file is not None:
            params["file"] = file
        if folder is not None:
            params["folder"] = folder
        if url is not None:
            params["url"] = url
        if title is not None:
            params["title"] = title
        if search is not None:
            params["search"] = search
        if subpath is not None:
            params["subpath"] = subpath
        await self._cli._execute("bookmark", params=params or None)

    async def list(self) -> list[dict[str, Any]]:
        """List all bookmarks.

        Returns:
            List of bookmark objects.
        """
        output = await self._cli._execute("bookmarks", output_format="json")
        result: list[dict[str, Any]] = self._parse_json("bookmarks", output)
        return result
