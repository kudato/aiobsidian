import assert from "node:assert/strict";
import fs from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { after, afterEach, describe, it } from "node:test";

import { CODES } from "../src/protocol/codes.ts";
import { PROTOCOL_MAJOR, PROTOCOL_MINOR } from "../src/protocol/version.ts";
import { clientProof, serverProof } from "../src/server/auth.ts";
import { Connection, type ConnectionLimits } from "../src/server/connection.ts";
import { MethodRegistry } from "../src/server/registry.ts";

const scratch = await fs.mkdtemp(path.join(os.tmpdir(), "aio-conn-"));
const TOKEN = Buffer.alloc(32, 3);

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
  readonly connection: Connection;
  readonly client: net.Socket;
  /** The next message the server sent. */
  next(within?: number): Promise<Record<string, unknown>>;
  send(message: unknown): void;
  raw(text: string): void;
  /** Resolves when the server hangs up. */
  ended(): Promise<void>;
}

interface PeerOptions {
  readonly registry?: MethodRegistry;
  readonly limits?: Partial<ConnectionLimits>;
  readonly token?: Buffer;
}

async function peer(options: PeerOptions = {}): Promise<Peer> {
  counter += 1;
  const socketPath = path.join(scratch, `case-${counter}.sock`);

  let accepted: ((connection: Connection) => void) | null = null;
  const ready = new Promise<Connection>((resolve) => {
    accepted = resolve;
  });

  const server = net.createServer((socket) => {
    const connection = new Connection({
      socket,
      token: options.token ?? TOKEN,
      registry: options.registry ?? new MethodRegistry(),
      describe: () => ({
        plugin_version: "0.1.0",
        obsidian_version: "1.13.1",
        vault: { id: "0123456789abcdef", name: "Notes", path: "/Users/ada/Notes" },
      }),
      ...(options.limits === undefined ? {} : { limits: options.limits }),
    });
    accepted?.(connection);
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

  const ends = new Promise<void>((resolve) => {
    client.once("close", () => {
      resolve();
    });
  });

  return {
    connection: await ready,
    client,
    next: (within = 2_000) =>
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
      }),
    send: (message) => client.write(`${JSON.stringify(message)}\n`),
    raw: (text) => client.write(text),
    ended: () => ends,
  };
}

/** Take the challenge and answer it, leaving an authenticated peer. */
async function greet(
  target: Peer,
  options: { token?: Buffer; protocol?: number[] } = {},
): Promise<Record<string, unknown>> {
  const challenge = await target.next();
  const params = challenge["params"] as { nonce: string };
  const nonce = Buffer.from(params.nonce, "hex");
  target.send({
    jsonrpc: "2.0",
    id: 1,
    method: "session.hello",
    params: {
      protocol: options.protocol ?? [PROTOCOL_MAJOR],
      proof: clientProof(options.token ?? TOKEN, nonce).toString("hex"),
    },
  });
  return await target.next();
}

function errorOf(message: Record<string, unknown>): { code: number; message: string } {
  return message["error"] as { code: number; message: string };
}

