from __future__ import annotations

from ..models import MatchedFile
from ._base import BaseCLIResource


class CLISearchResource(BaseCLIResource):
    """CLI resource for vault search operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def open(self, query: str) -> None:
        """Open the search panel in the Obsidian UI with a query.

        Args:
            query: Search query string.
        """
        await self._cli._execute("search:open", params={"query": query})

    async def query(
        self,
        query: str,
        *,
        path: str | None = None,
        limit: int | None = None,
        case: bool = False,
    ) -> list[str]:
        """Search the vault.

        Args:
            query: Search query string.
            path: Restrict search to files under this path.
            limit: Maximum number of results to return.
            case: If ``True``, perform case-sensitive search.

        Returns:
            Paths of the matching files. Use `context()` to see where in
            each file the query matched.
        """
        params: dict[str, str] = {"query": query}
        if path is not None:
            params["path"] = path
        if limit is not None:
            params["limit"] = str(limit)
        flags = ["case"] if case else None
        output = await self._cli._execute(
            "search", params=params, flags=flags, output_format="json"
        )
        result: list[str] = self._parse_json("search", output)
        return result

    async def context(
        self,
        query: str,
        *,
        path: str | None = None,
        limit: int | None = None,
        case: bool = False,
    ) -> list[MatchedFile]:
        """Search the vault, with the matching line of every hit.

        Args:
            query: Search query string.
            path: Restrict search to files under this path.
            limit: Maximum number of results to return.
            case: If ``True``, perform case-sensitive search.

        Returns:
            One entry per matching file, each carrying the lines it
            matched on. The CLI reports the matching line itself, never
            the lines around it, and a file can match on none of them —
            when the query matched its name or its frontmatter.

        Raises:
            CLIParseError: If a match has an unexpected shape.
        """
        params: dict[str, str] = {"query": query}
        if path is not None:
            params["path"] = path
        if limit is not None:
            params["limit"] = str(limit)
        flags = ["case"] if case else None
        output = await self._cli._execute(
            "search:context", params=params, flags=flags, output_format="json"
        )
        return self._parse_json_rows("search:context", output, MatchedFile)
