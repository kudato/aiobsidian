from __future__ import annotations

from typing import Any

from pydantic import BaseModel, field_validator, model_validator

_CORE = "core"
_COMMUNITY = "community"
_MANIFEST_FIELDS = ("version", "author", "description")


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
    plugin's manifest. The two records do not overlap, and one that
    mixes them is refused: a core plugin has no manifest to carry a
    version, and a community plugin is read out of one that always names
    a version. A type Obsidian does not print today is taken as it comes
    rather than refused, so a third kind would arrive as data.

    Attributes:
        type: Where the plugin comes from: `"core"` or `"community"`.
        name: Display name of the plugin. A community plugin's is the
            one its manifest gives. A core plugin's is translated, so it
            reads in whatever language Obsidian runs in, and one that
            names itself nothing is named by its identifier instead.
        enabled: Whether the plugin is turned on.
        version: Version from the manifest, or `None` for a core plugin.
        author: Author from the manifest, or `None` for a core plugin
            and for a community plugin whose manifest names none.
            Obsidian blanks the field for a manifest that credits
            Obsidian itself, so those read as unauthored too.
        description: Description from the manifest, or `None` for a core
            plugin and for a community plugin that leaves it empty. It
            is printed last and untrimmed, so it keeps whatever blank
            space the manifest gave it. A newline is where the CLI
            would start another field, so a description a manifest
            writes one into is read short or refused outright, never
            whole.
    """

    type: str
    name: str
    enabled: bool
    version: str | None = None
    author: str | None = None
    description: str | None = None

    @field_validator("author", mode="before")
    @classmethod
    def _blank_is_unauthored(cls, value: Any) -> Any:
        """Read the empty author field as no author at all.

        Obsidian empties it itself when the manifest names nobody, so
        the field arrives blank rather than missing and would otherwise
        be the one absent value spelled `""`.

        Args:
            value: Author field as the CLI prints it.

        Returns:
            `None` for the empty string, otherwise the value untouched —
            including any other type, which is left for the field to
            refuse.
        """
        return (value or None) if isinstance(value, str) else value

    @model_validator(mode="after")
    def _the_manifest_fields_follow_the_type(self) -> PluginInfo:
        """Hold the manifest fields to the record the type names.

        Returns:
            The record, when its fields fit its type.

        Raises:
            ValueError: If a core plugin carries a manifest field, or a
                community plugin names no version.
        """
        if self.type == _CORE:
            named = [
                field for field in _MANIFEST_FIELDS if getattr(self, field) is not None
            ]
            if named:
                raise ValueError(
                    f"a core plugin has no manifest to name: {', '.join(named)}"
                )
        elif self.type == _COMMUNITY and self.version is None:
            raise ValueError("a community plugin names the version its manifest gives")
        return self
