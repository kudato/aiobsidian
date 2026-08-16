from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLIBasesResource(BaseCLIResource):
    """CLI resource for Obsidian Bases (database) operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    async def views(self) -> list[dict[str, str]]:
        """List the views of the base file open in the Obsidian UI.

        The CLI has no way to address a base file here: `base:views`
        takes no parameters and reads whichever file is active. Open the
        base with `vault.open()` first, or read the file yourself.

        Returns:
            One entry per view, with its ``name`` and its ``type``.

        Raises:
            CommandError: If no file is active, or the active file is not
                a base file.
        """
        output = await self._cli._execute("base:views")
        return [
            {"name": row[0], "type": row[1]}
            for row in self._parse_rows(output)
            if len(row) == 2
        ]

    async def create(
        self,
        path: str,
        *,
        view: str | None = None,
        name: str | None = None,
        content: str | None = None,
    ) -> None:
        """Create a note as a new item in a base.

        A base collects notes; an item is a note, and its fields come from
        that note's frontmatter. The CLI cannot set them at creation time,
        so write the note here and set its fields with `properties.set()`.

        Args:
            path: Path to the base file relative to the vault root.
            view: View to create the item in. Defaults to the first one.
            name: File name for the new note.
            content: Initial content of the new note.
        """
        params: dict[str, str] = {"path": path}
        if view is not None:
            params["view"] = view
        if name is not None:
            params["name"] = name
        if content is not None:
            params["content"] = content
        await self._cli._execute("base:create", params=params)

    async def query(
        self, path: str, *, view: str | None = None
    ) -> list[dict[str, Any]]:
        """Query records from a base.

        Args:
            path: Path to the base file relative to the vault root.
            view: Optional view name to filter by.

        Returns:
            List of record objects.
        """
        params: dict[str, str] = {"path": path}
        if view is not None:
            params["view"] = view
        output = await self._cli._execute(
            "base:query", params=params, output_format="json"
        )
        result: list[dict[str, Any]] = self._parse_json("base:query", output)
        return result

    async def list(self) -> list[str]:
        """List all base files in the vault.

        Returns:
            List of paths to `.base` files.
        """
        output = await self._cli._execute("bases")
        return self._parse_lines(output)
