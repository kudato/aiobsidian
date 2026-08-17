from __future__ import annotations

from ..models import Hotkey
from ..models.hotkeys import _split_keys
from ._base import BaseCLIResource

_NO_HOTKEY = "(none)"


class CLIHotkeysResource(BaseCLIResource):
    """CLI resource for hotkey operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def get(self, command_id: str) -> list[str]:
        """Get the keys bound to one command.

        The CLI can also mark the binding as the user's or Obsidian's,
        but not for a command that has none, so `list()` is the only
        place that answers it for every command.

        Args:
            command_id: Command identifier.

        Returns:
            Every binding, spelled the way Obsidian displays it, as in
            `"⌘ ⇧ F"`. Empty when nothing is bound to the command.
        """
        output = await self._cli._execute("hotkey", params={"id": command_id})
        printed = output.strip()
        return [] if printed == _NO_HOTKEY else _split_keys(printed)

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
