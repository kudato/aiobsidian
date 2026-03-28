from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLISearchResource(BaseCLIResource):
    """CLI resource for vault search operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def query(
        self,
        query: str,
        *,
        path: str | None = None,
        limit: int | None = None,
        case: bool = False,
        matches: bool = False,
    ) -> list[dict[str, Any]]:
        """Search the vault.

        Args:
            query: Search query string.
            path: Restrict search to files under this path.
            limit: Maximum number of results to return.
            case: If ``True``, perform case-sensitive search.
            matches: If ``True``, include match details in results.

        Returns:
            List of search result dictionaries.
        """
        params: dict[str, str] = {"query": query}
        if path is not None:
            params["path"] = path
        if limit is not None:
            params["limit"] = str(limit)
        flags: list[str] = []
        if case:
            flags.append("--case")
        if matches:
            flags.append("--matches")
        output = await self._cli._execute("search", params=params, flags=flags or None)
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def context(
        self,
        query: str,
        *,
        lines: int | None = None,
        path: str | None = None,
        limit: int | None = None,
        case: bool = False,
    ) -> list[dict[str, Any]]:
        """Search the vault with surrounding context lines.

        Args:
            query: Search query string.
            lines: Number of context lines to include around matches.
            path: Restrict search to files under this path.
            limit: Maximum number of results to return.
            case: If ``True``, perform case-sensitive search.

        Returns:
            List of search result dictionaries with context.
        """
        params: dict[str, str] = {"query": query}
        if lines is not None:
            params["lines"] = str(lines)
        if path is not None:
            params["path"] = path
        if limit is not None:
            params["limit"] = str(limit)
        flags = ["--case"] if case else None
        output = await self._cli._execute("search:context", params=params, flags=flags)
        result: list[dict[str, Any]] = json.loads(output)
        return result
