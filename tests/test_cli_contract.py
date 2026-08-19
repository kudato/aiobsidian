"""What every CLI method owes the caller, method by method.

The tests beside this one each read one command's output and check what
the resource made of it. They say nothing about the methods nobody
thought to write a case for, and nothing at all about what happens when
the CLI answers with something no case anticipated. This says both, for
every public method of every CLI resource at once:

- the command line it builds is one Obsidian accepts — checked by the
  `cli` fixture against the grammar of the app itself, on every call
  made here as everywhere else;
- an empty answer produces the value named in the table below, rather
  than whatever falls out;
- an answer of a shape no command produces either raises `CLIParseError`
  or comes back as the type the method promises — never as another type,
  and never as some other exception. That is a floor rather than a
  contract for each method: a method returning `str` promises little,
  and one that reads a table can honestly find nothing in a line it
  does not recognise. What it rules out is the shape reaching the caller
  under a type that does not fit it, which is how three methods used to
  hand back a mapping where the signature said list;
- a failing command and a timeout reach the caller unchanged.

`CALLS` names every method, and a test here fails when one is added
without an entry, so the guarantees above cannot quietly stop covering
the surface they are about.
"""

from __future__ import annotations

import contextlib
import inspect
from dataclasses import dataclass, field
from functools import cached_property
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

import pytest

from aiobsidian._cli import ObsidianCLI
from aiobsidian._exceptions import CLIParseError, CLITimeoutError, CommandError


@dataclass(frozen=True, slots=True)
class Call:
    """One way to reach a resource method.

    Attributes:
        resource: Name of the resource on `ObsidianCLI`.
        method: Name of the method on that resource.
        args: Positional arguments to call it with.
        kwargs: Keyword arguments to call it with.
        empty: What the method answers when the CLI prints nothing, or
            the exception it raises instead.
        label: Distinguishes two ways of reaching the same method.
    """

    resource: str
    method: str
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    empty: Any = None
    label: str = ""

    def __str__(self) -> str:
        name = f"{self.resource}.{self.method}"
        return f"{name}[{self.label}]" if self.label else name

    async def __call__(self, cli: ObsidianCLI) -> Any:
        """Make the call.

        Args:
            cli: Client to call it on.

        Returns:
            Whatever the method returns.
        """
        resource = getattr(cli, self.resource)
        return await getattr(resource, self.method)(*self.args, **self.kwargs)


