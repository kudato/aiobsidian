"""What the grammar check refuses, and what the table it reads holds.

The check runs on every command line the CLI tests build, so it has to
be right about which of them Obsidian would accept. The cases below are
the mistakes it exists for — most of them mistakes this library actually
shipped, each with a green test suite behind it.
"""

from __future__ import annotations

import re

import pytest

from .grammar import Grammar, GrammarError

GRAMMAR = Grammar.load()


def test_names_the_obsidian_release_it_was_read_from():
    assert GRAMMAR.obsidian.count(".") == 2


def test_holds_the_commands_the_library_sends():
    # A table that loaded but came back nearly empty would let every
    # check below pass by having nothing to check against.
    assert len(GRAMMAR.commands) > 100
    assert {"read", "create", "append", "tasks", "plugins:enabled"} <= set(
        GRAMMAR.commands
    )


def test_accepts_a_command_line_the_library_builds():
    GRAMMAR.check("tags", params={"path": "notes/setup.md"}, flags=["counts"])


def test_accepts_the_vault_every_command_is_given():
    # `vault=` is the CLI's own option rather than any command's, and
    # `_execute` puts it on every line it builds.
    GRAMMAR.check("version", params={"vault": "TestVault"})


@pytest.mark.parametrize("command", ["task:create", "tags:rename", "note:read"])
def test_refuses_a_command_obsidian_does_not_register(command):
    with pytest.raises(GrammarError, match="no command"):
        GRAMMAR.check(command)


def test_names_the_commands_a_misspelt_one_might_have_meant():
    with pytest.raises(GrammarError, match="plugin:enable"):
        GRAMMAR.check("plugin:activate", params={"id": "dataview"})


def test_resolves_a_command_that_is_a_flag_of_another():
    # `sync:on` reaches no handler of its own. Obsidian splits it at the
    # last colon, finds `on` among the options of `sync`, and runs that.
    assert GRAMMAR.resolve("sync:on") == ("sync", "on")


def test_refuses_a_parameter_the_command_does_not_take():
    with pytest.raises(GrammarError, match="no parameter 'property'"):
        GRAMMAR.check("property:read", params={"path": "a.md", "property": "tags"})


def test_refuses_a_renamed_parameter():
    with pytest.raises(GrammarError, match="no parameter 'new-name'"):
        GRAMMAR.check("rename", params={"path": "a.md", "new-name": "b"})


def test_refuses_a_flag_given_a_value():
    with pytest.raises(GrammarError, match="counts is a flag"):
        GRAMMAR.check("tags", params={"counts": "true"})


def test_refuses_a_parameter_given_as_a_flag():
    with pytest.raises(GrammarError, match="name takes <tag>"):
        GRAMMAR.check("tag", flags=["name"])


def test_refuses_a_value_outside_the_ones_the_command_lists():
    with pytest.raises(GrammarError, match=re.escape("takes format=json|tsv|csv")):
        GRAMMAR.check("tags", output_format="yaml")


def test_refuses_a_format_the_command_has_no_use_for():
    # `read` prints a file, and asking it for JSON does not make it JSON.
    with pytest.raises(GrammarError, match="no parameter 'format'"):
        GRAMMAR.check("read", params={"path": "a.md"}, output_format="json")


def test_refuses_a_required_parameter_left_out():
    with pytest.raises(GrammarError, match="needs query"):
        GRAMMAR.check("search")


def test_takes_a_format_named_on_its_own():
    # Obsidian reads a bare `json` as `format=json` for any command that
    # has a `format` parameter, so the check has to as well.
    GRAMMAR.check("tags", flags=["json"])


def test_still_refuses_a_bare_format_the_command_does_not_offer():
    with pytest.raises(GrammarError, match="no parameter 'json'"):
        GRAMMAR.check("read", params={"path": "a.md"}, flags=["json"])


def test_accepts_anything_where_the_command_prints_a_placeholder():
    # `<path>` stands for whatever the caller has, unlike `json|tsv|csv`.
    GRAMMAR.check("read", params={"path": "notes/A note, with a comma.md"})