describe("Connection", { skip: process.platform === "win32" }, () => {
  it("challenges first and says nothing else", async () => {
    const target = await peer();
    const challenge = await target.next();
    assert.equal(challenge["method"], "session.challenge");
    const params = challenge["params"] as { nonce: string };
    assert.match(params.nonce, /^[0-9a-f]{64}$/);
    await assert.rejects(target.next(200), /said nothing/);
  });

  it("refuses every method until the handshake, and hangs up", async () => {
    const registry = new MethodRegistry();
    registry.add("files.read", () => "secret");
    const target = await peer({ registry });
    await target.next();

    target.send({ jsonrpc: "2.0", id: 1, method: "files.read", params: {} });
    assert.equal(errorOf(await target.next()).code, CODES.unauthenticated);
    await target.ended();
  });

  it("refuses a proof that does not match, and hangs up", async () => {
    const target = await peer();
    const answer = await greet(target, { token: Buffer.alloc(32, 99) });
    assert.equal(errorOf(answer).code, CODES.unauthenticated);
    await target.ended();
  });

  it("refuses a protocol it does not speak, and names the side to update", async () => {
    const target = await peer();
    const answer = await greet(target, { protocol: [PROTOCOL_MAJOR + 1] });
    assert.equal(errorOf(answer).code, CODES.unsupportedProtocol);
    assert.match(errorOf(answer).message, /update the plugin/);
    await target.ended();
  });

  it("tells an older client to update itself", async () => {
    const target = await peer();
    const answer = await greet(target, { protocol: [PROTOCOL_MAJOR - 1] });
    assert.match(errorOf(answer).message, /update the client/);
  });

  it("proves itself back", async () => {
    const target = await peer();
    const challenge = await target.next();
    const nonce = Buffer.from((challenge["params"] as { nonce: string }).nonce, "hex");
    target.send({
      jsonrpc: "2.0",
      id: 1,
      method: "session.hello",
      params: { protocol: [PROTOCOL_MAJOR], proof: clientProof(TOKEN, nonce).toString("hex") },
    });

    const result = (await target.next())["result"] as Record<string, unknown>;
    assert.equal(result["server_proof"], serverProof(TOKEN, nonce).toString("hex"));
    assert.deepEqual(result["protocol"], { major: PROTOCOL_MAJOR, minor: PROTOCOL_MINOR });
    assert.equal(result["plugin_version"], "0.1.0");
    assert.equal(result["obsidian_version"], "1.13.1");
    assert.deepEqual(result["vault"], {
      id: "0123456789abcdef",
      name: "Notes",
      path: "/Users/ada/Notes",
    });
  });

  it("refuses a second handshake on one connection", async () => {
    const target = await peer();
    await greet(target);
    target.send({ jsonrpc: "2.0", id: 2, method: "session.hello", params: { protocol: [1] } });
    assert.equal(errorOf(await target.next()).code, CODES.invalidRequest);
  });

  it("answers a registered method once the handshake is done", async () => {
    const registry = new MethodRegistry();
    registry.add("echo", (params) => params["value"]);
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "echo", params: { value: "hello" } });
    const answer = await target.next();
    assert.equal(answer["id"], 2);
    assert.equal(answer["result"], "hello");
  });

  it("answers in completion order, not arrival order", async () => {
    const registry = new MethodRegistry();
    registry.add("slow", async () => {
      await new Promise((resolve) => setTimeout(resolve, 40));
      return "slow";
    });
    registry.add("fast", () => "fast");
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "slow", params: {} });
    target.send({ jsonrpc: "2.0", id: 3, method: "fast", params: {} });
    assert.equal((await target.next())["id"], 3);
    assert.equal((await target.next())["id"], 2);
  });

  it("reports an unknown method", async () => {
    const target = await peer();
    await greet(target);
    target.send({ jsonrpc: "2.0", id: 2, method: "nope", params: {} });
    assert.equal(errorOf(await target.next()).code, CODES.methodNotFound);
  });

  it("hides what a handler threw from the wire, logs it, and keeps answering", async () => {
    const registry = new MethodRegistry();
    registry.add("boom", () => {
      throw new Error("the password is hunter2");
    });
    registry.add("fine", () => "fine");
    const target = await peer({ registry });
    await greet(target);

    const logged: unknown[] = [];
    const real = console.error;
    console.error = (...parts: unknown[]) => logged.push(...parts);
    try {
      target.send({ jsonrpc: "2.0", id: 2, method: "boom", params: {} });
      const failure = errorOf(await target.next());
      assert.equal(failure.code, CODES.internalError);
      assert.doesNotMatch(failure.message, /hunter2/);
    } finally {
      console.error = real;
    }
    // The cause is not the caller's business, but it must not vanish either: a
    // maintainer reads it in Obsidian's console.
    assert.ok(logged.some((part) => part instanceof Error && /hunter2/.test(part.message)));

    target.send({ jsonrpc: "2.0", id: 3, method: "fine", params: {} });
    assert.equal((await target.next())["result"], "fine");
  });

  it("survives a line that is not JSON", async () => {
    const target = await peer();
    await greet(target);
    target.raw("{ not json\n");
    assert.equal(errorOf(await target.next()).code, CODES.parseError);

    target.send({ jsonrpc: "2.0", id: 2, method: "nope", params: {} });
    assert.equal((await target.next())["id"], 2);
  });

  it("survives a line over the cap and resynchronises on the next one", async () => {
    const registry = new MethodRegistry();
    registry.add("fine", () => "fine");
    const target = await peer({ registry, limits: { maxMessageBytes: 256 } });
    await greet(target);

    target.raw(`${"x".repeat(4096)}\n`);
    const failure = errorOf(await target.next());
    assert.equal(failure.code, CODES.messageTooLarge);

    target.send({ jsonrpc: "2.0", id: 2, method: "fine", params: {} });
    assert.equal((await target.next())["result"], "fine");
  });

  it("refuses to answer with more than the cap", async () => {
    const registry = new MethodRegistry();
    registry.add("huge", () => "x".repeat(4096));
    const target = await peer({ registry, limits: { maxMessageBytes: 1024 } });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "huge", params: {} });
    const failure = errorOf(await target.next());
    assert.equal(failure.code, CODES.messageTooLarge);
    assert.match(failure.message, /pages/);
  });

  it("caps how many requests may be in flight", async () => {
    const registry = new MethodRegistry();
    registry.add("hang", () => new Promise(() => {}));
    const target = await peer({ registry, limits: { maxInFlight: 2 } });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "hang", params: {} });
    target.send({ jsonrpc: "2.0", id: 3, method: "hang", params: {} });
    target.send({ jsonrpc: "2.0", id: 4, method: "hang", params: {} });
    const failure = await target.next();
    assert.equal(failure["id"], 4);
    assert.equal(errorOf(failure).code, CODES.tooManyRequests);
  });

  it("refuses an id that is already in flight", async () => {
    const registry = new MethodRegistry();
    registry.add("hang", () => new Promise(() => {}));
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "hang", params: {} });
    target.send({ jsonrpc: "2.0", id: 2, method: "hang", params: {} });
    assert.equal(errorOf(await target.next()).code, CODES.invalidRequest);
  });

  it("withdraws a request on rpc.cancel", async () => {
    const registry = new MethodRegistry();
    registry.add(
      "wait",
      (_params, context) =>
        new Promise((resolve) => {
          context.signal.addEventListener("abort", () => resolve("stopped"));
        }),
    );
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "wait", params: {} });
    target.send({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 2 } });
    const answer = await target.next();
    assert.equal(answer["id"], 2);
    assert.equal(errorOf(answer).code, CODES.cancelled);
  });

  it("reads a raised abort as the withdrawal it is, not as a failure", async () => {
    const registry = new MethodRegistry();
    registry.add(
      "wait",
      (_params, context) =>
        new Promise((_resolve, reject) => {
          context.signal.addEventListener("abort", () => reject(new Error("aborted")));
        }),
    );
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "wait", params: {} });
    target.send({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 2 } });
    assert.equal(errorOf(await target.next()).code, CODES.cancelled);
  });

  it("ignores rpc.cancel for an id it is not running", async () => {
    const registry = new MethodRegistry();
    registry.add("fine", () => "fine");
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 99 } });
    target.send({ jsonrpc: "2.0", id: 2, method: "fine", params: {} });
    assert.equal((await target.next())["id"], 2);
  });

  it("frees the slot a withdrawn request held", async () => {
    const registry = new MethodRegistry();
    registry.add(
      "wait",
      (_params, context) =>
        new Promise((resolve) => {
          context.signal.addEventListener("abort", () => resolve("stopped"));
        }),
    );
    const target = await peer({ registry, limits: { maxInFlight: 1 } });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "wait", params: {} });
    target.send({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 2 } });
    assert.equal(errorOf(await target.next()).code, CODES.cancelled);

    target.send({ jsonrpc: "2.0", id: 3, method: "wait", params: {} });
    target.send({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 3 } });
    const second = await target.next();
    assert.equal(second["id"], 3);
    assert.equal(errorOf(second).code, CODES.cancelled);
  });

  it("lets a method send notifications down its own connection", async () => {
    const registry = new MethodRegistry();
    registry.add("chatty", (_params, context) => {
      context.notify("progress", { done: 1 });
      return "done";
    });
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", id: 2, method: "chatty", params: {} });
    assert.equal((await target.next())["method"], "progress");
    assert.equal((await target.next())["result"], "done");
  });

  it("ignores a notification it does not know", async () => {
    const registry = new MethodRegistry();
    registry.add("fine", () => "fine");
    const target = await peer({ registry });
    await greet(target);

    target.send({ jsonrpc: "2.0", method: "who.knows", params: {} });
    target.send({ jsonrpc: "2.0", id: 2, method: "fine", params: {} });
    assert.equal((await target.next())["id"], 2);
  });

  it("says goodbye before hanging up", async () => {
    const target = await peer();
    await greet(target);
    target.connection.goodbye("stopped");
    const goodbye = await target.next();
    assert.equal(goodbye["method"], "session.goodbye");
    assert.deepEqual(goodbye["params"], { reason: "stopped" });
    await target.ended();
  });

  it("drops a peer that connects and says nothing", async () => {
    const target = await peer({ limits: { handshakeTimeoutMs: 30 } });
    await target.next();
    await target.ended();
  });

  it("does not drop a peer that finished the handshake", async () => {
    const target = await peer({ limits: { handshakeTimeoutMs: 30 } });
    await greet(target);
    await new Promise((resolve) => setTimeout(resolve, 90));
    assert.equal(target.connection.closed, false);
  });

  it("refuses a protocol list too long to walk, rather than dying on it", async () => {
    // `Math.max(...list)` passes every element as an argument, so a long enough list
    // overflowed the argument stack — a RangeError thrown out of the socket's own data
    // handler, which in Obsidian's renderer is the whole application. Reachable before
    // anything is proved, since negotiation deliberately comes first. The assertion
    // that matters most is not the code below: it is that this process is still here
    // to make it.
    const target = await peer();
    await target.next();
    target.send({
      jsonrpc: "2.0",
      id: 1,
      method: "session.hello",
      params: { protocol: new Array(300_000).fill(2), proof: "00" },
    });
    assert.equal(errorOf(await target.next()).code, CODES.invalidParams);
  });

  it("still negotiates a list of a sensible length", async () => {
    const target = await peer();
    const hello = await greet(target, { protocol: [PROTOCOL_MAJOR, 99] });
    assert.equal((hello["result"] as { protocol: { major: number } }).protocol.major, PROTOCOL_MAJOR);
  });

  it("stops reading from a peer that is behind on what it asked for", async () => {
    // An unflushed write is held in this process, so a peer that asks and never reads
    // spends the vault's memory rather than its own. Reading stops until it catches
    // up, which is what keeps it from asking for more while it is behind.
    const registry = new MethodRegistry();
    registry.add("files.read", () => "x".repeat(200_000));
    const target = await peer({ registry, limits: { idleTimeoutMs: 60_000 } });
    await greet(target);

    target.client.pause();
    for (let id = 10; id < 30; id += 1) {
      target.send({ jsonrpc: "2.0", id, method: "files.read", params: {} });
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    // Every request that arrived was answered into the buffer, and then reading
    // stopped rather than the buffer growing for as long as the peer cared to ask.
    assert.equal(target.connection.reading, false);

    target.client.resume();
    await new Promise((resolve) => setTimeout(resolve, 200));
    assert.equal(target.connection.reading, true);
  });

  it("hangs up on a peer whose queue passes the ceiling", async () => {
    const registry = new MethodRegistry();
    registry.add("files.read", () => "x".repeat(200_000));
    const target = await peer({ registry, limits: { maxQueuedBytes: 64 * 1024 } });
    await greet(target);

    target.client.pause();
    for (let id = 10; id < 30; id += 1) {
      target.send({ jsonrpc: "2.0", id, method: "files.read", params: {} });
    }
    // Not `ended()`: a paused peer does not see the hang-up until it reads again, and
    // never reading is the whole premise of this one.
    await new Promise((resolve) => setTimeout(resolve, 300));
    assert.equal(target.connection.closed, true);
  });

  it("answers nothing more once it has refused a proof", async () => {
    // `end()` shuts the writing half only, so a peer that never sends its own FIN went
    // on being read — and its methods went on running — for the whole linger, with the
    // answers thrown away. A refusal has to be final, not advisory.
    let ran = false;
    const registry = new MethodRegistry();
    registry.add("files.write", () => {
      ran = true;
      return null;
    });
    const target = await peer({ registry });
    const challenge = await target.next();
    const nonce = Buffer.from((challenge["params"] as { nonce: string }).nonce, "hex");
    target.send({
      jsonrpc: "2.0",
      id: 1,
      method: "session.hello",
      params: { protocol: [PROTOCOL_MAJOR], proof: clientProof(Buffer.alloc(32, 9), nonce).toString("hex") },
    });
    assert.equal(errorOf(await target.next()).code, CODES.unauthenticated);

    target.send({
      jsonrpc: "2.0",
      id: 2,
      method: "session.hello",
      params: { protocol: [PROTOCOL_MAJOR], proof: clientProof(TOKEN, nonce).toString("hex") },
    });
    target.send({ jsonrpc: "2.0", id: 3, method: "files.write", params: {} });
    await new Promise((resolve) => setTimeout(resolve, 100));
    assert.equal(ran, false, "a refused connection ran a method");
  });

  it("drops the id rather than answering with a frame over the cap", async () => {
    // The cap binds this side too, and a conforming client discards a line over it. A
    // refusal carries less around the id than a request does, but not by much, so an id
    // that only just fit on the way in cannot be echoed back inside one.
    const cap = 1_024;
    const target = await peer({ limits: { maxMessageBytes: cap } });
    await target.next();
    target.send({ jsonrpc: "2.0", id: "x".repeat(cap - 50), method: "", params: {} });
    const answer = await target.next();
    assert.equal(answer["id"], null);
    assert.ok(Buffer.byteLength(JSON.stringify(answer), "utf8") <= cap);
  });

  it("cuts the words of a refusal before it gives up the id", async () => {
    // Dropping the id is not enough when the message is the bulk: a refusal quotes the
    // method name back, and the caller picks that too. Nor is it what should go — an id
    // this short costs the frame nothing, and it is what the answer is for.
    const cap = 4_096;
    const target = await peer({ limits: { maxMessageBytes: cap } });
    await greet(target);
    // As long a name as the inbound cap will carry, which is what makes the refusal
    // quoting it back the thing that does not fit.
    target.send({ jsonrpc: "2.0", id: 2, method: "n".repeat(cap - 60), params: {} });
    const answer = await target.next();
    assert.equal(answer["id"], 2);
    assert.equal(errorOf(answer).code, CODES.methodNotFound);
    assert.ok(Buffer.byteLength(JSON.stringify(answer), "utf8") <= cap);
    assert.match(errorOf(answer).message, /…$/);
  });
});
