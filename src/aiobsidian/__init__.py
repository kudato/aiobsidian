"""Async Python client for Obsidian CLI and Local REST API plugin."""

from ._cli import ObsidianCLI
from ._client import ObsidianClient
from ._exceptions import (
    APIError,
    AuthenticationError,
    BinaryNotFoundError,
    CLIError,
    CLITimeoutError,
    CommandError,
    NotFoundError,
    ObsidianError,
)
from ._types import ContentType, PatchOperation, Period, TargetType
from .models.commands import Command
from .models.search import MatchSpan, SearchMatch, SearchResult
from .models.system import ServerStatus, Versions
from .models.vault import DocumentMap, FileStat, NoteJson, VaultDirectory

__all__ = [
    "APIError",
    "AuthenticationError",
    "BinaryNotFoundError",
    "CLIError",
    "CLITimeoutError",
    "Command",
    "CommandError",
    "ContentType",
    "DocumentMap",
    "FileStat",
    "MatchSpan",
    "NotFoundError",
    "NoteJson",
    "ObsidianCLI",
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
