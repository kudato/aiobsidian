"""Async Python client for Obsidian Local REST API."""

from ._client import ObsidianClient
from ._exceptions import APIError, AuthenticationError, NotFoundError, ObsidianError
from ._types import ContentType, PatchOperation, Period, TargetType
from .models.commands import Command
from .models.search import SearchMatch, SearchResult
from .models.system import ServerStatus, Versions
from .models.vault import DocumentMap, FileStat, NoteJson, VaultDirectory

__all__ = [
    "APIError",
    "AuthenticationError",
    "Command",
    "ContentType",
    "DocumentMap",
    "FileStat",
    "NotFoundError",
    "NoteJson",
    "ObsidianClient",
    "ObsidianError",
    "PatchOperation",
    "Period",
    "SearchMatch",
    "SearchResult",
    "ServerStatus",
    "TargetType",
    "Versions",
    "VaultDirectory",
]
