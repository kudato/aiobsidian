from enum import StrEnum


class Period(StrEnum):
    """Time period for periodic notes.

    Used with `client.periodic` to access daily, weekly, monthly,
    quarterly, or yearly notes.
    """

    DAILY = "daily"
    """Daily note."""
    WEEKLY = "weekly"
    """Weekly note."""
    MONTHLY = "monthly"
    """Monthly note."""
    QUARTERLY = "quarterly"
    """Quarterly note."""
    YEARLY = "yearly"
    """Yearly note."""


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
    """Target a heading section (e.g. `## My Heading`)."""
    BLOCK = "block"
    """Target a block reference (e.g. `^block-id`)."""
    FRONTMATTER = "frontmatter"
    """Target a frontmatter field."""


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
    DATAVIEW_DQL = "application/vnd.olrapi.dataview.dql+txt"
    """Dataview Query Language query string."""
    JSONLOGIC = "application/vnd.olrapi.jsonlogic+json"
    """JsonLogic query object."""
