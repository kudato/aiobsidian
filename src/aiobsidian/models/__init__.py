"""Pydantic models returned by the resource methods."""

from .bases import BaseView
from .bookmarks import Bookmark
from .commands import Command
from .history import FileVersion
from .hotkeys import Hotkey
from .links import Backlink
from .outline import Heading
from .plugins import Plugin, PluginInfo
from .publish import PublishChange, PublishSite
from .search import MatchedFile, MatchedLine, MatchSpan, SearchMatch, SearchResult
from .sync import SyncStatus
from .system import ServerStatus, Versions
from .tags import Tag
from .tasks import Task
from .vault import (
    DocumentMap,
    FileInfo,
    FileStat,
    FolderInfo,
    NoteJson,
    VaultInfo,
    WordCount,
)

__all__ = [
    "Backlink",
    "BaseView",
    "Bookmark",
    "Command",
    "DocumentMap",
    "FileInfo",
    "FileStat",
    "FileVersion",
    "FolderInfo",
    "Heading",
    "Hotkey",
    "MatchSpan",
    "MatchedFile",
    "MatchedLine",
    "NoteJson",
    "Plugin",
    "PluginInfo",
    "PublishChange",
    "PublishSite",
    "SearchMatch",
    "SearchResult",
    "ServerStatus",
    "SyncStatus",
    "Tag",
    "Task",
    "VaultInfo",
    "Versions",
    "WordCount",
]
