from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLISearchResource(BaseCLIResource):
    """CLI resource for vault search operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def query(self, query: str) -> list[dict[str, Any]]:
        """Search the vault.

        Args:
            query: Search query string.

        Returns:
            List of search result dictionaries.
        """
        output = await self._cli._execute("search", params={"query": query})
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def context(
        self, query: str, *, lines: int | None = None
    ) -> list[dict[str, Any]]:
        """Search the vault with surrounding context lines.

        Args:
            query: Search query string.
            lines: Number of context lines to include around matches.

        Returns:
            List of search result dictionaries with context.
        """
        params: dict[str, str] = {"query": query}
        if lines is not None:
            params["lines"] = str(lines)
        output = await self._cli._execute("search:context", params=params)
        result: list[dict[str, Any]] = json.loads(output)
        return result
