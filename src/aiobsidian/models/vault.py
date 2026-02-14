from typing import Any

from pydantic import BaseModel


class FileStat(BaseModel):
    ctime: int
    mtime: int
    size: int


class NoteJson(BaseModel):
    content: str
    frontmatter: dict[str, Any]
    tags: list[str]
    path: str
    stat: FileStat


class DocumentMap(BaseModel):
    headings: list[str]
    blocks: list[str]
    frontmatter_fields: list[str] = []


class VaultDirectory(BaseModel):
    files: list[str]
