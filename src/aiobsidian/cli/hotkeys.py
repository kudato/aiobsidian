from __future__ import annotations

from typing import Any

from ._base import BaseCLIResource


class CLIHotkeysResource(BaseCLIResource):
    """CLI resource for hotkey operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

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

    async def list(self) -> list[dict[str, Any]]:
        """List all hotkey bindings.

        Returns:
            List of hotkey binding objects.
        """
        output = await self._cli._execute("hotkeys", output_format="json")
        result: list[dict[str, Any]] = self._parse_json("hotkeys", output)
        return result
