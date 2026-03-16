from __future__ import annotations

import json
from typing import Any

from ._base import BaseCLIResource


class CLISnippetsResource(BaseCLIResource):
    """CLI resource for CSS snippet management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def enabled(self) -> list[dict[str, Any]]:
        """List enabled CSS snippets.

        Returns:
            List of enabled snippet objects.
        """
        output = await self._cli._execute("snippets:enabled")
        result: list[dict[str, Any]] = json.loads(output)
        return result

    async def enable(self, name: str) -> None:
        """Enable a CSS snippet.

        Args:
            name: Snippet name.
        """
        await self._cli._execute("snippet:enable", params={"name": name})

    async def disable(self, name: str) -> None:
        """Disable a CSS snippet.

        Args:
            name: Snippet name.
        """
        await self._cli._execute("snippet:disable", params={"name": name})

    async def list(self) -> list[dict[str, Any]]:
        """List all CSS snippets.

        Returns:
            List of snippet objects.
        """
        output = await self._cli._execute("snippets")
        result: list[dict[str, Any]] = json.loads(output)
        return result
