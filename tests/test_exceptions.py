from __future__ import annotations

import pickle

import pytest

from aiobsidian._exceptions import (
    APIConnectionError,
    APINotFoundError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BinaryNotFoundError,
    CLINotFoundError,
    CLIParseError,
    CLITimeoutError,
    CommandError,
)

CASES = [
    APIStatusError(500, "Internal error"),
    APIStatusError(400, "Bad request", 40001),
    APIConnectionError("GET", "https://127.0.0.1:27124/", "Connection refused"),
    APITimeoutError("GET", "https://127.0.0.1:27124/", "timed out"),
    AuthenticationError(401, "Unauthorized"),
    APINotFoundError(404, "Not found", 40401),
    BinaryNotFoundError("binary not found"),
    CommandError("read", 0, "", 'Error: File "a.md" not found.'),
    CLINotFoundError("read", 0, "", 'Error: File "a.md" not found.'),
    CLIParseError("tags", "plain text"),
    CLITimeoutError("read", 30.0),
]


@pytest.mark.parametrize("error", CASES, ids=lambda e: type(e).__name__)
def test_pickle_roundtrip(error):
    restored = pickle.loads(pickle.dumps(error))
    assert type(restored) is type(error)
    assert str(restored) == str(error)
    assert restored.__dict__ == error.__dict__
