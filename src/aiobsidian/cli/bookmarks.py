from __future__ import annotations

from ..models import Bookmark
from ._base import BaseCLIResource


class CLIBookmarksResource(BaseCLIResource):
    """CLI resource for bookmark operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

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

        With none of ``file``, ``folder``, ``url`` and ``search`` given,
        the CLI bookmarks the file open in the Obsidian UI, and fails if
        there is none.

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

    async def list(self) -> list[Bookmark]:
        """List all bookmarks.

        Returns:
            Every bookmark with what it points at and how it is titled.
            The listing is flat: a group is one entry, the bookmarks
            inside it are entries of their own, and nothing says which
            group they came from.
        """
        output = await self._cli._execute(
            "bookmarks", flags=["verbose"], output_format="json"
        )
        return self._parse_json_rows("bookmarks", output, Bookmark)
