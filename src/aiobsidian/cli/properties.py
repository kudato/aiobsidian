from __future__ import annotations

import json
from typing import Any

from .._types import JsonValue, PropertyType, PropertyValue
from ._base import BaseCLIResource

_EMPTY_VALUE = "(empty)"


class CLIPropertiesResource(BaseCLIResource):
    """CLI resource for note property operations.

    Attributes:
        _cli: Reference to the parent ``ObsidianCLI`` instance.
    """

    __slots__ = ()

    async def list(self, path: str) -> dict[str, Any]:
        """List all properties of a note.

        Args:
            path: Path to the note relative to the vault root.

        Returns:
            Dictionary of property names to their values, carrying the
            types the frontmatter declares: numbers as numbers, checkboxes
            as booleans, lists as lists.
        """
        output = await self._cli._execute(
            "properties", params={"path": path}, output_format="json"
        )
        return self._parse_json_object("properties", output)

    async def read(self, path: str, property_name: str) -> PropertyValue:
        """Read a single property from a note.

        The CLI renders the value as text, so the declared type is lost:
        the number `4` reads back as `"4"` and the checkbox `true` as
        `"true"`. Use `list()` when the types matter.

        Args:
            path: Path to the note relative to the vault root.
            property_name: Name of the property to read.

        Returns:
            The value as text, a list of strings when the property holds
            several values, or `None` when it is empty.

        Raises:
            CLINotFoundError: If the note has no such property.
        """
        output = await self._cli._execute(
            "property:read",
            params={"path": path, "name": property_name},
        )
        # The CLI ends the value with a newline and joins a list of values
        # with newlines, so one trailing newline is punctuation, not value.
        text = output.removesuffix("\n")
        if text == _EMPTY_VALUE:
            return None
        if "\n" in text:
            return text.split("\n")
        return text

    async def set(
        self,
        path: str,
        property_name: str,
        value: JsonValue,
        *,
        property_type: PropertyType | None = None,
    ) -> None:
        """Set a property on a note.

        The type follows the value: a `bool` becomes a checkbox, an `int`
        or a `float` a number, a `list` a list, a `str` text. Pass
        `property_type` to override that, which is the only way to write
        a date or a datetime.

        Args:
            path: Path to the note relative to the vault root.
            property_name: Name of the property to set.
            value: Value to write.
            property_type: Type to declare instead of the derived one.

        Raises:
            TypeError: If the value is `None` or a mapping, neither of
                which the CLI can write.
        """
        text, derived_type = self._encode_value(value)
        params = {"path": path, "name": property_name, "value": text}
        effective_type = property_type or derived_type
        if effective_type is not None:
            params["type"] = effective_type.value
        await self._cli._execute("property:set", params=params)

    async def remove(self, path: str, property_name: str) -> None:
        """Remove a property from a note.

        Args:
            path: Path to the note relative to the vault root.
            property_name: Name of the property to remove.
        """
        await self._cli._execute(
            "property:remove",
            params={"path": path, "name": property_name},
        )

    @staticmethod
    def _encode_value(value: JsonValue) -> tuple[str, PropertyType | None]:
        """Render a value the way the CLI reads it, and name its type.

        A list travels as JSON rather than in the comma-separated form the
        CLI also accepts, so that a value containing a comma survives.

        Args:
            value: Value as given by the caller.

        Returns:
            The value text and the property type it implies, or `None` for
            a list, whose type the CLI infers on its own.

        Raises:
            TypeError: If the value is `None` or a mapping.
        """
        if isinstance(value, bool):
            return "true" if value else "false", PropertyType.CHECKBOX
        if isinstance(value, int | float):
            return str(value), PropertyType.NUMBER
        if isinstance(value, list):
            return json.dumps(value), None
        if isinstance(value, str):
            return value, PropertyType.TEXT
        raise TypeError(
            f"a property value cannot be {type(value).__name__}; "
            f"pass a string, number, boolean or list"
        )
