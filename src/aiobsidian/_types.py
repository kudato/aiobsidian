from enum import StrEnum
from typing import Any

JsonValue = str | int | float | bool | None | list[Any] | dict[str, Any]
"""Any value the Obsidian REST API can carry as JSON.

Used for frontmatter values, which are not restricted to strings.
"""

PropertyValue = str | list[str] | None
"""A frontmatter value as the Obsidian CLI prints it.

The CLI renders every value as text, so the declared type is lost: a
property holding several values arrives as a list of strings, an empty
one as `None`, and everything else as a single string.
"""


class PatchOperation(StrEnum):
    """Operation type for PATCH requests.

    Determines how content is inserted relative to the target.
    """

    APPEND = "append"
    """Insert content after the target."""
    PREPEND = "prepend"
    """Insert content before the target."""
    REPLACE = "replace"
    """Replace the target content entirely."""


class TargetType(StrEnum):
    """Target type for PATCH requests.

    Specifies which part of a note the patch operation targets.
    """

    HEADING = "heading"
    """Target a heading section, by its text (e.g. `"My Heading"`)."""
    BLOCK = "block"
    """Target a block reference, by its bare id (e.g. `"block-id"`)."""
    FRONTMATTER = "frontmatter"
    """Target a frontmatter field, by its key."""


class PropertyType(StrEnum):
    """Type of a frontmatter property, as the Obsidian CLI names it.

    Passed to `property:set` to decide how the value text is turned into
    a frontmatter value.
    """

    TEXT = "text"
    """A string."""
    LIST = "list"
    """A list of strings, written as a comma-separated value."""
    NUMBER = "number"
    """A number."""
    CHECKBOX = "checkbox"
    """A boolean, written as `"true"` or `"false"`."""
    DATE = "date"
    """A date, written as `YYYY-MM-DD`."""
    DATETIME = "datetime"
    """A date and time, written as `YYYY-MM-DDTHH:mm` or with seconds."""


class ContentType(StrEnum):
    """Content types (MIME types) used by the Obsidian REST API.

    Controls the format of request and response bodies.
    """

    MARKDOWN = "text/markdown"
    """Plain Markdown text."""
    NOTE_JSON = "application/vnd.olrapi.note+json"
    """Structured JSON with content, frontmatter, tags, and stats."""
    DOCUMENT_MAP = "application/vnd.olrapi.document-map+json"
    """JSON listing headings, blocks, and frontmatter fields."""
    JSONLOGIC = "application/vnd.olrapi.jsonlogic+json"
    """JsonLogic query object."""
