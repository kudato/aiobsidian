from unittest.mock import DEFAULT, AsyncMock, patch

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


@pytest.fixture()
def cli():
    """An `ObsidianCLI` that answers instead of spawning anything.

    `_execute` is replaced, so a test says what the CLI printed and
    reads back what the command was asked. What it was asked is checked
    against the grammar of the app itself on the way past: the mock
    would answer a misspelt parameter as readily as a real one, and the
    real CLI would too — it ignores what it does not recognise. Every
    test that calls a resource method is therefore also a test that the
    command line it produces is one Obsidian accepts.

    Setting `side_effect` in a test replaces the check along with the
    answer, which is what a test raising from the CLI wants.
    """
    instance = ObsidianCLI("TestVault", binary="/usr/local/bin/obsidian")
    instance._execute = AsyncMock(side_effect=_check_grammar)
    return instance


def _check_grammar(command, *, params=None, flags=None, output_format=None, **_):
    """Check a command line, then let the mock answer as it was told.

    Args:
        command: CLI command name.
        params: Parameters passed as `key=value`.
        flags: Parameters passed as bare words.
        output_format: Value of the `format` parameter, if any.

    Returns:
        The sentinel that tells the mock to use its own `return_value`.

    Raises:
        GrammarError: If Obsidian would refuse the command line, or
            would accept it having ignored part of it.
    """
    GRAMMAR.check(command, params=params, flags=flags, output_format=output_format)
    return DEFAULT
