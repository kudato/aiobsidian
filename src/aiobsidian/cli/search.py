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
