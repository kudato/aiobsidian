from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from .._exceptions import CLIParseError

if TYPE_CHECKING:
    from .._cli import ObsidianCLI

_EMPTY_RESULT_PATTERN = re.compile(r"^No [^\n]+\.$")
_ESCAPE_BOUNDARY_PATTERN = re.compile(r"(?<=\\)(?=[nt])")


class BaseCLIResource:
    """Base class for all CLI resource classes."""

    __slots__ = ("_cli",)

    def __init__(self, cli: ObsidianCLI) -> None:
        self._cli = cli

    @staticmethod
    def _split_content(content: str) -> list[str]:
        """Split content where the CLI would reinterpret a backslash escape.

        The CLI replaces the two-character sequences `\\n` and `\\t` in content
        values with a newline and a tab, and offers no way to escape a literal
        backslash. Cutting the content between the backslash and the following
        `n` or `t` keeps the sequence out of any single value, so writing the
        parts one after another round-trips.

        Args:
            content: Content as given by the caller.

        Returns:
            Content parts in write order. A single part when nothing would be
            reinterpreted.
        """
        return _ESCAPE_BOUNDARY_PATTERN.split(content)

    async def _write_parts(
        self,
        command: str,
        parts: list[str],
        *,
        params: dict[str, str] | None = None,
    ) -> None:
        """Write content parts one call each, without adding separators.

        Args:
            command: CLI command to run for every part (e.g. `"append"`).
            parts: Content parts to write, in call order.
            params: Extra parameters passed to every call.
        """
        for part in parts:
            await self._cli._execute(
                command,
                params={**(params or {}), "content": part},
                flags=["inline"],
            )

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
    def _parse_json_column(cls, command: str, output: str, *, key: str) -> list[str]:
        """Parse JSON output whose objects hold a single named value.

        Asked for `format=json`, the CLI prints a table, so a one-column
        answer arrives as a list of one-key objects — `plugins:enabled`
        prints `[{"id": "dataview"}]`. The key names the column rather
        than the value, and is known here, so the values come back on
        their own.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            key: Name of the key holding the value.

        Returns:
            The value of `key` from every object, in the order printed, or
            an empty list for an empty result.

        Raises:
            CLIParseError: If the output is not valid JSON, is not a list
                of objects, or an object does not carry `key` as a string.
        """
        rows = cls._parse_json(command, output)
        if not isinstance(rows, list):
            raise CLIParseError(command, output)
        values: list[str] = []
        for row in rows:
            value = row.get(key) if isinstance(row, dict) else None
            if not isinstance(value, str):
                raise CLIParseError(command, output)
            values.append(value)
        return values

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
        strict: bool = True,
    ) -> dict[str, str]:
        """Parse `key<separator>value` output into a dictionary.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            separator: Separator between key and value.
            strict: If `False`, skip lines without the separator instead of
                refusing to parse. Some commands mix a plain sentence into
                the field list.

        Returns:
            Mapping of keys to values, in the order printed by the CLI.

        Raises:
            CLIParseError: If `strict` and a line does not contain the
                separator.
        """
        fields: dict[str, str] = {}
        for line in cls._parse_lines(output):
            key, found, value = line.partition(separator)
            if not found:
                if strict:
                    raise CLIParseError(command, output)
                continue
            fields[key.strip()] = value.strip()
        return fields

    @staticmethod
    def _strip_content_header(output: str) -> str:
        """Drop the header the CLI prints before a stored file version.

        `history:read` and `sync:read` announce the version they found on
        one line, follow it with a `---` rule and only then print the
        content. The content itself often starts with frontmatter, whose
        own `---` must survive, so exactly the first two lines go.

        Args:
            output: Raw output of the command.

        Returns:
            The content, or the whole output when the header is missing.
        """
        header, rule, content = (output.split("\n", 2) + ["", ""])[:3]
        if rule == "---" and header.endswith(")"):
            return content
        return output

    @staticmethod
    def _strip_path_header(output: str) -> str:
        """Drop the path line the CLI prints before a note it picked itself.

        `random:read` names the note it landed on, leaves a blank line and
        then prints the content.

        Args:
            output: Raw output of the command.

        Returns:
            The content, or the whole output when the header is missing.
        """
        path, blank, content = (output.split("\n", 2) + ["", ""])[:3]
        if blank == "" and path:
            return content
        return output

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
