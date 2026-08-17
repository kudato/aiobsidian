from __future__ import annotations

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


class MatchedLine(BaseModel):
    """A line of a note that a search matched.

    Attributes:
        line: Line number within the note, counting from 1.
        text: The line as the note writes it.
    """

    line: int
    text: str


class MatchedFile(BaseModel):
    """A note a search matched, with the lines it matched on.

    Attributes:
        file: Path to the note relative to the vault root.
        matches: The matching lines, in the order they appear in the
            note. Empty when the query matched the note without
            matching any line of it.
    """

    file: str
    matches: list[MatchedLine]


class SearchResult(BaseModel):
    """A search result entry.

    Attributes:
        filename: Path to the matching file relative to the vault root.
        score: Relevance score (present for simple search).
        matches: List of match locations with context
            (present for simple search).
        result: What the query evaluated to for this file (present for
            JsonLogic queries). Any JSON type: a predicate yields
            `True`, a field lookup yields that field's value.
    """

    filename: str
    score: float | None = None
    matches: list[SearchMatch] | None = None
    result: str | bool | int | float | dict[str, Any] | list[Any] | None = None
