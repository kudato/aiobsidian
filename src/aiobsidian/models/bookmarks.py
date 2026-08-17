from __future__ import annotations

from pydantic import BaseModel


class Bookmark(BaseModel):
    """A bookmark.

    Attributes:
        type: What is bookmarked: `"file"`, `"folder"`, `"search"`,
            `"url"`, `"group"` for a folder of bookmarks, or `"graph"`.
        value: The path, query or URL the bookmark points at, according
            to `type`. A file bookmark carries its subpath along, as in
            `"notes/hello.md#Heading"`. Empty for a bookmark that points
            at nothing of its own, such as a group.
        title: Display title. Obsidian falls back to the file's short
            name or the search query when the bookmark carries none of
            its own, and leaves it empty when it has neither.
    """

    type: str
    value: str
    title: str
