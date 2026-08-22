"""What the extractor makes of the app bundle it reads.

`tests/data/cli_grammar.json` is only worth checking against if it says
what Obsidian says, and nothing in CI can compare the two: the runner
has no Obsidian on it. What CI can do is check the reading itself, on
registrations written the way the bundle writes them — minified, with
descriptions holding the braces, quotes and commas that would end a
naive scan early.
"""

from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any

import pytest

from tools.extract_cli_grammar import (
    ExtractionError,
    extract_grammar,
    parse_options,
    read_asar,
    read_js_string,
    read_version,
    split_call_arguments,
)

# One registration as the bundle writes them: no whitespace, `!0` for
# `true`, and a description carrying the punctuation this has to survive.
BUNDLE = (
    'this.registerHandler("tags","List tags in the vault",'
    '{path:{value:"<path>",description:"File path, e.g. {a,b}"},'
    'counts:{description:"Include tag counts"},'
    'sort:{value:"count",description:"Sort by count (default: name)"},'
    'format:{value:"json|tsv|csv",description:"Output format"}},'
    "(function(t){return t.path}))"
)


def _asar(files: dict[str, bytes], *, unpacked: tuple[str, ...] = ()) -> bytes:
    """Pack files into an asar archive.

    Args:
        files: Contents by archive path. A path holding a `/` is packed
            as the archive packs one, a directory at a time.
        unpacked: Names to record as left outside the archive, the way
            the packer records a native module.

    Returns:
        The archive as Obsidian ships one: four lengths, a JSON header,
        then every file end to end.
    """
    header: dict[str, Any] = {"files": {}}
    body = b""
    for name, content in files.items():
        node = header
        *folders, leaf = name.split("/")
        for folder in folders:
            node = node["files"].setdefault(folder, {"files": {}})
        node["files"][leaf] = {"offset": str(len(body)), "size": len(content)}
        body += content
    for name in unpacked:
        header["files"][name] = {"size": 0, "unpacked": True}
    payload = json.dumps(header).encode()
    padding = -len(payload) % 4
    return (
        struct.pack(
            "<IIII", 4, 8 + len(payload) + padding, 4 + len(payload), len(payload)
        )
        + payload
        + b"\0" * padding
        + body
    )


def test_reads_a_string_that_holds_its_own_quote():
    assert read_js_string(r'"a \"quoted\" word"rest', 0) == ('a "quoted" word', 19)


def test_reads_a_single_quoted_string_holding_both_quotes():
    assert read_js_string(r"""'say "no", don\'t'rest""", 0) == (
        'say "no", don\'t',
        18,
    )


def test_refuses_a_string_it_would_read_wrong():
    with pytest.raises(ExtractionError, match="string literal"):
        read_js_string(r'"a \q escape"', 0)


def test_splits_arguments_around_a_comma_inside_a_string():
    assert split_call_arguments('"a,b",{c:1},d)', 0) == ['"a,b"', "{c:1}", "d"]


def test_reads_a_command_that_takes_nothing():
    assert parse_options("null") == {}


def test_refuses_options_that_are_not_written_out():
    # A registration passing a variable would be read as a command
    # taking nothing, which is a grammar that accepts everything.
    with pytest.raises(ExtractionError):
        parse_options("someVariable")


def test_reads_the_options_of_a_registration():
    assert extract_grammar(BUNDLE) == {
        "tags": {
            "path": {"value": "<path>", "required": False},
            "counts": {"required": False},
            "sort": {"value": "count", "required": False},
            "format": {"value": "json|tsv|csv", "required": False},
        }
    }


def test_reads_a_required_parameter():
    source = 'r.registerHandler("tag","",{name:{value:"<tag>",required:!0}},f)'
    assert extract_grammar(source)["tag"]["name"]["required"] is True


def test_reads_a_registration_made_by_a_plugin():
    source = 't.registerCliHandler("daily:path","Get daily note path",null,f)'
    assert extract_grammar(source) == {"daily:path": {}}


def test_skips_a_registration_whose_name_is_not_written_out():
    source = 'e.registerHandler(name,"",null,f);e.registerHandler("version","",null,f)'
    assert extract_grammar(source) == {"version": {}}


