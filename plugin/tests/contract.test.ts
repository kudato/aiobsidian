/**
 * The plugin against the contract.
 *
 * `protocol/methods.json` is the shared file, so nothing here restates what it says —
 * these tests read it and check that the plugin agrees. A method the plugin answers and
 * the contract does not name is undocumented; a live method in the contract the plugin
 * does not answer is a promise it does not keep. Both are failures here rather than at a
 * caller.
 *
 * What is under test is a **connection the plugin built**, not a registry assembled
 * here. Earlier rounds of this test compared a registry with one the test made to match,
 * which agrees with itself no matter what a peer can actually reach — and in particular
 * said nothing about the methods the connection answers before the handshake, which are
 * the ones where being wrong hands a stranger the vault's token.
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { after, afterEach, describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import type { App } from "obsidian";

import { type ApiContext, buildRegistry } from "../src/api/index.ts";
import { CODES } from "../src/protocol/codes.ts";
import { MAX_MESSAGE_BYTES } from "../src/protocol/framing.ts";
import { PROTOCOL_MAJOR, PROTOCOL_MINOR, SUPPORTED_MAJORS } from "../src/protocol/version.ts";
import { clientProof } from "../src/server/auth.ts";
import { type Connection, DEFAULT_LIMITS } from "../src/server/connection.ts";
import { Sessions } from "../src/server/sessions.ts";
import { MAX_CONNECTIONS } from "../src/server/socket.ts";
import { DEFAULT_SETTINGS, type Settings } from "../src/settings.ts";

interface Contract {
  readonly protocol: { readonly major: number; readonly minor: number };
  readonly errors: Record<string, { readonly code: number }>;
  readonly methods: Record<string, { readonly status: string }>;
  readonly notifications: Record<
    string,
    { readonly status: string; readonly direction: string }
  >;
}

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..");
const contract = JSON.parse(
  await fs.readFile(path.join(root, "protocol", "methods.json"), "utf8"),
) as Contract;

const scratch = await fs.mkdtemp(path.join(os.tmpdir(), "aio-contract-"));
const TOKEN = Buffer.alloc(32, 7);

function methodsWithStatus(status: string): string[] {
  return Object.entries(contract.methods)
    .filter(([, method]) => method.status === status)
    .map(([name]) => name)
    .sort();
}

/**
 * A context the way a domain will really see one.
 *
 * `app` is a stub, which is the point of the rule `buildRegistry` states: a domain that
 * registered conditionally on something in here would register nothing under this
 * context, and the comparison below would agree that all is well.
 */
function context(settings: Settings = DEFAULT_SETTINGS): ApiContext {
  return { app: {} as App, settings: () => settings };
}

const servers: net.Server[] = [];
const clients: net.Socket[] = [];

afterEach(async () => {
  for (const client of clients.splice(0)) {
    client.destroy();
  }
  await Promise.all(
    servers.splice(0).map(
      (server) =>
        new Promise<void>((resolve) => {
          server.close(() => {
            resolve();
          });
        }),
    ),
  );
});

after(async () => {
  await fs.rm(scratch, { recursive: true, force: true });
});

let counter = 0;

interface Peer {
  readonly sessions: Sessions;
  readonly connection: Connection;
  next(within?: number): Promise<Record<string, unknown>>;
  send(message: unknown): void;
  /** Send `session.hello` with a valid proof and read the answer. */
  handshake(nonce: string): Promise<Record<string, unknown>>;
}

/**
 * A client attached to a `Sessions` built the way the plugin builds one.
 *
 * Deliberately not a `Connection` constructed here: `Sessions` is where the registry
 * comes from, and a test that builds its own connection would be testing the thing it
 * assembled rather than the thing that serves.
 */
async function peer(settings: Settings = DEFAULT_SETTINGS): Promise<Peer> {
  counter += 1;
  const socketPath = path.join(scratch, `case-${counter}.sock`);

  const sessions = new Sessions({
    token: TOKEN,
    context: context(settings),
    describe: () => ({
      plugin_version: "0.1.0",
      obsidian_version: "1.13.1",
      vault: { id: "0123456789abcdef", name: "Notes", path: "/Users/ada/Notes" },
    }),
  });

  let accepted: ((connection: Connection) => void) | null = null;
  const ready = new Promise<Connection>((resolve) => {
    accepted = resolve;
  });
  const server = net.createServer((socket) => {
    accepted?.(sessions.accept(socket));
  });
  servers.push(server);
  await new Promise<void>((resolve) => server.listen(socketPath, resolve));

  const client = net.connect(socketPath);
  clients.push(client);
  await new Promise((resolve, reject) => {
    client.once("connect", resolve);
    client.once("error", reject);
  });

  const queue: Record<string, unknown>[] = [];
  const waiting: ((message: Record<string, unknown>) => void)[] = [];
  let buffer = "";
  client.on("data", (chunk: Buffer) => {
    buffer += chunk.toString("utf8");
    for (;;) {
      const newline = buffer.indexOf("\n");
      if (newline === -1) {
        return;
      }
      const line = buffer.slice(0, newline);
      buffer = buffer.slice(newline + 1);
      if (line.trim().length === 0) {
        continue;
      }
      const message = JSON.parse(line) as Record<string, unknown>;
      const waiter = waiting.shift();
      if (waiter === undefined) {
        queue.push(message);
      } else {
        waiter(message);
      }
    }
  });

  const next = (within = 2_000): Promise<Record<string, unknown>> =>
    new Promise((resolve, reject) => {
      const pending = queue.shift();
      if (pending !== undefined) {
        resolve(pending);
        return;
      }
      const timer = setTimeout(() => {
        reject(new Error("the server said nothing"));
      }, within);
      waiting.push((message) => {
        clearTimeout(timer);
        resolve(message);
      });
    });

  const send = (message: unknown): void => {
    client.write(`${JSON.stringify(message)}\n`);
  };

  return {
    sessions,
    connection: await ready,
    next,
    send,
    handshake: async (nonce: string) => {
      send({
        jsonrpc: "2.0",
        id: "hello",
        method: "session.hello",
        params: {
          protocol: [PROTOCOL_MAJOR],
          proof: clientProof(TOKEN, Buffer.from(nonce, "hex")).toString("hex"),
        },
      });
      return next();
    },
  };
}

