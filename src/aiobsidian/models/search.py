from typing import Any

from pydantic import BaseModel


class SearchMatch(BaseModel):
    match: dict[str, int]
    context: str


class SearchResult(BaseModel):
    filename: str
    score: float | None = None
    matches: list[SearchMatch] | None = None
    result: Any = None
