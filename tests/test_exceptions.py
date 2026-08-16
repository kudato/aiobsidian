from __future__ import annotations

import pickle

import pytest

from aiobsidian._exceptions import (
    APIConnectionError,
    APIError,
    APINotFoundError,
    APIProtocolError,
    APIRequestError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BinaryNotFoundError,
    CLIError,
    CLINotFoundError,
    CLIParseError,
    CLITimeoutError,
    CommandError,
    NotFoundError,
    ObsidianError,
)

CASES = [
    APIStatusError(500, "Internal error"),
    APIStatusError(400, "Bad request", 40001),
    APIConnectionError("GET", "https://127.0.0.1:27124/", "Connection refused"),
    APITimeoutError("GET", "https://127.0.0.1:27124/", "timed out"),
    APIProtocolError("GET", "https://127.0.0.1:27124/", "illegal status line"),
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


@pytest.mark.parametrize("error", CASES, ids=lambda e: type(e).__name__)
def test_every_error_is_an_obsidian_error(error):
    assert isinstance(error, ObsidianError)


class TestHierarchy:
    """The shape of the tree, asserted rather than assumed.

    Re-parenting a class keeps every other test green — the catch
    clauses in this project's own code and in its users' code are the
    only thing that notices, and they notice at runtime.
    """

    @pytest.mark.parametrize(
        "error",
        [error for error in CASES if isinstance(error, APIError)],
        ids=lambda e: type(e).__name__,
    )
    def test_api_error_is_the_rest_transport_root(self, error):
        assert not isinstance(error, CLIError)

    @pytest.mark.parametrize(
        "error",
        [error for error in CASES if isinstance(error, CLIError)],
        ids=lambda e: type(e).__name__,
    )
    def test_cli_error_is_the_cli_transport_root(self, error):
        assert not isinstance(error, APIError)

    def test_a_refused_request_is_not_a_status_error(self):
        # It has no status to carry, which is the whole reason the two
        # branches exist.
        error = APIConnectionError("GET", "https://127.0.0.1:27124/", "refused")
        assert isinstance(error, APIRequestError)
        assert not isinstance(error, APIStatusError)
        assert not hasattr(error, "status_code")

    @pytest.mark.parametrize(
        "error_class", [APIConnectionError, APITimeoutError, APIProtocolError]
    )
    def test_no_response_errors_share_a_base(self, error_class):
        assert issubclass(error_class, APIRequestError)
        assert issubclass(error_class, APIError)

    @pytest.mark.parametrize("error_class", [AuthenticationError, APINotFoundError])
    def test_status_errors_share_a_base(self, error_class):
        assert issubclass(error_class, APIStatusError)
        assert issubclass(error_class, APIError)

    def test_missing_resources_are_transport_neutral(self):
        assert issubclass(APINotFoundError, NotFoundError)
        assert issubclass(CLINotFoundError, NotFoundError)

    def test_the_two_not_found_errors_stay_unrelated(self):
        assert not issubclass(APINotFoundError, CLINotFoundError)
        assert not issubclass(CLINotFoundError, APINotFoundError)


class TestMessages:
    def test_a_connection_failure_suggests_the_usual_cause(self):
        error = APIConnectionError(
            "GET", "https://127.0.0.1:27124/vault/", "All connection attempts failed"
        )
        assert str(error) == (
            "GET https://127.0.0.1:27124/vault/ could not be reached: "
            "All connection attempts failed. Is Obsidian running with the "
            "Local REST API plugin enabled?"
        )

    def test_a_broken_exchange_does_not_blame_a_running_obsidian(self):
        error = APIProtocolError(
            "GET", "https://127.0.0.1:27124/vault/", "illegal status line"
        )
        assert str(error) == (
            "GET https://127.0.0.1:27124/vault/ did not complete: illegal status line"
        )
        assert "Obsidian running" not in str(error)

    def test_a_timeout_names_the_request(self):
        error = APITimeoutError(
            "PUT", "https://127.0.0.1:27124/vault/a.md", "timed out"
        )
        assert str(error) == (
            "PUT https://127.0.0.1:27124/vault/a.md timed out: timed out"
        )
