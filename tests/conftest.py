from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from aiobsidian._cli import ObsidianCLI
from aiobsidian._client import ObsidianClient

from .grammar import Grammar

GRAMMAR = Grammar.load()


@pytest.fixture(autouse=True)
def guard_killpg(request):
    """Keep os.killpg away from process groups the tests do not own.

    A mocked process answers `.pid` with a MagicMock, and MagicMock
    coerces to 1 through `__index__`, so an unguarded `_kill` would ask
    the OS to SIGKILL process group 1. A desktop refuses that; a
    container running as root would not.

    Autouse across the whole suite, not one file: any test that patches
    `asyncio.create_subprocess_exec` can reach `_kill`.
    """
    if "real_processes" in request.keywords:
        yield None
        return
    with patch("aiobsidian._cli.os.killpg") as killpg:
        yield killpg


@pytest.fixture()
def mock_api():
    with respx.mock(base_url="https://127.0.0.1:27124") as api:
        yield api


@pytest.fixture()
async def client(mock_api):
    # No Authorization header here on purpose: the client must install it
    # itself, whoever built the transport.
    http = httpx.AsyncClient(base_url="https://127.0.0.1:27124")
    async with ObsidianClient("test-key", http_client=http) as c:
        yield c


class CheckedExecute(AsyncMock):
    """An `_execute` that checks the command line before answering.

    The mock stands in for the spawn, not for the command line: the
    arguments still go through `_build_argv`, and what comes out is
    checked against the grammar of the app itself. Both halves matter.
    A mock answers a misspelt parameter as readily as a real one, and so
    does the CLI — it ignores what it does not recognise. And where an
    argument sits in the line decides what it means, which is a thing
    only the built line can be asked.

    Checking here rather than through `side_effect` keeps the check
    whatever a test does with the answer: `side_effect` is how a test
    raises from the CLI or answers a series of commands, and it would
    otherwise take the check away with it.

    Attributes:
        cli: The client whose command lines these are.
    """

    def __call__(self, /, *args, **kwargs):
        argv = self.cli._build_argv(
            *args, **{name: v for name, v in kwargs.items() if name != "timeout"}
        )
        GRAMMAR.check_argv(argv[1:])
        return super().__call__(*args, **kwargs)


@pytest.fixture()
def cli():
    """An `ObsidianCLI` that answers instead of spawning anything.

    `_execute` is replaced, so a test says what the CLI printed and
    reads back what the command was asked. Every test that calls a
    resource method is therefore also a test that the command line it
    produces is one Obsidian accepts — see `CheckedExecute`.
    """
    instance = ObsidianCLI("TestVault", binary="/usr/local/bin/obsidian")
    instance._execute = CheckedExecute()
    instance._execute.cli = instance
    return instance
