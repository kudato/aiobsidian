"""Async Python client for Obsidian CLI and Local REST API plugin."""

from ._cli import ObsidianCLI
from ._client import ObsidianClient
from ._exceptions import (
    APIError,
    APINotFoundError,
    AuthenticationError,
    BinaryNotFoundError,
    CLIError,
    CLINotFoundError,
    CLIParseError,
    CLITimeoutError,
    CommandError,
    NotFoundError,
    ObsidianError,
)
from ._types import (
    ContentType,
    JsonValue,
    PatchOperation,
    PropertyType,
    PropertyValue,
    TargetType,
)
from .models.commands import Command
from .models.search import MatchSpan, SearchMatch, SearchResult
from .models.system import ServerStatus, Versions
from .models.vault import DocumentMap, FileStat, NoteJson, VaultDirectory

__all__ = [
    "APIError",
    "APINotFoundError",
    "AuthenticationError",
    "BinaryNotFoundError",
    "CLIError",
    "CLINotFoundError",
    "CLIParseError",
    "CLITimeoutError",
    "Command",
    "CommandError",
    "ContentType",
    "DocumentMap",
    "FileStat",
    "JsonValue",
    "MatchSpan",
    "NotFoundError",
    "NoteJson",
    "ObsidianCLI",
    "ObsidianClient",
    "ObsidianError",
    "PatchOperation",
    "PropertyType",
    "PropertyValue",
    "SearchMatch",
    "SearchResult",
    "ServerStatus",
    "TargetType",
    "Versions",
    "VaultDirectory",
]
