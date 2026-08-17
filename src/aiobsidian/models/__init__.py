"""Pydantic models returned by the resource methods."""

from .bookmarks import Bookmark
from .commands import Command
from .hotkeys import Hotkey
from .links import Backlink
from .plugins import Plugin
from .search import MatchSpan, SearchMatch, SearchResult
from .system import ServerStatus, Versions
from .tags import Tag
from .tasks import Task
from .vault import DocumentMap, FileStat, NoteJson

__all__ = [
    "Backlink",
    "Bookmark",
    "Command",
    "DocumentMap",
    "FileStat",
    "Hotkey",
    "MatchSpan",
    "NoteJson",
    "Plugin",
    "SearchMatch",
    "SearchResult",
    "ServerStatus",
    "Tag",
    "Task",
    "Versions",
]
