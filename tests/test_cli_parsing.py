from __future__ import annotations

from datetime import datetime

import pytest

from aiobsidian._exceptions import CLIParseError
from aiobsidian.cli._base import BaseCLIResource
from aiobsidian.models.bases import BaseView
from aiobsidian.models.history import FileVersion
from aiobsidian.models.links import Backlink
from aiobsidian.models.sync import SyncStatus
from aiobsidian.models.vault import FolderInfo, WordCount


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


class TestParseJsonColumn:
    def test_column(self):
        output = '[{"id": "backlink"}, {"id": "bookmarks"}]'
        result = BaseCLIResource._parse_json_column("plugins:enabled", output, key="id")
        assert result == ["backlink", "bookmarks"]

    def test_sentinel(self):
        result = BaseCLIResource._parse_json_column(
            "unresolved", "No unresolved links found.\n", key="link"
        )
        assert result == []

    def test_ignores_the_other_columns(self):
        output = '[{"id": "backlink", "version": ""}]'
        result = BaseCLIResource._parse_json_column("plugins:enabled", output, key="id")
        assert result == ["backlink"]

    def test_missing_key(self):
        with pytest.raises(CLIParseError) as exc_info:
            BaseCLIResource._parse_json_column(
                "unresolved", '[{"target": "missing-note"}]', key="link"
            )
        assert exc_info.value.command == "unresolved"

    @pytest.mark.parametrize("output", ['[{"link": 1}]', '[{"link": null}]'])
    def test_non_string_value(self, output):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_column("unresolved", output, key="link")

    def test_not_a_list(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_column(
                "plugins:enabled", '{"id": "backlink"}', key="id"
            )

    def test_not_a_list_of_objects(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_column(
                "plugins:enabled", '["backlink"]', key="id"
            )

    def test_invalid_json(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_column("unresolved", "plain text", key="link")


class TestParseJsonRows:
    def test_rows(self):
        output = '[{"file": "a.md", "count": "2"}, {"file": "b.md", "count": "1"}]'
        result = BaseCLIResource._parse_json_rows("backlinks", output, Backlink)
        assert result == [
            Backlink(file="a.md", count=2),
            Backlink(file="b.md", count=1),
        ]

    def test_sentinel(self):
        result = BaseCLIResource._parse_json_rows(
            "backlinks", "No backlinks found.\n", Backlink
        )
        assert result == []

    def test_missing_column(self):
        with pytest.raises(CLIParseError) as exc_info:
            BaseCLIResource._parse_json_rows(
                "backlinks", '[{"file": "a.md"}]', Backlink
            )
        assert exc_info.value.command == "backlinks"

    def test_column_of_the_wrong_type(self):
        output = '[{"file": "a.md", "count": "many"}]'
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_rows("backlinks", output, Backlink)

    def test_not_a_list(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_rows(
                "backlinks", '{"file": "a.md", "count": "2"}', Backlink
            )

    def test_not_a_list_of_objects(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_rows("backlinks", '["a.md"]', Backlink)

    def test_invalid_json(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_json_rows("backlinks", "plain text", Backlink)


class TestParseRowsAs:
    def test_rows(self):
        output = "All\ttable\nActive\tcards\n"
        result = BaseCLIResource._parse_rows_as(
            "base:views", output, BaseView, columns=("name", "type")
        )
        assert result == [
            BaseView(name="All", type="table"),
            BaseView(name="Active", type="cards"),
        ]

    def test_sentinel(self):
        result = BaseCLIResource._parse_rows_as(
            "base:views", "No views defined.\n", BaseView, columns=("name", "type")
        )
        assert result == []

    def test_drops_the_heading_line_when_asked(self):
        output = "notes/todo.md\n1\t2026-08-16 02:38\t431 B\n"
        result = BaseCLIResource._parse_rows_as(
            "history",
            output,
            FileVersion,
            columns=("version", "modified", "size"),
            heading=True,
        )
        assert result == [
            FileVersion(version=1, modified=datetime(2026, 8, 16, 2, 38), size="431 B")
        ]

    def test_too_many_columns(self):
        with pytest.raises(CLIParseError) as exc_info:
            BaseCLIResource._parse_rows_as(
                "base:views", "All\ttable\textra\n", BaseView, columns=("name", "type")
            )
        assert exc_info.value.command == "base:views"

    def test_too_few_columns(self):
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_rows_as(
                "history",
                "notes/todo.md\n1\t2026-08-16 02:38\n",
                FileVersion,
                columns=("version", "modified", "size"),
                heading=True,
            )

    def test_a_row_that_lost_every_separator(self):
        # `base:views` prints no heading, so such a line is a broken row
        # rather than something to skip.
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_rows_as(
                "base:views", "All\ttable\nActive\n", BaseView, columns=("name", "type")
            )

    def test_values_arrive_verbatim(self):
        # A view is named by whoever wrote the base file, so a name that
        # ends in a space is theirs to keep.
        output = "All\ttable\nActive \tcards\n"
        result = BaseCLIResource._parse_rows_as(
            "base:views", output, BaseView, columns=("name", "type")
        )
        assert result == [
            BaseView(name="All", type="table"),
            BaseView(name="Active ", type="cards"),
        ]

    def test_the_ends_of_the_output_are_still_trimmed(self):
        # `_parse_lines()` strips the blank space around the whole
        # output before counting lines, which no command puts there.
        output = " All\ttable\nActive\tcards \n"
        result = BaseCLIResource._parse_rows_as(
            "base:views", output, BaseView, columns=("name", "type")
        )
        assert result == [
            BaseView(name="All", type="table"),
            BaseView(name="Active", type="cards"),
        ]

    def test_value_of_the_wrong_type(self):
        output = "one\t2026-08-16 02:38\t431 B\n"
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_rows_as(
                "history",
                output,
                FileVersion,
                columns=("version", "modified", "size"),
            )


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


class TestParseFieldsAs:
    def test_fields(self):
        output = "path\tnotes\nfiles\t3\nfolders\t0\nsize\t305\n"
        result = BaseCLIResource._parse_fields_as("folder", output, FolderInfo)
        assert result == FolderInfo(path="notes", files=3, folders=0, size=305)

    def test_custom_separator(self):
        output = "words: 10\ncharacters: 84\n"
        result = BaseCLIResource._parse_fields_as(
            "wordcount", output, WordCount, separator=":"
        )
        assert result == WordCount(words=10, characters=84)

    def test_skips_a_sentence_when_not_strict(self):
        output = "status: disconnected\nSync is not set up for this vault.\n"
        result = BaseCLIResource._parse_fields_as(
            "sync:status", output, SyncStatus, separator=":", strict=False
        )
        assert result == SyncStatus(status="disconnected")

    def test_missing_separator(self):
        with pytest.raises(CLIParseError) as exc_info:
            BaseCLIResource._parse_fields_as(
                "folder", "no separator here\n", FolderInfo
            )
        assert exc_info.value.command == "folder"

    def test_missing_field(self):
        output = "path\tnotes\nfiles\t3\nfolders\t0\n"
        with pytest.raises(CLIParseError) as exc_info:
            BaseCLIResource._parse_fields_as("folder", output, FolderInfo)
        assert exc_info.value.command == "folder"

    def test_value_of_the_wrong_type(self):
        output = "path\tnotes\nfiles\tthree\nfolders\t0\nsize\t305\n"
        with pytest.raises(CLIParseError):
            BaseCLIResource._parse_fields_as("folder", output, FolderInfo)

    def test_ignores_a_field_the_model_does_not_name(self):
        output = "path\tnotes\nfiles\t3\nfolders\t0\nsize\t305\nowner\tme\n"
        result = BaseCLIResource._parse_fields_as("folder", output, FolderInfo)
        assert result == FolderInfo(path="notes", files=3, folders=0, size=305)


class TestSplitContent:
    def test_plain_content_is_one_part(self):
        assert BaseCLIResource._split_content("# Title\n\ntext") == ["# Title\n\ntext"]

    def test_empty_content(self):
        assert BaseCLIResource._split_content("") == [""]

    def test_splits_before_n_and_t(self):
        assert BaseCLIResource._split_content(r"C:\notes\temp") == [
            "C:\\",
            "notes\\",
            "temp",
        ]

    def test_double_backslash(self):
        assert BaseCLIResource._split_content(r"a\\nb") == ["a\\\\", "nb"]

    def test_other_escapes_are_left_alone(self):
        assert BaseCLIResource._split_content(r"a\rb \alpha") == [r"a\rb \alpha"]

    def test_trailing_backslash(self):
        assert BaseCLIResource._split_content("path\\") == ["path\\"]
