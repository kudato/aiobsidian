"""Read the Obsidian CLI grammar out of a shipped `obsidian.asar`.

Every command name, parameter and flag this library sends was read by
hand from the command handlers inside the desktop app. This reads them
back mechanically, so the table the tests check against is the app's own
and not a transcription of it.

The handlers register themselves as
`registerHandler(name, description, options, handler)` — plugins call it
as `registerCliHandler` — and `options` is the object `obsidian help`
renders: a key per parameter, carrying `value` when the parameter takes
one and `required` when it must be given. That object is the grammar.

Usage:

```bash
uv run python tools/extract_cli_grammar.py > tests/data/cli_grammar.json
```

Pass `--asar` to read an app installed somewhere this does not look.

The bundle is transpiled to ES5, so the registrations hold nothing but
object and string literals: no template literals, no regular expressions,
no shorthand and no spread. This reads them on that assumption and
refuses anything else rather than guessing, because a grammar guessed
wrong is worse than none — the tests would check against it and agree.
"""

from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Any

_ASAR_CANDIDATES = (
    "/Applications/Obsidian.app/Contents/Resources/obsidian.asar",
    "/opt/Obsidian/resources/obsidian.asar",
    "/usr/lib/obsidian/resources/obsidian.asar",
    R"C:\Program Files\Obsidian\resources\obsidian.asar",
)

_REGISTRATION = re.compile(r"\.register(?:Cli)?Handler\(")
_VALUE = re.compile(r"""\bvalue:\s*("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')""")
_REQUIRED = re.compile(r"\brequired:\s*(?:!0|true)\b")


class ExtractionError(Exception):
    """Raised when the app does not hold what this expects."""


def read_asar(path: Path) -> dict[str, bytes]:
    """Unpack an asar archive into its files.

    The format is a chromium pickle of four little-endian lengths, a JSON
    header describing the tree, and then every file end to end. The
    header names each file's offset into that region and its size.

    Args:
        path: Path to the archive.

    Returns:
        The contents of every file in the archive, by archive path. A
        file the packer left outside the archive is named and skipped:
        `obsidian.asar` has none, and its neighbour `app.asar` does.

    Raises:
        ExtractionError: If the archive cannot be read as an asar.
    """
    blob = path.read_bytes()
    if len(blob) < 16:
        raise ExtractionError(f"{path} is too short to be an asar archive")
    _, header_size, _, json_length = struct.unpack("<IIII", blob[:16])
    try:
        header = json.loads(blob[16 : 16 + json_length].decode())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"{path} has no readable asar header") from exc
    base = 8 + header_size

    files: dict[str, bytes] = {}

    def walk(node: dict[str, Any], prefix: str) -> None:
        for name, entry in node.get("files", {}).items():
            if "files" in entry:
                walk(entry, f"{prefix}{name}/")
                continue
            if "offset" not in entry:
                print(f"skipping unpacked {prefix}{name}", file=sys.stderr)
                continue
            offset = base + int(entry["offset"])
            files[f"{prefix}{name}"] = blob[offset : offset + int(entry["size"])]

    walk(header, "")
    return files


def read_js_string(source: str, start: int) -> tuple[str, int]:
    """Read the JavaScript string literal beginning at `start`.

    The value is rewritten as a JSON string on the way, which is a
    translation rather than a copy: a literal written with single quotes
    may hold a bare `"` that JSON needs escaped, and an escaped `'` that
    JSON has no escape for.

    Args:
        source: Text to read from.
        start: Index of the opening quote.

    Returns:
        The literal's value and the index just past its closing quote.

    Raises:
        ExtractionError: If the literal holds an escape JSON does not
            share, which would be read wrong rather than not at all.
    """
    quote = source[start]
    index = start + 1
    chunks: list[str] = []
    while source[index] != quote:
        character = source[index]
        if character == "\\":
            pair = source[index : index + 2]
            chunks.append("'" if pair == "\\'" else pair)
            index += 2
            continue
        chunks.append('\\"' if character == '"' else character)
        index += 1
    try:
        value: str = json.loads('"' + "".join(chunks) + '"')
    except json.JSONDecodeError as exc:
        raise ExtractionError(
            f"cannot read the string literal at {start}: {source[start : index + 1]}"
        ) from exc
    return value, index + 1


def _scan(source: str, start: int, stop: str) -> int:
    """Find the delimiter closing the group that begins at `start`.

    Skips over nested groups and over string literals, so a bracket or a
    comma inside a description does not end anything.

    Args:
        source: Text to scan.
        start: Index just past the opening delimiter.
        stop: Delimiters that end the scan at nesting depth zero.

    Returns:
        Index of the delimiter that ended the scan.
    """
    depth = 0
    index = start
    while True:
        char = source[index]
        if char in "\"'`":
            _, index = read_js_string(source, index)
            continue
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0 and char in stop:
                return index
            depth -= 1
        elif char in stop and depth == 0:
            return index
        index += 1


def split_call_arguments(source: str, start: int) -> list[str]:
    """Split the arguments of the call whose `(` precedes `start`.

    Args:
        source: Text holding the call.
        start: Index just past the opening parenthesis.

    Returns:
        The arguments as written, in order.
    """
    arguments: list[str] = []
    index = start
    while True:
        end = _scan(source, index, ",)")
        arguments.append(source[index:end])
        if source[end] == ")":
            return arguments
        index = end + 1


