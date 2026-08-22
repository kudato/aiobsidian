"""The wire contract has to hold together before either side is written against it.

``protocol/methods.json`` is what the plugin is tested against, and what this library
will be tested against once the socket transport lands, so a contradiction inside it is
a contradiction neither side can catch. These tests read it as data and check the things
a reviewer would otherwise have to check by eye: that every method's errors exist, that
every result names a shape that exists, that no shape refers to a shape that does not,
and that the file says the same thing twice nowhere.

What they cannot check is whether the file describes the plugin truthfully. That is the
plugin's own contract test, and it is why the claims in here are about this file only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

CONTRACT = Path(__file__).resolve().parent.parent / "protocol" / "methods.json"

#: A type is a union of parts; each part is a shape, a primitive, a literal, or a list.
_LIST = re.compile(r"\[\]$")
_LITERAL = re.compile(r'^"[^"]*"$')
_PRIMITIVES = frozenset(
    {"string", "integer", "number", "boolean", "object", "null", "any"}
)

#: Every class an error code may map to. Two are the standard library's, because
#: `invalidParams` is a caller's mistake and `cancelled` is what withdrawal already
#: means in asyncio; inventing a name for either would only make callers learn it.
#:
#: The rest are the library's own and most of them are not written yet — this roster is
#: the list the transport will be held to when it lands, not a claim that it already is.
#: The day it does, this becomes an import and stops being a list of strings.
_EXCEPTIONS = frozenset(
    {
        "AlreadyExistsError",
        "CancelledError",
        "ConflictError",
        "ForbiddenError",
        "NotFoundError",
        "OperationError",
        "ProtocolError",
        "TooManyRequestsError",
        "UnavailableError",
        "UnsupportedProtocolError",
        "UntrustedPeerError",
        "ValueError",
    }
)


@pytest.fixture(scope="module")
def contract() -> dict[str, Any]:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _parts(declared: str) -> list[str]:
    """Split a declared type into the alternatives it is made of."""
    return [part.strip() for part in declared.split("|")]


def _named_shapes(declared: str) -> list[str]:
    """The shape names a declared type refers to, list and union syntax removed."""
    names = []
    for part in _parts(declared):
        bare = _LIST.sub("", part)
        if bare in _PRIMITIVES or _LITERAL.match(bare):
            continue
        names.append(bare)
    return names


def test_protocol_version_is_major_minor(contract: dict[str, Any]) -> None:
    version = contract["protocol"]
    assert isinstance(version["major"], int)
    assert isinstance(version["minor"], int)
    assert version["major"] >= 1, "a major of zero would mean nothing is promised"


def test_every_error_code_is_unique(contract: dict[str, Any]) -> None:
    codes = [error["code"] for error in contract["errors"].values()]
    assert len(codes) == len(set(codes))


def test_our_error_codes_stay_out_of_the_reserved_range(
    contract: dict[str, Any],
) -> None:
    for name, error in contract["errors"].items():
        code = error["code"]
        if code > 0:
            assert code >= 1000, f"{name} sits below the application range"
        else:
            assert -32768 <= code <= -32000, f"{name} is not a JSON-RPC code"


def test_every_error_maps_to_one_exception(contract: dict[str, Any]) -> None:
    """A name a caller can catch, not merely a non-empty string.

    Several codes may share a class — `ProtocolError` covers four — but a code with a
    class of its own invention is a class no caller imports.
    """
    for name, error in contract["errors"].items():
        assert error["exception"] in _EXCEPTIONS, (
            f"{name} maps to {error['exception']}, which is not one a caller can catch"
        )


def test_no_exception_is_promised_and_unused(contract: dict[str, Any]) -> None:
    """The other direction: a roster entry nothing raises is a class nobody needs."""
    raised = {error["exception"] for error in contract["errors"].values()}
    assert raised == _EXCEPTIONS


def test_universal_errors_are_real_errors(contract: dict[str, Any]) -> None:
    for name in contract["universal_errors"]:
        assert name in contract["errors"]


def test_no_method_repeats_a_universal_error(contract: dict[str, Any]) -> None:
    universal = set(contract["universal_errors"])
    for name, method in contract["methods"].items():
        repeated = universal.intersection(method["errors"])
        assert not repeated, (
            f"{name} repeats {sorted(repeated)}, which every method can raise"
        )


def test_every_method_error_exists(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        for error in method["errors"]:
            assert error in contract["errors"], f"{name} raises the unknown {error}"


def test_every_method_names_its_domain_in_its_name(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        assert name.startswith(f"{method['domain']}."), name
        assert re.fullmatch(r"[a-z]+\.[a-z_]+", name), f"{name} is not domain.verb"


def test_every_result_shape_exists(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        for shape in _named_shapes(method["result"]):
            assert shape in contract["shapes"], f"{name} returns the unknown {shape}"


def test_every_parameter_type_resolves(contract: dict[str, Any]) -> None:
    """Notifications are checked too, or the one carrying every event goes unchecked."""
    for section in ("methods", "notifications"):
        for name, entry in contract[section].items():
            for parameter, spec in entry["params"].items():
                for shape in _named_shapes(spec["type"]):
                    assert shape in contract["shapes"], (
                        f"{name}.{parameter} is typed as the unknown {shape}"
                    )


def test_every_shape_field_type_resolves(contract: dict[str, Any]) -> None:
    for shape_name, fields in contract["shapes"].items():
        for field, spec in fields.items():
            for shape in _named_shapes(spec["type"]):
                assert shape in contract["shapes"], (
                    f"{shape_name}.{field} is typed as the unknown {shape}"
                )


def test_every_shape_is_reachable(contract: dict[str, Any]) -> None:
    """A shape nothing refers to is a shape nobody will implement.

    Events are walked too: a shape only an event field names is referred to, and
    calling it an orphan would be a failure with the wrong message on it.
    """
    referenced: set[str] = set()
    for method in contract["methods"].values():
        referenced.update(_named_shapes(method["result"]))
        for spec in method["params"].values():
            referenced.update(_named_shapes(spec["type"]))
    for notification in contract["notifications"].values():
        for spec in notification["params"].values():
            referenced.update(_named_shapes(spec["type"]))
    for event in contract["events"].values():
        for spec in event["fields"].values():
            referenced.update(_named_shapes(spec["type"]))
    for fields in contract["shapes"].values():
        for spec in fields.values():
            referenced.update(_named_shapes(spec["type"]))

    orphans = set(contract["shapes"]) - referenced
    assert not orphans, f"nothing refers to {sorted(orphans)}"


def test_everything_documented(contract: dict[str, Any]) -> None:
    """A contract with an undocumented field is a contract read from source anyway.

    Every section, because the one left out is the one that goes undocumented: a
    notification is as much of the wire as a method, and an event field is the only
    thing a client reads off an event.
    """
    for section in ("methods", "notifications", "events"):
        for name, entry in contract[section].items():
            assert entry["summary"], f"{name} says nothing about itself"
    for section in ("methods", "notifications"):
        for name, entry in contract[section].items():
            for parameter, spec in entry["params"].items():
                assert spec["doc"], f"{name}.{parameter} says nothing about itself"
    for name, event in contract["events"].items():
        for field, spec in event["fields"].items():
            assert spec["doc"], f"{name}.{field} says nothing about itself"
    for shape_name, fields in contract["shapes"].items():
        for field, spec in fields.items():
            assert spec["doc"], f"{shape_name}.{field} says nothing about itself"


def test_optional_parameters_declare_a_default(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        for parameter, spec in method["params"].items():
            if not spec["required"]:
                assert "default" in spec, (
                    f"{name}.{parameter} is optional and does not say what it means"
                )


def test_required_parameters_declare_no_default(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        for parameter, spec in method["params"].items():
            if spec["required"]:
                assert "default" not in spec, f"{name}.{parameter} cannot be both"


def test_status_is_live_or_planned(contract: dict[str, Any]) -> None:
    for section in ("methods", "notifications", "events"):
        for name, entry in contract[section].items():
            assert entry["status"] in {"live", "planned"}, name


def test_session_hello_is_frozen(contract: dict[str, Any]) -> None:
    """Version negotiation has to be versionless, so its request can never change."""
    hello = contract["methods"]["session.hello"]
    assert hello["frozen"] is True
    assert set(hello["params"]) == {"protocol", "proof"}
    assert all(spec["required"] for spec in hello["params"].values())


def test_every_gate_is_a_capability(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        for capability in method["gates"]:
            assert capability in contract["capabilities"], (
                f"{name} gates on the unknown {capability}"
            )


def test_a_method_answers_forbidden_exactly_when_it_gates(
    contract: dict[str, Any],
) -> None:
    """`gates` is the whole answer to "can this refuse on a capability".

    `gated` narrows it: a gated method is switched off entirely, while
    `events.subscribe` gates only the argument — subscribing to an ordinary event
    works whether or not the unstable capability is on.
    """
    for name, method in contract["methods"].items():
        answers = "forbidden" in method["errors"]
        assert answers == bool(method["gates"]), name


def test_a_gated_method_says_what_gates_it(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        if method["gated"]:
            assert method["gates"], f"{name} is off and does not say why"


def test_every_capability_is_off_by_default(contract: dict[str, Any]) -> None:
    """What is gated is gated because it is dangerous; a default of on gates nothing."""
    for name, capability in contract["capabilities"].items():
        assert capability["default"] is False, name


def test_anything_gated_on_unstable_says_it_is_unstable(
    contract: dict[str, Any],
) -> None:
    """The gate is the switch; the flag is the warning. A gate without one is a trap.

    Only what is *itself* off on the unstable capability carries the flag.
    `events.subscribe` gates on it too, but only to refuse an unstable event name;
    the method is as stable as the events it is asked for.
    """
    for name, method in contract["methods"].items():
        if method["gated"] and "unstable" in method["gates"]:
            assert method["unstable"] is True, name
    for name, event in contract["events"].items():
        if "unstable" in event["gates"]:
            assert event["unstable"] is True, name


def test_anything_unstable_gates_on_unstable(contract: dict[str, Any]) -> None:
    """And the other way round, which is the half that keeps a warning honest.

    A method that reaches past Obsidian's public API and does not gate on
    ``unstable`` is reachable by a user who never agreed to undocumented internals.
    ``commands.execute`` gates on ``commands`` as well, and needs both.
    """
    for name, method in contract["methods"].items():
        if method["unstable"]:
            assert "unstable" in method["gates"], f"{name} warns and does not gate"
    for name, event in contract["events"].items():
        if event["unstable"]:
            assert "unstable" in event["gates"], f"{name} warns and does not gate"


def test_every_event_field_type_resolves(contract: dict[str, Any]) -> None:
    for name, event in contract["events"].items():
        for field, spec in event["fields"].items():
            for shape in _named_shapes(spec["type"]):
                assert shape in contract["shapes"], (
                    f"{name}.{field} is typed as the unknown {shape}"
                )


def test_every_event_gate_is_a_capability(contract: dict[str, Any]) -> None:
    for name, event in contract["events"].items():
        for capability in event["gates"]:
            assert capability in contract["capabilities"], name


def test_a_method_can_refuse_every_gate_its_arguments_carry(
    contract: dict[str, Any],
) -> None:
    """Subscribing to a gated event has to be refusable, or the gate is decorative."""
    gated_events = {
        capability
        for event in contract["events"].values()
        for capability in event["gates"]
    }
    assert gated_events <= set(contract["methods"]["events.subscribe"]["gates"])


def test_notifications_declare_a_direction(contract: dict[str, Any]) -> None:
    for name, notification in contract["notifications"].items():
        assert notification["direction"] in {"vault to client", "client to vault"}, name


def test_an_event_is_its_name_and_its_own_fields(contract: dict[str, Any]) -> None:
    """The envelope carries the discriminator; the table carries the rest.

    ``Event`` cannot list the fields, because they differ per event — so it declares
    the one field every event has, and the events table declares the others. That only
    works while no event wants a field of its own called ``name``.
    """
    assert set(contract["shapes"]["Event"]) == {"name"}
    for name, event in contract["events"].items():
        assert "name" not in event["fields"], (
            f"{name} declares a field the envelope already uses"
        )


def test_the_event_notification_carries_the_envelope(contract: dict[str, Any]) -> None:
    """A subscription id and a sequence number are of no use without the event."""
    params = contract["notifications"]["events.event"]["params"]
    assert set(params) == {"subscription", "seq", "event"}
    assert params["event"]["type"] == "Event"


def test_a_gap_is_an_event(contract: dict[str, Any]) -> None:
    """The consumer's decision point has to be inside its own loop, not beside it."""
    assert "gap" in contract["events"]
    assert contract["events"]["gap"]["fields"]["missed"]["type"] == "integer"