CALLS = (
    Call("aliases", "get", ("notes/setup.md",), empty=[]),
    Call("bases", "views", empty=[]),
    Call("bases", "create", ("bases/tasks.base",)),
    Call("bases", "query", ("bases/tasks.base",), empty=[]),
    Call("bases", "list", empty=[]),
    Call("bookmarks", "add", kwargs={"file": "notes/setup.md"}),
    Call("bookmarks", "list", empty=[]),
    Call("commands", "execute", ("app:go-back",)),
    Call("commands", "list", empty=[]),
    Call("daily", "read", empty=""),
    Call("daily", "path", empty=""),
    Call("daily", "open", empty=""),
    Call("daily", "append", ("Done.",)),
    Call("daily", "prepend", ("Done.",)),
    Call("dev", "devtools"),
    Call("dev", "eval", ("1 + 1",), empty=""),
    Call("dev", "console", empty=[]),
    Call("dev", "errors", empty=[]),
    Call("dev", "screenshot", ("shot.png",)),
    Call("dev", "dom", ("body",), empty=""),
    Call("dev", "css", ("body",), empty=""),
    Call("dev", "set_mobile", (True,), empty=CLIParseError),
    Call("dev", "is_attached", empty=CLIParseError),
    Call("dev", "set_debugger", (True,), empty=CLIParseError),
    Call("dev", "cdp", ("DOM.getDocument", "{}"), empty=""),
    Call("history", "versions", ("notes/setup.md",), empty=[]),
    Call("history", "open", ("notes/setup.md",)),
    Call("history", "diff", ("notes/setup.md",), empty=""),
    Call("history", "read", ("notes/setup.md",), empty=""),
    Call("history", "restore", ("notes/setup.md",), {"version": 2}),
    Call("history", "list", empty=[]),
    Call("hotkeys", "get", ("app:go-back",), empty=[]),
    Call("hotkeys", "list", empty=[]),
    Call("links", "outgoing", ("notes/setup.md",), empty=[]),
    Call("links", "incoming", ("notes/setup.md",), empty=[]),
    Call("links", "unresolved", empty=[]),
    Call("links", "orphans", empty=[]),
    Call("links", "deadends", empty=[]),
    Call("outline", "get", ("notes/setup.md",), empty=[]),
    Call("plugins", "info", ("dataview",), empty=CLIParseError),
    Call("plugins", "is_restricted", empty=CLIParseError),
    Call("plugins", "set_restricted", (True,), empty=CLIParseError),
    Call("plugins", "enabled", empty=[]),
    Call("plugins", "enable", ("dataview",)),
    Call("plugins", "disable", ("dataview",)),
    Call("plugins", "install", ("dataview",)),
    Call("plugins", "uninstall", ("dataview",)),
    Call("plugins", "reload", ("dataview",)),
    Call("plugins", "list", empty=[]),
    Call("properties", "list", ("notes/setup.md",), empty={}),
    Call("properties", "read", ("notes/setup.md", "tags"), empty=""),
    Call("properties", "set", ("notes/setup.md", "tags", "cli")),
    Call("properties", "remove", ("notes/setup.md", "tags")),
    Call("publish", "open", empty=""),
    Call("publish", "site", empty=CLIParseError),
    Call("publish", "status", empty=[]),
    Call("publish", "add", ("notes/setup.md",), empty=""),
    Call("publish", "add", kwargs={"changed": True}, empty="", label="changed"),
    Call("publish", "remove", ("notes/setup.md",)),
    Call("publish", "list", empty=[]),
    Call("random", "open"),
    Call("random", "read", empty=""),
    Call("search", "open", ("cli",)),
    Call("search", "query", ("cli",), empty=[]),
    Call("search", "context", ("cli",), empty=[]),
    Call("snippets", "enabled", empty=[]),
    Call("snippets", "enable", ("theme.css",)),
    Call("snippets", "disable", ("theme.css",)),
    Call("snippets", "list", empty=[]),
    Call("sync", "is_paused", empty=CLIParseError),
    Call("sync", "set_paused", (True,), empty=CLIParseError),
    Call("sync", "open"),
    Call("sync", "status", empty=CLIParseError),
    Call("sync", "history", ("notes/setup.md",), empty=[]),
    Call("sync", "read", ("notes/setup.md",), {"version": 2}, empty=""),
    Call("sync", "restore", ("notes/setup.md",), {"version": 2}),
    Call("sync", "deleted", empty=[]),
    Call("system", "version", empty=""),
    Call("system", "help", empty=""),
    Call("system", "reload"),
    Call("system", "restart"),
    Call("system", "vaults", empty=[]),
    Call("tabs", "open", kwargs={"file": "notes/setup.md"}),
    Call("tabs", "recents", empty=[]),
    Call("tabs", "recent_count", empty=CLIParseError),
    Call("tabs", "list", empty=[]),
    Call("tags", "get", ("python",), empty=[]),
    Call("tags", "list", empty=[]),
    Call("tasks", "list", empty=[]),
    Call("tasks", "toggle", ("notes/setup.md", 5)),
    Call("tasks", "complete", ("notes/setup.md", 5)),
    Call("tasks", "reopen", ("notes/setup.md", 5)),
    Call("templates", "read", ("Daily",), empty=""),
    Call("templates", "insert", ("Daily",)),
    Call("templates", "list", empty=[]),
    Call("themes", "current", empty=""),
    Call("themes", "set", ("Minimal",)),
    Call("themes", "install", ("Minimal",)),
    Call("themes", "uninstall", ("Minimal",)),
    Call("themes", "list", empty=[]),
    Call("vault", "open", ("notes/setup.md",)),
    Call("vault", "read", ("notes/setup.md",), empty=""),
    Call("vault", "write", ("notes/setup.md", "Body.")),
    Call("vault", "create_unique", empty=""),
    Call("vault", "append", ("notes/setup.md", "Body.")),
    Call("vault", "prepend", ("notes/setup.md", "Body.")),
    Call("vault", "move", ("notes/setup.md", "archive/setup.md")),
    Call("vault", "rename", ("notes/setup.md", "install")),
    Call("vault", "delete", ("notes/setup.md",)),
    Call("vault", "info", empty=CLIParseError),
    Call("vault", "file_info", ("notes/setup.md",), empty=CLIParseError),
    Call("vault", "resolve", ("setup",), empty=CLIParseError),
    Call("vault", "folder_info", ("notes",), empty=CLIParseError),
    Call("vault", "folders", empty=[]),
    Call("vault", "folder_count", empty=CLIParseError),
    Call("vault", "wordcount", ("notes/setup.md",), empty=CLIParseError),
    Call("vault", "list", empty=[]),
    Call("vault", "file_count", empty=CLIParseError),
    Call("web", "open", ("https://obsidian.md",)),
    Call("workspaces", "current", empty=""),
    Call("workspaces", "save", ("Writing",)),
    Call("workspaces", "load", ("Writing",)),
    Call("workspaces", "delete", ("Writing",)),
    Call("workspaces", "list", empty=[]),
)