function errorCode(message: Record<string, unknown>): number | null {
  const error = message["error"] as { code?: number } | undefined;
  return error?.code ?? null;
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

  it("answers exactly the methods the contract calls live", async () => {
    // Read off a live connection, both halves of it: the registry `Sessions` built and
    // the methods the connection answers before there is a session at all. The second
    // half is the one a test that stops at the registry never sees.
    const { connection } = await peer();
    assert.deepEqual(connection.answers, methodsWithStatus("live"));
  });

  it("answers nothing the contract only plans", async () => {
    // The same set from the other side, over the wire, after a real handshake: a
    // planned method has to be methodNotFound and not some half-built answer.
    const { next, handshake, send } = await peer();
    const challenge = await next();
    const nonce = (challenge["params"] as { nonce: string }).nonce;
    await handshake(nonce);

    for (const name of methodsWithStatus("planned")) {
      send({ jsonrpc: "2.0", id: name, method: name, params: {} });
      const answer = await next();
      assert.equal(answer["id"], name);
      assert.equal(errorCode(answer), CODES.methodNotFound, `${name} answers something`);
    }
  });

  it("answers nothing but the handshake before the handshake", async () => {
    // spec.md §3 calls this an invariant rather than an accident of today's method
    // list, so it is checked against the whole list rather than against today's.
    const probes = [...Object.keys(contract.methods), "session.diagnostics"].filter(
      (name) => name !== "session.hello",
    );
    for (const name of probes) {
      const { next, send } = await peer();
      const challenge = await next();
      assert.equal(challenge["method"], "session.challenge");

      send({ jsonrpc: "2.0", id: 1, method: name, params: {} });
      const answer = await next();
      assert.equal(
        errorCode(answer),
        CODES.unauthenticated,
        `${name} answered an unproven peer`,
      );
      assert.equal(answer["result"], undefined, `${name} told an unproven peer something`);
    }
  });

  it("registers the same methods whatever the context says", () => {
    // The rule `buildRegistry` states, checked rather than trusted: a domain that
    // registered only when a capability is on would be invisible to every test above,
    // because their context is a stub and every such condition takes its off-branch.
    const off = buildRegistry(context({ ...DEFAULT_SETTINGS, serve: false })).names();
    const on = buildRegistry(context({ ...DEFAULT_SETTINGS, serve: true })).names();
    assert.deepEqual(off, on);
  });

  it("hands out a registry nothing can add to or replace afterwards", () => {
    const registry = buildRegistry(context());
    assert.throws(() => {
      registry.add("files.sneaky", () => null);
    }, /sealed/);
    assert.throws(
      () => {
        (registry as unknown as { get: unknown }).get = () => () => null;
      },
      TypeError,
      "a replacement lookup would serve a method the name list never mentions",
    );
  });

  it("sends the notifications the contract calls live, and no others", async () => {
    // Observed, not grepped for: a name spelled right in the source and never sent is
    // exactly the failure a source scan cannot tell from success.
    const { sessions, next } = await peer();
    const seen = new Set<string>();

    const challenge = await next();
    seen.add(challenge["method"] as string);

    sessions.closeAll("stopped");
    const goodbye = await next();
    seen.add(goodbye["method"] as string);
    assert.equal((goodbye["params"] as { reason: string }).reason, "stopped");

    const live = Object.entries(contract.notifications)
      .filter(
        ([, notification]) =>
          notification.status === "live" && notification.direction === "vault to client",
      )
      .map(([name]) => name)
      .sort();
    assert.deepEqual([...seen].sort(), live);
  });

  it("acts on the one notification the contract has a client send", async () => {
    // `rpc.cancel` is client to vault, so the way to observe it is its effect: the
    // withdrawal has to come back as an answer rather than as silence.
    const { next, handshake, send } = await peer();
    const challenge = await next();
    const nonce = (challenge["params"] as { nonce: string }).nonce;
    await handshake(nonce);

    // No method is registered yet, so a request cannot be left running to withdraw.
    // What can be checked is that the vault takes the notification and says nothing
    // back, which is what JSON-RPC asks of a notification it cannot act on.
    send({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 404 } });
    send({ jsonrpc: "2.0", id: "after", method: "files.read", params: {} });
    const answer = await next();
    assert.equal(answer["id"], "after", "the cancellation drew an answer of its own");
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
    assert.equal(DEFAULT_LIMITS.maxQueuedBytes, 2 * MAX_MESSAGE_BYTES);
  });
});
