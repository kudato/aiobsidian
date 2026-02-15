from typing import Any

from pydantic import BaseModel, Field


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

    headings: list[str]
    blocks: list[str]
    frontmatter_fields: list[str] = Field(default=[], alias="frontmatterFields")


class VaultDirectory(BaseModel):
    """Directory listing of files in the vault.

    Attributes:
        files: List of file paths relative to the vault root.
    """

    files: list[str]