UNEXPECTED_OUTPUT = (
    "   \n",
    "{",
    "[1, 2]",
    "null",
    '{"tag": "#python"}',
    "Obsidian is starting up, please wait.",
    "one\ttwo\tthree\tfour\tfive",
)
"""Answers no command documents: blank space, JSON cut short, JSON of
the wrong shape, prose where a table was expected, and a row with more
columns than any table has."""


def _resource_names() -> list[str]:
    """Name every CLI resource `ObsidianCLI` exposes.

    Returns:
        The attribute names, which is how `CALLS` addresses them.
    """
    return [
        name
        for name, member in vars(ObsidianCLI).items()
        if not name.startswith("_") and isinstance(member, cached_property)
    ]


def _public_methods(resource: object) -> list[str]:
    """Name every method a resource offers its callers.

    Args:
        resource: Resource instance to look at.

    Returns:
        The public method names it defines.
    """
    return [
        name
        for name, member in inspect.getmembers(type(resource), inspect.isfunction)
        if not name.startswith("_")
    ]


def _matches(value: Any, annotation: Any) -> bool:
    """Check a value against a return annotation.

    Only as deep as the annotation goes, which for these methods is a
    container of models or of strings. `Any` accepts anything, which is
    the point of writing it.

    Args:
        value: Value the method returned.
        annotation: Its declared return type.

    Returns:
        Whether the value is of that type.
    """
    if annotation is Any:
        return True
    if annotation is None or annotation is type(None):
        return value is None
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        return any(_matches(value, arm) for arm in get_args(annotation))
    if origin is None:
        return isinstance(value, annotation)
    if not isinstance(value, origin):
        return False
    arguments = get_args(annotation)
    if origin is list:
        return all(_matches(item, arguments[0]) for item in value)
    if origin is dict:
        return all(
            _matches(key, arguments[0]) and _matches(item, arguments[1])
            for key, item in value.items()
        )
    return True


def _returns(cli: ObsidianCLI, call: Call) -> Any:
    """Resolve what a method says it returns.

    Args:
        cli: Client the method belongs to.
        call: The call being made.

    Returns:
        The return annotation, resolved against the module it was
        written in.
    """
    method = getattr(type(getattr(cli, call.resource)), call.method)
    return get_type_hints(method).get("return")


def test_every_public_method_is_called():
    cli = ObsidianCLI("TestVault", binary="/usr/local/bin/obsidian")
    called = {(call.resource, call.method) for call in CALLS}
    missing = sorted(
        f"{resource}.{method}"
        for resource in _resource_names()
        for method in _public_methods(getattr(cli, resource))
        if (resource, method) not in called
    )
    assert not missing, (
        f"add {', '.join(missing)} to CALLS: until then nothing checks the "
        f"command line they build, nor what they make of an answer they do "
        f"not expect"
    )


@pytest.mark.parametrize("call", CALLS, ids=str)
async def test_builds_a_command_line_obsidian_accepts(cli, call):
    # The checking is the fixture's; this is what makes every method
    # pass through it, whether or not a test elsewhere calls it.
    cli._execute.return_value = ""
    with contextlib.suppress(CLIParseError):
        await call(cli)
    assert cli._execute.await_count >= 1, f"{call} never reached the CLI"


@pytest.mark.parametrize("call", CALLS, ids=str)
async def test_empty_output(cli, call):
    cli._execute.return_value = ""
    if call.empty is CLIParseError:
        with pytest.raises(CLIParseError):
            await call(cli)
        return
    assert await call(cli) == call.empty


@pytest.mark.parametrize("output", UNEXPECTED_OUTPUT, ids=repr)
@pytest.mark.parametrize("call", CALLS, ids=str)
async def test_unexpected_output(cli, call, output):
    cli._execute.return_value = output
    try:
        result = await call(cli)
    except CLIParseError:
        return
    annotation = _returns(cli, call)
    assert _matches(result, annotation), (
        f"{call} answered {result!r} for output {output!r}, which is not "
        f"the {annotation} it promises"
    )


@pytest.mark.parametrize("call", CALLS, ids=str)
async def test_command_error_reaches_the_caller(cli, call):
    failure = CommandError("read", 1, "", "Error: File not found.")
    cli._execute.side_effect = failure
    with pytest.raises(CommandError) as raised:
        await call(cli)
    assert raised.value is failure


@pytest.mark.parametrize("call", CALLS, ids=str)
async def test_timeout_reaches_the_caller(cli, call):
    failure = CLITimeoutError("read", 30.0)
    cli._execute.side_effect = failure
    with pytest.raises(CLITimeoutError) as raised:
        await call(cli)
    assert raised.value is failure