def test_a_gap_is_the_one_event_nobody_asks_for(contract: dict[str, Any]) -> None:
    """A client that had to subscribe to `gap` could silently miss losing events.

    So every event says whether `events.subscribe` takes its name, and `gap` is the
    one that says no: it arrives on a subscription because that subscription
    overflowed, not because anyone asked.
    """
    for name, event in contract["events"].items():
        assert isinstance(event["subscribable"], bool), name
    unasked = {
        name for name, event in contract["events"].items() if not event["subscribable"]
    }
    assert unasked == {"gap"}


def test_a_bounded_number_says_both_of_its_bounds(contract: dict[str, Any]) -> None:
    """Half a range is a number a client still cannot check before it sends it."""
    for name, method in contract["methods"].items():
        for parameter, spec in method["params"].items():
            declared = {"minimum", "maximum"}.intersection(spec)
            assert declared in (set(), {"minimum", "maximum"}), (
                f"{name}.{parameter} declares {sorted(declared)} and not the other"
            )


def test_the_event_queue_is_bounded(contract: dict[str, Any]) -> None:
    """It is the one size a peer chooses, and it is spent in Obsidian's renderer."""
    queue = contract["methods"]["events.subscribe"]["params"]["queue"]
    assert queue["minimum"] >= 1
    assert queue["maximum"] >= queue["default"] >= queue["minimum"]


def test_mutating_methods_are_marked(contract: dict[str, Any]) -> None:
    for name, method in contract["methods"].items():
        assert isinstance(method["mutates"], bool), name


def test_read_and_process_agree_on_the_hash(contract: dict[str, Any]) -> None:
    """Compare-and-set works only if one returns the token the other takes."""
    read = contract["shapes"][contract["methods"]["files.read"]["result"]]
    assert "hash" in read
    assert "expect_hash" in contract["methods"]["files.process"]["params"]
    assert "conflict" in contract["methods"]["files.process"]["errors"]
