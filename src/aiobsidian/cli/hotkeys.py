from __future__ import annotations

from ..models import Hotkey
from ._base import BaseCLIResource


class CLIHotkeysResource(BaseCLIResource):
    """CLI resource for hotkey operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def get(self, command_id: str, *, verbose: bool = False) -> str:
        """Get the hotkey binding for a command.

        Args:
            command_id: Command identifier.
            verbose: If ``True``, mark the binding as custom or default.

        Returns:
            The hotkey as displayed by Obsidian (e.g. ``"⌘ ⇧ F"``, or
            ``"⌘ ⇧ F (default)"`` with ``verbose``). ``"(none)"`` if the
            command has no hotkey assigned.
        """
        flags = ["verbose"] if verbose else None
        output = await self._cli._execute(
            "hotkey", params={"id": command_id}, flags=flags
        )
        return output.strip()

    async def list(self) -> list[Hotkey]:
        """List the hotkeys of every command.

        Returns:
            One entry per command the app knows, sorted by identifier,
            including the commands nothing is bound to.
        """
        output = await self._cli._execute(
            "hotkeys", flags=["verbose"], output_format="json"
        )
        return self._parse_json_rows("hotkeys", output, Hotkey)
