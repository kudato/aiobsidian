from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

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
    def _parse_json_rows[ModelT: BaseModel](
        cls, command: str, output: str, model: type[ModelT]
    ) -> list[ModelT]:
        """Parse JSON output whose objects are the rows of a table.

        Asked for `format=json`, the CLI still prints a table, and a
        table holds text: `tasks` reports a line number as `"5"` and
        `tags` a count as `"4"`. The model names the columns and hands
        the values back with the types they had.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            model: Model to validate every row against.

        Returns:
            One model per row, in the order printed, or an empty list
            for an empty result.

        Raises:
            CLIParseError: If the output is not valid JSON, is not a
                list, or a row does not fit the model.
        """
        rows = cls._parse_json(command, output)
        if not isinstance(rows, list):
            raise CLIParseError(command, output)
        try:
            return [model.model_validate(row) for row in rows]
        except ValidationError as exc:
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
    def _parse_fields_as[ModelT: BaseModel](
        cls,
        command: str,
        output: str,
        model: type[ModelT],
        *,
        separator: str = "\t",
        strict: bool = True,
    ) -> ModelT:
        """Parse `key<separator>value` output into a model.

        The commands that describe one thing print a field per line
        rather than a table, and print text: `file` reports a size as
        `"55"` and a timestamp as the milliseconds behind it. The model
        names the fields and hands the values back with the types they
        had, and says for itself what a field the CLI leaves out is
        worth without it. Values come back as printed, save at the two
        ends of the output, where the blank space around the whole of it
        goes before the lines are counted.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            model: Model to validate the fields against.
            separator: Separator between key and value, blank space
                included. The commands that separate with a colon write
                a space after it, and passing `": "` keeps that space
                out of the value rather than trimming it back off, which
                would take a value's own with it.
            strict: If `False`, skip lines without the separator instead
                of refusing to parse. Some commands mix a plain sentence
                into the field list.

        Returns:
            The model built from the fields the CLI printed.

        Raises:
            CLIParseError: If `strict` and a line does not contain the
                separator, or the fields do not fit the model.
        """
        fields: dict[str, str] = {}
        for line in cls._parse_lines(output):
            key, found, value = line.partition(separator)
            if not found:
                if strict:
                    raise CLIParseError(command, output)
                continue
            fields[key] = value
        try:
            return model.model_validate(fields)
        except ValidationError as exc:
            raise CLIParseError(command, output) from exc

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
    def _parse_rows_as[ModelT: BaseModel](
        cls,
        command: str,
        output: str,
        model: type[ModelT],
        *,
        columns: tuple[str, ...],
        heading: bool = False,
    ) -> list[ModelT]:
        """Parse tab-separated output into models, one per row.

        The commands without a `format=` print their table as plain
        text, so the column names live here rather than in the output,
        and every line has to hold one value per column. Values come
        back as printed, save at the two ends of the output: the blank
        space around the whole of it goes before the lines are counted,
        so a first value starting with one, or a last value ending in
        one, loses it.

        Args:
            command: CLI command name, used for error reporting.
            output: Raw output of the command.
            model: Model to validate every row against.
            columns: Column names, in the order the CLI prints them.
            heading: If `True`, drop the first line: `history` names the
                file above its table.

        Returns:
            One model per row, in the order printed, or an empty list
            for an empty result.

        Raises:
            CLIParseError: If a row does not carry one value per column,
                or does not fit the model.
        """
        lines = cls._parse_lines(output)
        if heading:
            lines = lines[1:]
        values: list[ModelT] = []
        for line in lines:
            row = line.split("\t")
            if len(row) != len(columns):
                raise CLIParseError(command, output)
            try:
                values.append(model.model_validate(dict(zip(columns, row))))
            except ValidationError as exc:
                raise CLIParseError(command, output) from exc
        return values
