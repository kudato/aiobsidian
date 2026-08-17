from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLILinksResource(BaseCLIResource):
    """CLI resource for link and backlink operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def outgoing(self, path: str) -> list[str]:
        """Get outgoing links from a note.

        Args:
            path: Path to the note relative to the vault root.

        Returns:
            List of paths the note links to.
        """
        output = await self._cli._execute("links", params={"path": path})
        return self._parse_lines(output)

    async def incoming(
        self, path: str, *, counts: bool = False
    ) -> list[dict[str, Any]]:
        """Get backlinks (incoming links) to a note.

        Args:
            path: Path to the note relative to the vault root.
            counts: If ``True``, include reference counts.

        Returns:
            List of backlink objects.
        """
        flags = ["counts"] if counts else None
        output = await self._cli._execute(
            "backlinks", params={"path": path}, flags=flags, output_format="json"
        )
        result: list[dict[str, Any]] = self._parse_json("backlinks", output)
        return result

    async def unresolved(self) -> list[str]:
        """Get all unresolved (broken) links in the vault.

        Returns:
            The link targets that no note in the vault answers to, spelled
            as the notes write them.
        """
        output = await self._cli._execute("unresolved", output_format="json")
        return self._parse_json_column("unresolved", output, key="link")

    async def orphans(self) -> list[str]:
        """Get orphan notes (notes with no incoming links).

        Returns:
            List of note paths with no incoming links.
        """
        output = await self._cli._execute("orphans")
        return self._parse_lines(output)

    async def deadends(self) -> list[str]:
        """Get notes with no outgoing links (dead ends).

        Returns:
            List of note paths with no outgoing links.
        """
        output = await self._cli._execute("deadends")
        return self._parse_lines(output)
