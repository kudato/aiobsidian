from __future__ import annotations

from ..models import Heading
from ._base import BaseCLIResource


class CLIOutlineResource(BaseCLIResource):
    """CLI resource for document outline operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def get(self, path: str) -> list[Heading]:
        """Get the heading outline of a file.

        Args:
            path: Path to the file relative to the vault root.

        Returns:
            Every heading in the order the note writes them, flat: the
            level says how deep a heading sits, nothing nests it.

        Raises:
            CommandError: If the file is not a markdown file.
            CLIParseError: If a heading has an unexpected shape.
        """
        output = await self._cli._execute(
            "outline", params={"path": path}, output_format="json"
        )
        return self._parse_json_rows("outline", output, Heading)
