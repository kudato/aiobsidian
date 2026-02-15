from typing import Any

from pydantic import BaseModel


class MatchSpan(BaseModel):
    """A span representing start and end positions of a match.

    Attributes:
        start: Start position of the match.
        end: End position of the match.
    """

    start: int
    end: int


class SearchMatch(BaseModel):
    """A single match within a search result.

    Attributes:
        match: Span with start and end positions of the match.
        context: Surrounding text context for the match.
    """

    match: MatchSpan
    context: str


class SearchResult(BaseModel):
    """A search result entry.

    Attributes:
        filename: Path to the matching file relative to the vault root.
        score: Relevance score (present for simple search).
        matches: List of match locations with context
            (present for simple search).
        result: Raw result data (present for Dataview/JsonLogic queries).
    """

    filename: str
    score: float | None = None
    matches: list[SearchMatch] | None = None
    result: dict[str, Any] | list[Any] | None = None
