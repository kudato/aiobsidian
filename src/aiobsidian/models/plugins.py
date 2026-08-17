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
            their own. Required, so a listing printed without the
            column is refused rather than read as all-core.
    """

    id: str
    version: str | None

    @field_validator("version", mode="before")
    @classmethod
    def _blank_is_unversioned(cls, value: Any) -> Any:
        """Read the empty version column as no version at all.

        Args:
            value: Version column as the CLI prints it.

        Returns:
            `None` for the empty string the CLI prints for a core
            plugin, otherwise the value untouched — including any other
            type, which is left for the field to refuse.
        """
        return (value or None) if isinstance(value, str) else value


class PluginInfo(BaseModel):
    """Everything the CLI knows about one plugin.

    A core plugin ships with Obsidian and is described by its name and
    its state alone; the three remaining fields come from a community
    plugin's manifest.

    Attributes:
        type: Where the plugin comes from: `"core"` or `"community"`.
        name: Display name of the plugin. A core plugin's is translated,
            so it reads in whatever language Obsidian runs in.
        enabled: Whether the plugin is turned on.
        version: Version from the manifest, or `None` for a core plugin.
        author: Author from the manifest, or `None` for a core plugin.
        description: Description from the manifest, or `None` for a core
            plugin and for a community plugin that leaves it empty.
    """

    type: str
    name: str
    enabled: bool
    version: str | None = None
    author: str | None = None
    description: str | None = None