def _skip_space(source: str, index: int) -> int:
    """Move past whatever blank space follows.

    Args:
        source: Text to scan.
        index: Where to start.

    Returns:
        Index of the next character that is not blank space.
    """
    while index < len(source) and source[index] in " \t\r\n":
        index += 1
    return index


def parse_options(source: str) -> dict[str, dict[str, Any]]:
    """Parse a handler's options object into the grammar of one command.

    Args:
        source: The object literal as written, or `null` for a command
            that takes nothing.

    Returns:
        A description per parameter: `value` when it takes one, spelt as
        the help text spells it, and `required` for one that must be
        given.

    Raises:
        ExtractionError: If the argument is neither an object literal nor
            `null`, or if a parameter is described by anything but an
            object literal of its own. Seeking the next `{` past such a
            parameter would read the following one's description as its
            own and drop a parameter without saying so.
    """
    text = source.strip()
    if text == "null":
        return {}
    if not text.startswith("{"):
        raise ExtractionError(f"handler options are not an object literal: {text[:60]}")

    options: dict[str, dict[str, Any]] = {}
    index = 1
    while index < len(text):
        char = text[index]
        if char in " \t\n,":
            index += 1
            continue
        if char == "}":
            break
        if char in "\"'":
            key, index = read_js_string(text, index)
        else:
            colon = text.find(":", index)
            if colon == -1:
                raise ExtractionError(f"a parameter without a colon: {text[index:60]}")
            key, index = text[index:colon].strip(), colon
        index = _skip_space(text, index)
        if text[index : index + 1] != ":":
            raise ExtractionError(f"parameter {key!r} names no description")
        index = _skip_space(text, index + 1)
        if text[index : index + 1] != "{":
            raise ExtractionError(
                f"parameter {key!r} is not described by an object literal: "
                f"{text[index : index + 60]}"
            )
        end = _scan(text, index + 1, "}")
        body = text[index + 1 : end]
        index = end + 1

        option: dict[str, Any] = {}
        value = _VALUE.search(body)
        if value is not None:
            option["value"] = read_js_string(value.group(1), 0)[0]
        option["required"] = _REQUIRED.search(body) is not None
        options[key] = option
    return options


def extract_grammar(app_js: str) -> dict[str, dict[str, dict[str, Any]]]:
    """Collect every CLI command the app registers.

    Args:
        app_js: Source of the app bundle.

    Returns:
        The options of every command, by command name.

    Raises:
        ExtractionError: If a command is registered twice, which would
            make one of the two the grammar and the other a lie.
    """
    commands: dict[str, dict[str, dict[str, Any]]] = {}
    for match in _REGISTRATION.finditer(app_js):
        arguments = split_call_arguments(app_js, match.end())
        if len(arguments) < 3:
            continue
        name_source = arguments[0].strip()
        if not name_source.startswith(("'", '"')):
            # A name held in a variable is a registration this cannot
            # read; the app has none today.
            continue
        name = read_js_string(name_source, 0)[0]
        if name in commands:
            raise ExtractionError(f"command {name!r} is registered twice")
        commands[name] = parse_options(arguments[2])
    if not commands:
        raise ExtractionError("no CLI handlers found in the app bundle")
    return commands


def find_asar(explicit: str | None) -> Path:
    """Locate the archive to read.

    Args:
        explicit: Path given on the command line, if any.

    Returns:
        Path to an existing archive.

    Raises:
        ExtractionError: If nothing is there to read.
    """
    if explicit is not None:
        path = Path(explicit)
        if not path.is_file():
            raise ExtractionError(f"{path} does not exist")
        return path
    for candidate in _ASAR_CANDIDATES:
        path = Path(candidate)
        if path.is_file():
            return path
    raise ExtractionError(
        "no obsidian.asar found; pass --asar with the path to an installed app"
    )


def read_version(files: dict[str, bytes], path: Path) -> str:
    """Read which Obsidian an archive holds.

    The grammar is only good for the release it was read from, so the
    table carries the version and this refuses an archive that cannot
    name one.

    Args:
        files: Contents of the archive.
        path: Where it came from, for the message.

    Returns:
        The version the archive declares.

    Raises:
        ExtractionError: If the archive names no version.
    """
    try:
        version = json.loads(files["package.json"].decode())["version"]
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExtractionError(f"{path} names no version in its package.json") from exc
    if not isinstance(version, str):
        raise ExtractionError(f"{path} names a version that is not a string")
    return version


def main() -> int:
    """Write the grammar of an installed Obsidian to standard output.

    Returns:
        Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asar", help="path to obsidian.asar")
    arguments = parser.parse_args()

    try:
        path = find_asar(arguments.asar)
        files = read_asar(path)
        version = read_version(files, path)
        if "app.js" not in files:
            raise ExtractionError(f"{path} holds no app.js")
        commands = extract_grammar(files["app.js"].decode(errors="replace"))
    except ExtractionError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"read {len(commands)} commands from Obsidian {version}", file=sys.stderr)
    json.dump(
        {"obsidian": version, "commands": commands},
        sys.stdout,
        indent=2,
        sort_keys=True,
    )
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
