from __future__ import annotations

from typing import Literal

from ..models import Tag
from ._base import BaseCLIResource


class CLITagsResource(BaseCLIResource):
    """CLI resource for tag operations.

    The CLI can read tags but not rewrite them: renaming a tag across the
    vault is a UI-only operation.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def get(self, name: str) -> list[str]:
        """Get notes that contain a specific tag.

        Args:
            name: Tag name (without ``#`` prefix).

        Returns:
            List of paths of notes carrying the tag.
        """
        output = await self._cli._execute("tag", params={"name": name})
        return self._parse_lines(output)

    async def list(
        self,
        *,
        sort: Literal["count"] | None = None,
        path: str | None = None,
    ) -> list[Tag]:
        """List all tags in the vault.

        Args:
            sort: ``"count"`` to sort by frequency. The CLI reads that
                one word and sorts by name for anything else, so there is
                nothing else to pass.
            path: Restrict to the tags of this one file. The CLI refuses
                a folder: there is no way to scope the listing to one.

        Returns:
            Every tag with its usage count, in the order the CLI sorted
            them.
        """
        params: dict[str, str] = {}
        if sort is not None:
            params["sort"] = sort
        if path is not None:
            params["path"] = path
        output = await self._cli._execute(
            "tags", params=params or None, flags=["counts"], output_format="json"
        )
        return self._parse_json_rows("tags", output, Tag)
