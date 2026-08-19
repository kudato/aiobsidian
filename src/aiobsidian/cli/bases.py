from __future__ import annotations

from typing import Any

from ..models import BaseView
from ._base import BaseCLIResource


class CLIBasesResource(BaseCLIResource):
    """CLI resource for Obsidian Bases (database) operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def views(self) -> list[BaseView]:
        """List the views of the base file open in the Obsidian UI.

        The CLI has no way to address a base file here: `base:views`
        takes no parameters and reads whichever file is active. Open the
        base with `vault.open()` first, or read the file yourself.

        Returns:
            One entry per view, in the order the base file defines them.

        Raises:
            CommandError: If no file is active, or the active file is not
                a base file.
            CLIParseError: If a view row has an unexpected shape.
        """
        output = await self._cli._execute("base:views")
        return self._parse_rows_as(
            "base:views", output, BaseView, columns=("name", "type")
        )

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

        Raises:
            CLIParseError: If the output has an unexpected shape.
        """
        params: dict[str, str] = {"path": path}
        if view is not None:
            params["view"] = view
        output = await self._cli._execute(
            "base:query", params=params, output_format="json"
        )
        return self._parse_json_objects("base:query", output)

    async def list(self) -> list[str]:
        """List all base files in the vault.

        Returns:
            List of paths to `.base` files.
        """
        output = await self._cli._execute("bases")
        return self._parse_lines(output)
