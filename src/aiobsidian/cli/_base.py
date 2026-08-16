from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from .._exceptions import CLIParseError

if TYPE_CHECKING:
    from .._cli import ObsidianCLI

_EMPTY_RESULT_PATTERN = re.compile(r"^No [^\n]+\.$")


class BaseCLIResource:
    """Base class for all CLI resource classes."""

    __slots__ = ("_cli",)

    def __init__(self, cli: ObsidianCLI) -> None:
        self._cli = cli

    @staticmethod
    def _is_empty_result(output: str) -> bool:
        """Check whether the output is the CLI's "nothing found" sentinel.

        For an empty result set the CLI prints a single human-readable line
        such as `No tasks found.` or `No workspaces saved.`, even when JSON
        output is requested.

        Args:
            output: Raw output of the command.

        Returns:
            `True` if the output announces an empty result.
        """
        return _EMPTY_RESULT_PATTERN.match(output.strip()) is not None

    @classmethod
    def _parse_json(cls, command: str, output: str, *, empty: Any = None) -> Any:
        """Parse JSON output of a command that supports `format=json`.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            empty: Value to return for an empty result. Defaults to `[]`.

        Returns:
            The decoded JSON value, or `empty` if the result set is empty.

        Raises:
            CLIParseError: If the output is not valid JSON.
        """
        stripped = output.strip()
        if not stripped or cls._is_empty_result(stripped):
            return [] if empty is None else empty
        try:
            return json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise CLIParseError(command, output) from exc

    @classmethod
    def _parse_lines(cls, output: str) -> list[str]:
        """Parse output that lists one item per line.

        Args:
            output: Raw output of the command.

        Returns:
            List of non-empty lines, or an empty list for an empty result.
        """
        stripped = output.strip()
        if not stripped or cls._is_empty_result(stripped):
            return []
        return [line for line in stripped.splitlines() if line.strip()]

    @classmethod
    def _parse_fields(
        cls,
        command: str,
        output: str,
        *,
        separator: str = "\t",
    ) -> dict[str, str]:
        """Parse `key<separator>value` output into a dictionary.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            separator: Separator between key and value.

        Returns:
            Mapping of keys to values, in the order printed by the CLI.

        Raises:
            CLIParseError: If a line does not contain the separator.
        """
        fields: dict[str, str] = {}
        for line in cls._parse_lines(output):
            key, found, value = line.partition(separator)
            if not found:
                raise CLIParseError(command, output)
            fields[key.strip()] = value.strip()
        return fields

    @classmethod
    def _parse_rows(cls, output: str, *, separator: str = "\t") -> list[list[str]]:
        """Parse tabular output into rows of columns.

        Lines without the separator are skipped: some commands print a
        heading line before the table.

        Args:
            output: Raw output of the command.
            separator: Separator between columns.

        Returns:
            List of rows, each a list of column values.
        """
        rows: list[list[str]] = []
        for line in cls._parse_lines(output):
            if separator not in line:
                continue
            rows.append([column.strip() for column in line.split(separator)])
        return rows
