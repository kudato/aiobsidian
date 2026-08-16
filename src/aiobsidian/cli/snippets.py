from __future__ import annotations

from ._base import BaseCLIResource


class CLISnippetsResource(BaseCLIResource):
    """CLI resource for CSS snippet management.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def enabled(self) -> list[str]:
        """List enabled CSS snippets.

        Returns:
            List of enabled snippet names.
        """
        output = await self._cli._execute("snippets:enabled")
        return self._parse_lines(output)

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

    async def list(self) -> list[str]:
        """List all CSS snippets.

        Returns:
            List of snippet names.
        """
        output = await self._cli._execute("snippets")
        return self._parse_lines(output)
