"""What every public model reads off the wire, model by model.

The resource tests exercise the models with whole command outputs and
whole response bodies, so a broken field alias only surfaces if some
resource test happens to touch it. This asks each model directly:

- the wire spelling — aliases included — reads into the documented
  attributes, with the types they promise, from the strings a CLI table
  holds as well as from real JSON;
- what a model writes it can read back, spelled by alias and spelled by
  field name both, which is what `populate_by_name` is for;
- the validators refuse what they document refusing, rather than
  quietly reading it as something else.

`CASES` names every model `aiobsidian.models` exports, and a test here
fails when one is added without an entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import aiobsidian.models
from aiobsidian.models import (
    Backlink,
    BaseView,
    Bookmark,
    Command,
    DocumentMap,
    FileInfo,
    FileStat,
    FileVersion,
    FolderInfo,
    Heading,
    Hotkey,
    MatchedFile,
    MatchedLine,
    MatchSpan,
    NoteJson,
    Plugin,
    PluginInfo,
    PublishChange,
    PublishSite,
    SearchMatch,
    SearchResult,
    ServerStatus,
    SyncStatus,
    Tag,
    Task,
    VaultInfo,
    Versions,
    WordCount,
)

# The moments Obsidian keeps as whole milliseconds since the epoch, and
# what they name in UTC.
_CTIME = 1786836399339
_MTIME = 1786922799339
_CREATED = datetime(2026, 8, 15, 23, 26, 39, 339000, tzinfo=UTC)
_MODIFIED = datetime(2026, 8, 16, 23, 26, 39, 339000, tzinfo=UTC)


@dataclass(frozen=True, slots=True)
class Case:
    """One model and one record it must read.

    Attributes:
        model: The model class.
        payload: The record in its wire spelling: alias names, and the
            printed strings of a CLI table where that is what feeds the
            model.
        expected: Attribute values the model must read out of it.
        label: Distinguishes two records for the same model.
    """

    model: type[BaseModel]
    payload: dict[str, Any]
    expected: dict[str, Any] = field(default_factory=dict)
    label: str = ""

    def __str__(self) -> str:
        name = self.model.__name__
        return f"{name}[{self.label}]" if self.label else name


CASES = (
    # The CLI list commands print tables, and a table holds text, so
    # these payloads carry their numbers and booleans as the strings the
    # rows really hold.
    Case(
        Backlink,
        {"file": "notes/hello.md", "count": "4"},
        {"file": "notes/hello.md", "count": 4},
    ),
    Case(
        BaseView,
        {"name": "All tasks", "type": "table"},
        {"name": "All tasks", "type": "table"},
    ),
    Case(
        Bookmark,
        {"type": "file", "value": "notes/hello.md#Heading", "title": "Hello"},
        {"value": "notes/hello.md#Heading"},
    ),
    Case(
        Command,
        {"id": "graph:open", "name": "Graph view: Open graph view"},
        {"id": "graph:open"},
    ),
    Case(
        DocumentMap,
        {
            "headings": ["Hello", "Hello::Details"],
            "blocks": ["abc123"],
            "frontmatterFields": ["title"],
        },
        {"frontmatter_fields": ["title"]},
    ),
    Case(
        FileInfo,
        {
            "path": "notes/hello.md",
            "name": "hello",
            "extension": "md",
            "size": "137",
            "created": str(_CTIME),
            "modified": str(_MTIME),
        },
        {"size": 137, "created": _CREATED, "modified": _MODIFIED},
    ),
    Case(
        FileStat,
        {"ctime": _CTIME, "mtime": _MTIME, "size": 42},
        {"created": _CREATED, "modified": _MODIFIED, "size": 42},
    ),
    Case(
        FileVersion,
        {"version": "2", "modified": "2026-08-16 02:38", "size": "431 B"},
        {"version": 2, "modified": datetime(2026, 8, 16, 2, 38), "size": "431 B"},
    ),
    Case(
        FolderInfo,
        {"path": "notes", "files": "3", "folders": "0", "size": "305"},
        {"files": 3, "folders": 0, "size": 305},
    ),
    Case(
        Heading,
        {"level": 2, "heading": "Details", "line": 5},
        {"level": 2, "text": "Details", "line": 5},
    ),
    Case(
        Hotkey,
        {"id": "editor:save-file", "hotkey": "⌘ S, ⌘ ⇧ S", "custom": "custom"},
        {"command_id": "editor:save-file", "keys": ["⌘ S", "⌘ ⇧ S"], "custom": True},
    ),
    Case(MatchSpan, {"start": 0, "end": 5}, {"start": 0, "end": 5}),
    Case(
        MatchedFile,
        {"file": "notes/hello.md", "matches": [{"line": 3, "text": "hello world"}]},
        {"file": "notes/hello.md"},
    ),
    Case(
        MatchedLine,
        {"line": 3, "text": "hello world"},
        {"line": 3, "text": "hello world"},
    ),
    Case(
        NoteJson,
        {
            "content": "# Hello\nWorld",
            "frontmatter": {"title": "Hello"},
            "tags": ["greeting"],
            "path": "notes/hello.md",
            "stat": {"ctime": _CTIME, "mtime": _MTIME, "size": 42},
        },
        {"path": "notes/hello.md"},
    ),
    Case(
        Plugin,
        {"id": "dataview", "version": "0.5.68"},
        {"version": "0.5.68"},
        label="community",
    ),
    Case(
        Plugin,
        {"id": "backlink", "version": ""},
        {"version": None},
        label="core",
    ),
    Case(
        PluginInfo,
        {
            "type": "community",
            "name": "Dataview",
            "enabled": "true",
            "version": "0.5.68",
            "author": "Michael Brenan",
            "description": "Advanced queries",
        },
        {"enabled": True, "version": "0.5.68"},
        label="community",
    ),
    Case(
        PluginInfo,
        {"type": "core", "name": "Backlinks", "enabled": "false"},
        {"enabled": False, "version": None, "author": None, "description": None},
        label="core",
    ),
    Case(
        PublishChange,
        {"type": "new", "path": "notes/hello.md"},
        {"type": "new"},
    ),
    Case(
        PublishSite,
        {
            "slug": "my-notes",
            "url": "https://publish.obsidian.md/my-notes",
            "custom": "example.com",
        },
        {"custom_url": "example.com"},
    ),
    Case(
        SearchMatch,
        {"match": {"start": 0, "end": 5}, "context": "Hello world"},
        {"context": "Hello world"},
    ),
    Case(
        SearchResult,
        {
            "filename": "notes/hello.md",
            "score": 0.95,
            "matches": [{"match": {"start": 0, "end": 5}, "context": "Hello world"}],
        },
        {"score": 0.95},
        label="simple",
    ),
    Case(
        SearchResult,
        {"filename": "games/elden-ring.md"},
        {"score": None, "matches": None, "result": None},
        label="defaults",
    ),
    Case(
        ServerStatus,
        {
            "status": "OK",
            "service": "Obsidian Local REST API",
            "authenticated": True,
            "versions": {"obsidian": "1.13.7", "self": "5.1.0"},
            # Fields the endpoint sends and the model documents
            # ignoring, so a new one cannot break status().
            "manifest": {"id": "obsidian-local-rest-api"},
            "certificateInfo": {"validFrom": "2024-01-01"},
        },
        {"authenticated": True},
    ),
    Case(
        SyncStatus,
        {
            "status": "synced",
            "vault": "Main",
            "device": "MacBook",
            "vault size": "4.06 KB",
            "account usage": "1.2 MB / 10 GB",
        },
        {
            "vault_size": "4.06 KB",
            "account_used": "1.2 MB",
            "account_limit": "10 GB",
        },
        label="whole",
    ),
    Case(
        SyncStatus,
        {"status": "disconnected"},
        {"vault": None, "vault_size": None, "account_used": None},
        label="bare",
    ),
    Case(
        Tag,
        {"tag": "#python", "count": "4"},
        {"name": "python", "count": 4},
    ),
    Case(
        Task,
        {"status": " ", "text": "- [ ] write tests", "file": "todo.md", "line": "5"},
        {"line": 5, "done": False},
    ),
    Case(
        VaultInfo,
        {
            "name": "TestVault",
            "path": "/vaults/TestVault",
            "files": "47",
            "folders": "14",
            "size": "2825",
        },
        {"files": 47, "folders": 14, "size": 2825},
    ),
    Case(
        Versions,
        {"obsidian": "1.13.7", "self": "5.1.0"},
        {"obsidian": "1.13.7", "self_": "5.1.0"},
    ),
    Case(
        WordCount,
        {"words": "500", "characters": "2800"},
        {"words": 500, "characters": 2800},
    ),
)


def test_every_public_model_has_a_case():
    # Guards the check below: an emptied export list would pass by
    # having nothing to compare.
    assert len(aiobsidian.models.__all__) > 20

    covered = {case.model.__name__ for case in CASES}
    missing = sorted(set(aiobsidian.models.__all__) - covered)
    assert not missing, (
        f"add {', '.join(missing)} to CASES: until then nothing checks their "
        f"aliases, defaults or round-trips directly"
    )


@pytest.mark.parametrize("case", CASES, ids=str)
def test_reads_the_wire_spelling(case):
    read = case.model.model_validate(case.payload)
    for name, value in case.expected.items():
        assert getattr(read, name) == value, name


@pytest.mark.parametrize("case", CASES, ids=str)
def test_reads_back_what_it_writes_by_alias(case):
    # `model_dump(by_alias=True)` is the wire spelling, so a model that
    # cannot read its own dump has an alias working in one direction.
    read = case.model.model_validate(case.payload)
    assert case.model.model_validate(read.model_dump(by_alias=True)) == read


@pytest.mark.parametrize("case", CASES, ids=str)
def test_reads_back_what_it_writes_by_name(case):
    # The other spelling, which is what `populate_by_name` promises for
    # every model that renames a field.
    read = case.model.model_validate(case.payload)
    assert case.model.model_validate(read.model_dump()) == read


class TestMomentsFromMilliseconds:
    """The rule both file records read their two moments by.

    `FileStat` is the public model that inherits it; `FileInfo` shares
    the rule by construction.
    """

    def _stat(self, moment: Any) -> FileStat:
        return FileStat.model_validate({"ctime": moment, "mtime": _MTIME, "size": 42})

    def test_reads_milliseconds_however_they_are_spelled(self):
        # As text or as a number, the moment is the same moment.
        assert self._stat(str(_CTIME)).created == self._stat(_CTIME).created == _CREATED

    def test_small_numbers_are_still_milliseconds(self):
        # A number that would pass for seconds is not read as seconds.
        assert self._stat(1000).created == datetime(1970, 1, 1, 0, 0, 1, tzinfo=UTC)

    def test_refuses_a_fraction_of_a_millisecond(self):
        with pytest.raises(ValidationError):
            self._stat(1786836399339.5)

    def test_refuses_a_whole_number_written_with_a_fraction(self):
        # `1786836399.0` is how a seconds timestamp usually looks; it is
        # refused rather than guessed at.
        with pytest.raises(ValidationError):
            self._stat("1786836399.0")

    def test_refuses_milliseconds_beyond_any_moment(self):
        with pytest.raises(ValidationError):
            self._stat("9" * 20)

    def test_reads_a_spelled_out_moment_with_a_zone(self):
        read = self._stat("2026-08-15T23:26:39.339000+02:00")
        assert read.created == datetime(2026, 8, 15, 21, 26, 39, 339000, tzinfo=UTC)
        assert read.created.tzinfo == UTC

    def test_refuses_a_spelled_out_moment_without_a_zone(self):
        # There would be no telling which zone it was written in.
        with pytest.raises(ValidationError):
            self._stat("2026-08-15T23:26:39")

    def test_refuses_a_datetime_without_a_zone(self):
        with pytest.raises(ValidationError):
            self._stat(datetime(2026, 8, 15, 23, 26, 39))

    def test_moves_an_aware_datetime_into_utc(self):
        zone = timezone(timedelta(hours=2))
        read = self._stat(datetime(2026, 8, 15, 23, 26, 39, tzinfo=zone))
        assert read.created == datetime(2026, 8, 15, 21, 26, 39, tzinfo=UTC)
        assert read.created.tzinfo == UTC

    def test_refuses_what_spells_no_moment_at_all(self):
        with pytest.raises(ValidationError):
            self._stat("yesterday")


class TestFileVersion:
    def test_reads_digits_of_another_locale(self):
        # Obsidian formats the timestamp under the app's locale, and an
        # Arabic UI rewrites every digit.
        read = FileVersion.model_validate(
            {"version": "1", "modified": "٢٠٢٦-٠٨-١٦ ٠٢:٣٨", "size": "431 B"}
        )
        assert read.modified == datetime(2026, 8, 16, 2, 38)

    def test_refuses_what_spells_no_timestamp(self):
        with pytest.raises(ValidationError):
            FileVersion.model_validate(
                {"version": "1", "modified": "a minute ago", "size": "431 B"}
            )


class TestHotkey:
    def test_an_unbound_command_has_no_keys(self):
        read = Hotkey.model_validate(
            {"id": "editor:save-file", "hotkey": "", "custom": "default"}
        )
        assert read.keys == []
        assert read.custom is False

    def test_a_word_that_is_neither_custom_nor_default_is_refused(self):
        with pytest.raises(ValidationError):
            Hotkey.model_validate(
                {"id": "editor:save-file", "hotkey": "⌘ S", "custom": "sometimes"}
            )


class TestTag:
    def test_a_name_without_the_sigil_is_left_alone(self):
        # `tags.get()` answers relations without the `#`; the validator
        # only drops one that is there.
        assert Tag.model_validate({"tag": "python", "count": "1"}).name == "python"


class TestTask:
    @pytest.mark.parametrize(
        ("status", "done"), [(" ", False), ("x", True), ("/", True)]
    )
    def test_only_a_blank_checkbox_is_not_done(self, status, done):
        read = Task.model_validate(
            {"status": status, "text": "- task", "file": "todo.md", "line": 1}
        )
        assert read.done is done


class TestPlugin:
    def test_a_listing_without_the_version_column_is_refused(self):
        # Required on purpose: a listing printed without the column
        # would otherwise read as all-core.
        with pytest.raises(ValidationError):
            Plugin.model_validate({"id": "dataview"})


class TestPluginInfo:
    def test_a_blank_author_reads_as_none(self):
        read = PluginInfo.model_validate(
            {
                "type": "community",
                "name": "Dataview",
                "enabled": "true",
                "version": "0.5.68",
                "author": "",
                "description": "Advanced queries",
            }
        )
        assert read.author is None

    def test_a_core_plugin_with_a_manifest_field_is_refused(self):
        with pytest.raises(ValidationError, match="no manifest"):
            PluginInfo.model_validate(
                {
                    "type": "core",
                    "name": "Backlinks",
                    "enabled": "true",
                    "version": "1.0.0",
                }
            )

    def test_a_community_plugin_without_a_version_is_refused(self):
        with pytest.raises(ValidationError, match="version"):
            PluginInfo.model_validate(
                {"type": "community", "name": "Dataview", "enabled": "true"}
            )


class TestSyncStatus:
    def test_a_usage_line_naming_one_size_is_refused(self):
        with pytest.raises(ValidationError, match="one size"):
            SyncStatus.model_validate(
                {
                    "status": "synced",
                    "vault size": "4.06 KB",
                    "account usage": "1.2 MB",
                }
            )

    def test_a_quota_reported_by_halves_is_refused(self):
        # The three sizes come of one request, so some without the rest
        # is a record Sync cannot report.
        with pytest.raises(ValidationError, match="whole or not at all"):
            SyncStatus.model_validate({"status": "synced", "vault size": "4.06 KB"})


class TestDocumentMap:
    def test_frontmatter_fields_default_to_none_at_all(self):
        read = DocumentMap.model_validate({"headings": [], "blocks": []})
        assert read.frontmatter_fields == []
