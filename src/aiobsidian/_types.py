from enum import StrEnum


class Period(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PatchOperation(StrEnum):
    APPEND = "append"
    PREPEND = "prepend"
    REPLACE = "replace"


class TargetType(StrEnum):
    HEADING = "heading"
    BLOCK = "block"
    FRONTMATTER = "frontmatter"


class ContentType(StrEnum):
    MARKDOWN = "text/markdown"
    NOTE_JSON = "application/vnd.olrapi.note+json"
    DOCUMENT_MAP = "application/vnd.olrapi.document-map+json"
    DATAVIEW_DQL = "application/vnd.olrapi.dataview.dql+txt"
    JSONLOGIC = "application/vnd.olrapi.jsonlogic+json"
