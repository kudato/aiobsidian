from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_KEYS_SEPARATOR = ", "


class Hotkey(BaseModel):
    """The keys bound to one command.

    Attributes:
        command_id: Command identifier, the name `hotkeys.get()` takes.
        keys: Every binding, spelled the way Obsidian displays it, as in
            `"⌘ ⇧ F"`. A command can carry more than one, and carries
            none when nothing is bound to it.
        custom: Whether the binding was set by the user rather than
            shipped with Obsidian. Custom with no keys is a default
            binding the user cleared.
    """

    model_config = ConfigDict(populate_by_name=True)

    command_id: str = Field(alias="id")
    keys: list[str] = Field(alias="hotkey")
    custom: bool

    @field_validator("keys", mode="before")
    @classmethod
    def _split_keys(cls, value: Any) -> Any:
        """Take apart the bindings the CLI joined into one column.

        Args:
            value: Hotkey column as the CLI prints it.

        Returns:
            One entry per binding, and none at all for the empty string
            the CLI prints for an unbound command. Any other type is
            left alone for the field to refuse.
        """
        if not isinstance(value, str):
            return value
        return value.split(_KEYS_SEPARATOR) if value else []

    @field_validator("custom", mode="before")
    @classmethod
    def _custom_or_default(cls, value: Any) -> Any:
        """Read the column that spells a boolean as a word.

        Args:
            value: Custom column as the CLI prints it, `"custom"` or
                `"default"`.

        Returns:
            The word as a boolean, or the value untouched if it is
            neither, leaving the type error to the field.
        """
        if value in ("custom", "default"):
            return value == "custom"
        return value
