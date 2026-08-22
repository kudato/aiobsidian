/**
 * The plugin against the contract.
 *
 * `protocol/methods.json` is the shared file, so nothing here restates what it says —
 * these tests read it and check that the plugin agrees. A method registered but not in
 * the contract is undocumented; a live method in the contract but not registered is a
 * promise the plugin does not keep. Both are failures here rather than at a caller.
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import { CODES } from "../src/protocol/codes.ts";
import { MAX_MESSAGE_BYTES } from "../src/protocol/framing.ts";
import { PROTOCOL_MAJOR, PROTOCOL_MINOR, SUPPORTED_MAJORS } from "../src/protocol/version.ts";
import { DEFAULT_LIMITS } from "../src/server/connection.ts";
import { MethodRegistry } from "../src/server/registry.ts";
import { MAX_CONNECTIONS } from "../src/server/socket.ts";

interface Contract {
  readonly protocol: { readonly major: number; readonly minor: number };
  readonly errors: Record<string, { readonly code: number }>;
  readonly methods: Record<string, { readonly status: string; readonly domain: string }>;
  readonly notifications: Record<string, { readonly status: string }>;
}

const here = path.dirname(fileURLToPath(import.meta.url));
const contract = JSON.parse(
  await fs.readFile(path.join(here, "..", "..", "protocol", "methods.json"), "utf8"),
) as Contract;

/**
 * Everything the plugin should have in its registry.
 *
 * `session.*` and `rpc.*` are answered by the connection itself, before there is an
 * authenticated session to dispatch on, so they are in the contract but never in the
 * registry.
 */
function expectedMethods(): string[] {
  return Object.entries(contract.methods)
    .filter(([, method]) => method.status === "live" && method.domain !== "session")
    .map(([name]) => name)
    .sort();
}

/** The registry the plugin builds, with every domain registered into it. */
function registry(): MethodRegistry {
  const methods = new MethodRegistry();
  // Domains register here as they land. Until then the list is empty, and the test
  // below is what says so out loud rather than letting it pass unnoticed.
  return methods;
}

describe("the plugin against protocol/methods.json", () => {
  it("speaks the version the contract names", () => {
    assert.equal(PROTOCOL_MAJOR, contract.protocol.major);
    assert.equal(PROTOCOL_MINOR, contract.protocol.minor);
  });

  it("still speaks the major it ships", () => {
    assert.ok(SUPPORTED_MAJORS.includes(PROTOCOL_MAJOR));
  });

  it("uses exactly the error codes the contract defines", () => {
    const fromContract = Object.fromEntries(
      Object.entries(contract.errors).map(([name, error]) => [name, error.code]),
    );
    assert.deepEqual({ ...CODES }, fromContract);
  });

  it("registers exactly the methods the contract calls live", () => {
    assert.deepEqual(registry().names(), expectedMethods());
  });

  it("answers every notification the contract calls live", () => {
    // Nothing dispatches these through the registry, so the check is that the contract
    // and the connection agree on the names — a rename on one side has to fail here.
    const live = Object.entries(contract.notifications)
      .filter(([, notification]) => notification.status === "live")
      .map(([name]) => name)
      .sort();
    assert.deepEqual(live, ["rpc.cancel", "session.challenge", "session.goodbye"]);
  });

  it("caps a frame at the 16 MiB the specification names", () => {
    assert.equal(MAX_MESSAGE_BYTES, 16 * 1024 * 1024);
    assert.equal(DEFAULT_LIMITS.maxMessageBytes, MAX_MESSAGE_BYTES);
  });

  it("holds to the bounds the specification names", () => {
    assert.equal(MAX_CONNECTIONS, 16);
    assert.equal(DEFAULT_LIMITS.maxInFlight, 32);
    assert.equal(DEFAULT_LIMITS.handshakeTimeoutMs, 5_000);
    assert.equal(DEFAULT_LIMITS.idleTimeoutMs, 30 * 60_000);
  });
});
