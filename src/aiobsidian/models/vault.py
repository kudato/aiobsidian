from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_MILLISECONDS = 1000


def _spells_a_number(printed: str) -> bool:
    """Tell a printed number from a timestamp written out in full.

    Args:
        printed: Timestamp field as the CLI prints it.

    Returns:
        `True` if Python can read the whole of it as a number.
    """
    try:
        float(printed)
    except ValueError:
        return False
    return True


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
        path: Absolute path of the vault folder on this machine. Only a
            vault kept in a file system has one, which every vault the
            CLI can reach is, since it talks to the desktop app.
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
        extension: Extension without the leading dot, in lower case, so
            `README.MD` reports `"md"`. Empty when the name holds no
            dot, or its last dot opens or closes it, as in `.gitignore`
            and `note.`. `name` keeps the case it was written in, so
            the two need not spell the file name back.
        size: File size in bytes.
        created: When the file was created, in UTC. A file system that
            records no creation time reports the epoch instead.
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
        """Read the timestamp in the unit Obsidian keeps it in.

        The CLI prints these two straight from the file system record,
        where they are the whole milliseconds since the epoch. Every
        number is read in that unit, however small — a timestamp that
        would pass for a plausible number of seconds is still
        milliseconds — and one that is not whole is refused rather than
        read in some other unit.

        A timestamp written out in full is left alone, so the model
        still reads back the one it prints out itself.

        Args:
            value: Timestamp field as the CLI prints it.

        Returns:
            The moment those milliseconds name, in UTC, or the value
            untouched when it spells no number at all — which the field
            knows how to read for itself, or will refuse.

        Raises:
            ValueError: If the number names no moment in milliseconds.
        """
        if not isinstance(value, str) or not _spells_a_number(value):
            return value
        try:
            return datetime.fromtimestamp(int(value) / _MILLISECONDS, tz=UTC)
        except (ValueError, OverflowError, OSError) as exc:
            raise ValueError(f"not a moment in milliseconds: {value!r}") from exc


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
