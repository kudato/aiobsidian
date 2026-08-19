"""Check a command line against the grammar Obsidian actually ships.

`tests/data/cli_grammar.json` is read out of an installed `obsidian.asar`
by `tools/extract_cli_grammar.py`: every command the app registers, with
the parameters and flags it declares. This decides whether a command line
built by this library is one that app would accept.

Two pieces of Obsidian read a command line, and this follows both.

The main process takes it off the socket first. It reads `vault=` off the
front — only off the front — and drops it before passing the rest on. An
argument that spells `vault=` anywhere else is left where it is, and the
vault becomes whichever one holds the working directory, or failing that
whichever window was last in front.

`handleCli` in the app bundle takes what is left:

- the first argument names the command, the rest are `key=value` pairs,
  and a bare word is the key set to `"true"`;
- a command it does not know is split at its last colon, and if the part
  before it is a command whose options carry the part after it, that
  option is set instead — which is how `sync:on` reaches `sync`;
- a command that declares `format` also answers to that parameter's
  values by name, so `json` means `format=json`;
- a parameter marked required must be there, or the command fails before
  the handler runs.

Two of the checks here are deliberately stricter than the dispatcher,
because the dispatcher's leniency is the whole problem. It does not
reject a parameter it has never heard of: it hands the handler everything
it was given, and the handler reads the keys it knows. Nor does it check
a value against the ones the help text lists, or mind a flag arriving
with a value — `counts=false` enables counts as readily as `counts` does,
since the handler only asks whether the key is there. None of that is an
error at the CLI. It is silence: the command succeeds having ignored what
it was asked. So each is an error here.

The table is what the app can register rather than what it has: a plugin
registers its commands as it loads, so `sync:read` is in there whether or
not that vault has Sync. Whether a command is answered at runtime is the
resource docstrings' business, not this one's.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_GRAMMAR_PATH = Path(__file__).parent / "data" / "cli_grammar.json"

_VAULT_PREFIX = "vault="


class GrammarError(AssertionError):
    """Raised when Obsidian would not accept a command line.

    An `AssertionError` because that is what it means in a test: the
    library sent something the app does not take.
    """


@dataclass(frozen=True, slots=True)
class Option:
    """One parameter or flag of a command.

    Attributes:
        value: Placeholder the help text prints after the `=`, or `None`
            for a flag that is named on its own.
        required: Whether the command fails when it is left out.
    """

    value: str | None
    required: bool

    @property
    def choices(self) -> tuple[str, ...] | None:
        """The values this option accepts, when it accepts a fixed set.

        A placeholder such as `<name>` stands for anything; alternatives
        such as `json|tsv|csv` stand for themselves. Order is kept: the
        dispatcher reads them in the order they are declared, and takes
        the first it finds among the arguments.

        Returns:
            The accepted values, or `None` when anything goes.
        """
        if self.value is None or "<" in self.value:
            return None
        return tuple(self.value.split("|"))


@dataclass(frozen=True, slots=True)
class Grammar:
    """The commands one release of Obsidian registers.

    Attributes:
        obsidian: Version of the app the grammar was read from.
        commands: Options of every command, by command name.
    """

    obsidian: str
    commands: dict[str, dict[str, Option]]

    @classmethod
    def load(cls, path: Path = _GRAMMAR_PATH) -> Grammar:
        """Read a grammar written by `tools/extract_cli_grammar.py`.

        Args:
            path: File to read.

        Returns:
            The grammar it holds.
        """
        raw: dict[str, Any] = json.loads(path.read_text())
        return cls(
            obsidian=raw["obsidian"],
            commands={
                command: {
                    name: Option(option.get("value"), option["required"])
                    for name, option in options.items()
                }
                for command, options in raw["commands"].items()
            },
        )

    def resolve(self, command: str) -> tuple[str, str | None]:
        """Work out which handler a command name reaches.

        Args:
            command: Command name as the library spells it.

        Returns:
            The handler that runs and the option the name set on the way,
            if the name reached it by being split at its last colon.

        Raises:
            GrammarError: If no handler answers to that name.
        """
        if command in self.commands:
            return command, None
        prefix, colon, suffix = command.rpartition(":")
        if colon and suffix in self.commands.get(prefix, {}):
            return prefix, suffix
        raise GrammarError(
            f"Obsidian {self.obsidian} has no command {command!r}"
            f"{self._suggest(command)}"
        )

    def _suggest(self, command: str) -> str:
        """Name the commands a misspelt one might have meant.

        Args:
            command: Command name that reached no handler.

        Returns:
            A sentence naming the near misses, or nothing when there are
            none.
        """
        stem = command.partition(":")[0]
        near = sorted(
            name
            for name in self.commands
            if not name.startswith("__")
            and (name.startswith(stem) or stem.startswith(name.partition(":")[0]))
        )
        return f"; it registers {', '.join(near)}" if near else ""

    def check_argv(self, argv: list[str]) -> None:
        """Check a whole command line, from the socket in.

        The arguments as the app receives them, which is what the library
        spawns without the binary. Where `vault=` sits decides whether the
        command reaches the vault it names, so it is read here and not
        taken on trust.

        Args:
            argv: Arguments the command was spawned with, binary aside.

        Raises:
            GrammarError: If Obsidian would refuse the command line, or
                would accept it having quietly ignored part of it.
        """
        rest = list(argv)
        if rest and rest[0].startswith(_VAULT_PREFIX):
            rest.pop(0)
        elif any(argument.startswith(_VAULT_PREFIX) for argument in rest):
            raise GrammarError(
                "vault= is read off the front of the command line and "
                "nowhere else; anywhere later it reaches the command as a "
                "parameter, and the vault is whichever one the working "
                f"directory sits in: {' '.join(argv)}"
            )
        if not rest:
            raise GrammarError("a command line names no command")

        params: dict[str, str] = {}
        flags: list[str] = []
        for argument in rest[1:]:
            name, found, value = argument.partition("=")
            if found:
                params[name] = value
            else:
                flags.append(name)
        self.check(rest[0], params=params, flags=flags)

    def check(
        self,
        command: str,
        *,
        params: dict[str, str] | None = None,
        flags: list[str] | None = None,
        output_format: str | None = None,
    ) -> None:
        """Check a call the way Obsidian's dispatcher would.

        Args:
            command: Command name.
            params: Parameters passed as `key=value`.
            flags: Parameters passed as bare words.
            output_format: Value of the `format` parameter, if any.

        Raises:
            GrammarError: If Obsidian would refuse the call, or would
                accept it having quietly ignored part of it.
        """
        handler, implied = self.resolve(command)
        options = self.commands[handler]

        given: dict[str, str | None] = {} if implied is None else {implied: None}
        for name in flags or ():
            given[name] = None
        for name, value in (params or {}).items():
            given[name] = value
        if output_format is not None:
            given["format"] = output_format

        self._apply_format_shorthand(options, given)

        for name, value in given.items():
            self._check_option(command, options, name, value)

        missing = sorted(
            name
            for name, option in options.items()
            if option.required and name not in given
        )
        if missing:
            raise GrammarError(
                f"{command} needs {', '.join(missing)}, and none was given"
            )

    @staticmethod
    def _apply_format_shorthand(
        options: dict[str, Option], given: dict[str, str | None]
    ) -> None:
        """Read `json` as `format=json`, as the dispatcher does.

        A command that declares `format` answers to that parameter's
        values by their own names. The dispatcher walks them in the
        order they are declared and takes the first that is there with
        anything to say: a bare word, which it reads as `"true"`, or a
        value of its own, which it then throws away in favour of the
        name. Only an empty value is passed over. The `--json` spelling
        it also accepts is not modelled, since nothing here sends one.

        Args:
            options: Options of the command being checked.
            given: What the call passes, rewritten in place.
        """
        choices = options["format"].choices if "format" in options else None
        if choices is None or "format" in given:
            return
        for choice in choices:
            if choice in given and given[choice] != "":
                del given[choice]
                given["format"] = choice
                return

    @staticmethod
    def _check_option(
        command: str,
        options: dict[str, Option],
        name: str,
        value: str | None,
    ) -> None:
        """Check one parameter of a call.

        Args:
            command: Command name, for the message.
            options: Options of the command being checked.
            name: Name of the parameter as the library spells it.
            value: Its value, or `None` when it is passed as a bare word.

        Raises:
            GrammarError: If the command does not declare the parameter,
                or declares it the other way round, or does not accept
                that value.
        """
        option = options.get(name)
        if option is None:
            declared = ", ".join(sorted(options)) or "nothing"
            raise GrammarError(
                f"{command} has no parameter {name!r}, so Obsidian would "
                f"ignore it and answer as though it had not been asked; "
                f"it takes {declared}"
            )
        if option.value is None and value is not None:
            raise GrammarError(
                f"{name} is a flag of {command}: the handler asks whether it "
                f"is there and not what it says, so {name}={value!r} turns it "
                f"on whatever the value says"
            )
        if option.value is not None and value is None:
            raise GrammarError(
                f"{name} takes {option.value} on {command}, and passing it "
                f"as a bare word sets it to 'true'"
            )
        choices = option.choices
        if choices is not None and value is not None and value not in choices:
            raise GrammarError(f"{command} takes {name}={option.value}, not {value!r}")