def test_refuses_a_command_registered_twice():
    with pytest.raises(ExtractionError, match="twice"):
        extract_grammar(BUNDLE + BUNDLE)


def test_refuses_a_bundle_that_registers_nothing():
    with pytest.raises(ExtractionError, match="no CLI handlers"):
        extract_grammar("console.log('hello')")


def test_does_not_read_a_description_that_quotes_a_key():
    # Read as a declaration, `value:` inside prose would say the
    # parameter takes anything where it takes one of a listed few, and
    # the grammar would then accept whatever it was checking.
    options = parse_options(
        '{format:{description:"one of value:\\"<any>\\", required:!0",'
        'value:"json|tsv"}}'
    )
    assert options == {"format": {"value": "json|tsv", "required": False}}


@pytest.mark.parametrize(
    "written",
    [
        '{format:{"value":"json|tsv","required":!0}}',
        '{format:{value : "json|tsv", required : !0}}',
    ],
    ids=["quoted keys", "spaced colons"],
)
def test_reads_a_parameter_however_its_keys_are_written(written):
    assert parse_options(written) == {"format": {"value": "json|tsv", "required": True}}


def test_refuses_a_value_that_is_not_written_out():
    with pytest.raises(ExtractionError, match="expected a string literal"):
        parse_options("{format:{value:FORMATS}}")


def test_refuses_a_required_it_cannot_read():
    # Read as `false`, a required parameter would stop being one, and the
    # grammar would pass a command line the CLI refuses.
    with pytest.raises(ExtractionError, match="boolean written as"):
        parse_options('{name:{value:"<tag>",required:e}}')


def test_reads_a_required_that_is_written_false():
    assert parse_options("{name:{required:!1}}") == {"name": {"required": False}}


def test_refuses_options_whose_parameter_is_not_described():
    # Seeking the next `{` would read the next parameter's description as
    # this one's, and drop a parameter with nothing said about it.
    with pytest.raises(ExtractionError, match="not described by an object literal"):
        parse_options('{path:null,name:{value:"<name>"}}')


def test_unpacks_an_archive(tmp_path):
    archive = tmp_path / "obsidian.asar"
    archive.write_bytes(_asar({"app.js": b"handlers", "package.json": b"{}"}))
    assert read_asar(archive) == {"app.js": b"handlers", "package.json": b"{}"}


def test_unpacks_an_archive_holding_folders(tmp_path):
    archive = tmp_path / "obsidian.asar"
    archive.write_bytes(_asar({"app.js": b"handlers", "lib/i18n/en.js": b"words"}))
    assert read_asar(archive) == {"app.js": b"handlers", "lib/i18n/en.js": b"words"}


def test_skips_a_file_left_outside_the_archive(tmp_path):
    # `app.asar` beside it carries native modules packed this way, so a
    # mistaken --asar should say what it found rather than crash.
    archive = tmp_path / "obsidian.asar"
    archive.write_bytes(_asar({"app.js": b"handlers"}, unpacked=("binding.node",)))
    assert read_asar(archive) == {"app.js": b"handlers"}


def test_reads_the_version_the_archive_declares():
    assert (
        read_version({"package.json": b'{"version": "1.13.7"}'}, Path("x")) == "1.13.7"
    )


@pytest.mark.parametrize("package", [b"{}", b"not json", b'{"version": 113}'], ids=repr)
def test_refuses_an_archive_that_names_no_version(package):
    with pytest.raises(ExtractionError, match="version"):
        read_version({"package.json": package}, Path("x"))


def test_refuses_a_file_that_is_not_an_archive(tmp_path):
    archive = tmp_path / "obsidian.asar"
    archive.write_bytes(b"not an asar archive at all")
    with pytest.raises(ExtractionError, match="no readable asar header"):
        read_asar(archive)


def test_refuses_a_file_too_short_to_hold_a_header(tmp_path):
    archive = tmp_path / "obsidian.asar"
    archive.write_bytes(b"\0")
    with pytest.raises(ExtractionError, match="too short"):
        read_asar(archive)
