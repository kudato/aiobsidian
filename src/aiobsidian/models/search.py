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
    """One thing a search matched, and the line it sits on.

    Attributes:
        line: Line number within the note, counting from 1.
        text: The line the match sits on, with its indentation trimmed
            off.
    """

    line: int
    text: str


class MatchedFile(BaseModel):
    """A note a search matched, and where in it.

    Attributes:
        file: Path to the note relative to the vault root.
        matches: One entry per match, in the order they occur, so a line
            matched twice is listed twice. Empty when the query matched
            the note without matching its text — on its name or one of
            its properties.
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
