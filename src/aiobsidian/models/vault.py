from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from numbers import Number
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)
_WHOLE_NUMBER = re.compile(r"[+-]?[0-9]+")


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


class _MomentsInMilliseconds(BaseModel):
    """What both file records read their two moments by.

    Obsidian keeps one file system record and this library is handed it
    twice, once printed by the CLI and once passed on by the REST
    plugin. The moments in it are the same moments in the same unit, so
    they are read by one rule rather than two.
    """

    @field_validator("created", "modified", mode="before", check_fields=False)
    @classmethod
    def _from_milliseconds(cls, value: Any) -> Any:
        """Read the timestamp in the unit Obsidian keeps it in.

        Obsidian takes these two straight from the file system record,
        where they are the whole milliseconds since the epoch. Every
        number is read in that unit, however small — a timestamp that
        would pass for a plausible number of seconds is still
        milliseconds — and one that is not whole is refused rather than
        read in some other unit, `1786836399.0` included. A number reads
        the same however it is written, as text or as any of the types
        Python counts with, so the answer does not turn on how the model
        was handed it.

        A timestamp written out in full is left alone, so the model
        still reads back the one it writes out itself.

        Args:
            value: Timestamp field as it arrived.

        Returns:
            The moment those milliseconds name, in UTC, or the value
            untouched when it spells no number at all — which the field
            knows how to read for itself, or will refuse.

        Raises:
            ValueError: If the number names no moment in milliseconds.
        """
        if not isinstance(value, str | Number):
            return value
        printed = value if isinstance(value, str) else str(value)
        if _WHOLE_NUMBER.fullmatch(printed):
            try:
                return _EPOCH + timedelta(milliseconds=int(printed))
            except OverflowError as exc:
                raise ValueError(f"not a moment in milliseconds: {printed}") from exc
        if isinstance(value, Number) or _spells_a_number(printed):
            raise ValueError(f"not a whole number of milliseconds: {printed}")
        return value

    @field_validator("created", "modified", mode="after", check_fields=False)
    @classmethod
    def _in_utc(cls, value: datetime) -> datetime:
        """Hold the two moments to the zone they are documented in.

        Args:
            value: The moment the field was built from.

        Returns:
            The same moment in UTC, wherever it was written.

        Raises:
            ValueError: If the moment names no time zone at all.
        """
        if value.tzinfo is None:
            raise ValueError(f"a moment without a time zone: {value.isoformat()}")
        return value.astimezone(UTC)


class FileStat(_MomentsInMilliseconds):
    """File system metadata for a vault file.

    The plugin passes Obsidian's own record on untouched, so the two
    moments are the ones the CLI reports for the same file, and they are
    read into UTC the way `FileInfo` reads them. A moment handed to the
    model without a time zone is refused rather than taken for one:
    there would be no telling which zone it was written in. The plugin
    names them `ctime` and `mtime` on the wire.

    Attributes:
        created: When the file was created, in UTC, as the file system
            reports it. One that records no creation time answers with
            the epoch or with the moment the inode last changed, and the
            second of those passes for a creation time.
        modified: When the file was last modified, in UTC.
        size: File size in bytes.
    """

    model_config = ConfigDict(populate_by_name=True)

    created: datetime = Field(alias="ctime")
    modified: datetime = Field(alias="mtime")
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


class FileInfo(_MomentsInMilliseconds):
    """A file in the vault.

    The two moments are moments in UTC, and a moment handed to the model
    without a time zone is refused rather than taken for one: there
    would be no telling which zone it was written in.

    Attributes:
        path: Path to the file relative to the vault root.
        name: File name without its extension.
        extension: Extension without the leading dot, in lower case, so
            `README.MD` reports `"md"`. Empty when the name holds no
            dot, or its last dot opens or closes it, as in `.gitignore`
            and `note.`. `name` keeps the case it was written in, so
            the two need not spell the file name back.
        size: File size in bytes.
        created: When the file was created, in UTC, as the file system
            reports it. One that records no creation time answers with
            the epoch or with the moment the inode last changed, and
            the second of those passes for a creation time.
        modified: When the file was last modified, in UTC.
    """

    path: str
    name: str
    extension: str
    size: int
    created: datetime
    modified: datetime


class WordCount(BaseModel):
    """How much text a note holds.

    Both counts are taken over the body alone — a note's frontmatter
    counts for nothing.

    Attributes:
        words: Number of words, which need not be the number the status
            bar shows. Obsidian counts words twice over, by two
            expressions that differ in one character: only the status
            bar's reads a typographic apostrophe as part of the word
            around it, so `don’t` is one word there and two here.
        characters: Number of characters, whitespace included, and the
            one the status bar shows. Obsidian counts them as
            JavaScript does, so a character outside the Basic
            Multilingual Plane, an emoji among them, counts twice.
    """

    words: int
    characters: int
