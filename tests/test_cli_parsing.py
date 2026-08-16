from __future__ import annotations

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.cli._base import BaseCLIResource


class TestIsEmptyResult:
    @pytest.mark.parametrize(
        "output",
        [
            "No tasks found.",
            "No matches found.",
            "No backlinks found.",
            "No workspaces saved.",
            "No errors captured.",
        ],
    )
    def test_sentinels(self, output):
        assert BaseCLIResource._is_empty_result(output)

    @pytest.mark.parametrize(
        "output",
        [
            "[]",
            "No sugar please\nsecond line",
            "Notes.md",
            "",
        ],
    )
    def test_not_sentinels(self, output):
        assert not BaseCLIResource._is_empty_result(output)


class TestParseJson:
    def test_object(self):
        assert BaseCLIResource._parse_json("tags", '{"tag": "#a"}') == {"tag": "#a"}

    def test_empty_sentinel_defaults_to_list(self):
        assert BaseCLIResource._parse_json("tasks", "No tasks found.\n") == []

    def test_empty_sentinel_custom_value(self):
        result = BaseCLIResource._parse_json(
            "properties", "No properties found.\n", empty={}
        )
        assert result == {}

    def test_blank_output(self):
        assert BaseCLIResource._parse_json("tags", "   \n") == []

    def test_invalid_json(self):
        with pytest.raises(CLIParseError) as exc_info:
            BaseCLIResource._parse_json("tags", "plain text output")
        assert exc_info.value.command == "tags"
        assert exc_info.value.output == "plain text output"


class TestParseLines:
    def test_lines(self):
        assert BaseCLIResource._parse_lines("a.md\nb.md\n") == ["a.md", "b.md"]

    def test_skips_blank_lines(self):
        assert BaseCLIResource._parse_lines("a.md\n\nb.md\n") == ["a.md", "b.md"]

    def test_empty_output(self):
        assert BaseCLIResource._parse_lines("") == []

    def test_sentinel(self):
        assert BaseCLIResource._parse_lines("No snippets found.\n") == []


class TestParseFields:
    def test_tab_separated(self):
        output = "name\tMyVault\nfiles\t47\n"
        assert BaseCLIResource._parse_fields("vault", output) == {
            "name": "MyVault",
            "files": "47",
        }

    def test_custom_separator(self):
        output = "words: 10\ncharacters: 84\n"
        result = BaseCLIResource._parse_fields("wordcount", output, separator=":")
        assert result == {"words": "10", "characters": "84"}

    def test_missing_separator(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_fields("vault", "no separator here\n")

    def test_value_may_contain_separator(self):
        output = "path\t/Users/me/My\tVault\n"
        assert BaseCLIResource._parse_fields("vault", output) == {
            "path": "/Users/me/My\tVault"
        }


class TestParseRows:
    def test_rows(self):
        output = "welcome.md\n1\t2026-08-16 02:38\t431 B\n"
        assert BaseCLIResource._parse_rows(output) == [
            ["1", "2026-08-16 02:38", "431 B"]
        ]

    def test_no_rows(self):
        assert BaseCLIResource._parse_rows("welcome.md\n") == []
