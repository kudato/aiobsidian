from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_MILLISECONDS = 1000


class FileStat(BaseModel):
    """File system metadata for a vault file.

    Attributes:
        ctime: Creation time as a Unix timestamp in milliseconds.
        mtime: Last modification time as a Unix timestamp in milliseconds.
        size: File size in bytes.
    """

    ctime: int
    mtime: int
    size: int


class NoteJson(BaseModel):
    """Structured JSON representation of a note.

    Returned when requesting a file with `ContentType.NOTE_JSON`.

    Attributes:
        content: The raw Markdown content of the note.
        frontmatter: Parsed YAML frontmatter as a dictionary.
        tags: List of tags found in the note.
        path: Path to the file relative to the vault root.
        stat: File system metadata.
    """

    content: str
    frontmatter: dict[str, Any]
    tags: list[str]
    path: str
    stat: FileStat


class DocumentMap(BaseModel):
    """Map of a note's structure (headings, blocks, frontmatter fields).

    Returned when requesting a file with `ContentType.DOCUMENT_MAP`.
    Useful for discovering valid patch targets.

    Attributes:
        headings: List of heading texts in the document.
        blocks: List of block reference IDs.
        frontmatter_fields: List of frontmatter field names.
    """

    model_config = ConfigDict(populate_by_name=True)

    headings: list[str]
    blocks: list[str]
    frontmatter_fields: list[str] = Field(default=[], alias="frontmatterFields")


class VaultInfo(BaseModel):
    """A vault as a whole.

    Attributes:
        name: Name of the vault, the one `ObsidianCLI(vault=)` takes.
        path: Absolute path of the vault folder on this machine.
        files: How many files the vault holds, at any depth.
        folders: How many folders it holds, at any depth.
        size: Total size of every file in bytes.
    """

    name: str
    path: str
    files: int
    folders: int
    size: int


class FolderInfo(BaseModel):
    """A folder in the vault.

    Attributes:
        path: Path to the folder relative to the vault root.
        files: How many files the folder holds, at any depth.
        folders: How many folders it holds, at any depth.
        size: Total size of every file below it in bytes.
    """

    path: str
    files: int
    folders: int
    size: int


class FileInfo(BaseModel):
    """A file in the vault.

    Attributes:
        path: Path to the file relative to the vault root.
        name: File name without its extension.
        extension: Extension without the leading dot, as in `"md"`.
        size: File size in bytes.
        created: When the file was created, in UTC.
        modified: When the file was last modified, in UTC.
    """

    path: str
    name: str
    extension: str
    size: int
    created: datetime
    modified: datetime

    @field_validator("created", "modified", mode="before")
    @classmethod
    def _from_milliseconds(cls, value: Any) -> Any:
        """Read the timestamp Obsidian keeps it in.

        The CLI prints these two straight from the file system record,
        where they are the milliseconds since the epoch.

        Args:
            value: Timestamp field as the CLI prints it.

        Returns:
            The moment those milliseconds name, in UTC, or the value
            untouched if it does not spell a whole number — which is
            left for the field to refuse.
        """
        if not isinstance(value, str):
            return value
        try:
            milliseconds = int(value)
        except ValueError:
            return value
        return datetime.fromtimestamp(milliseconds / _MILLISECONDS, tz=UTC)


class WordCount(BaseModel):
    """How much text a note holds.

    Both counts are the ones Obsidian shows in its status bar, and both
    are taken over the body alone — a note's frontmatter counts for
    nothing.

    Attributes:
        words: Number of words.
        characters: Number of characters, whitespace included. Obsidian
            counts them as JavaScript does, so a character outside the
            Basic Multilingual Plane, an emoji among them, counts twice.
    """

    words: int
    characters: int
