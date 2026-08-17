from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator


class Plugin(BaseModel):
    """An installed plugin.

    Attributes:
        id: Plugin identifier, the name `plugins.info()`,
            `plugins.enable()` and `plugins.disable()` take.
        version: Version of a community plugin, or `None` for a core
            plugin — those ship with Obsidian and carry no version of
            their own.
    """

    id: str
    version: str | None = None

    @field_validator("version", mode="before")
    @classmethod
    def _blank_is_unversioned(cls, value: Any) -> Any:
        """Read the empty version column as no version at all.

        Args:
            value: Version column as the CLI prints it.

        Returns:
            `None` for the empty string the CLI prints for a core
            plugin, otherwise the value untouched.
        """
        return value or None
