import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import { after, afterEach, describe, it } from "node:test";

import { ServeError } from "../src/lib/errors.ts";
import { SocketServer, type SocketServerOptions } from "../src/server/socket.ts";

const scratch = await fs.mkdtemp(path.join(os.tmpdir(), "aio-sock-"));
await fs.chmod(scratch, 0o700);

const running: SocketServer[] = [];
const listeners: net.Server[] = [];

afterEach(async () => {
  await Promise.all(running.splice(0).map((server) => server.stop()));
  await Promise.all(
    listeners.splice(0).map(
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

function fresh(): string {
  counter += 1;
  return path.join(scratch, `case-${counter}.sock`);
}

function build(socketPath: string, overrides: Partial<SocketServerOptions> = {}): SocketServer {
  const server = new SocketServer({
    socketPath,
    directory: scratch,
    onConnection: () => {},
    ...overrides,
  });
  running.push(server);
  return server;
}

async function connect(socketPath: string): Promise<net.Socket> {
  const socket = net.connect(socketPath);
  await new Promise((resolve, reject) => {
    socket.once("connect", resolve);
    socket.once("error", reject);
  });
  return socket;
}

/** Wait for a condition the event loop is about to make true. */
async function eventually(predicate: () => boolean): Promise<void> {
  for (let attempt = 0; attempt < 100; attempt += 1) {
    if (predicate()) {
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 10));
  }
  assert.fail("the condition never became true");
}

async function refusal(server: SocketServer): Promise<ServeError> {
  try {
    await server.start();
  } catch (error) {
    assert.ok(error instanceof ServeError);
    return error;
  }
  return assert.fail("the server started when it should have refused");
}

describe("SocketServer", { skip: process.platform === "win32" }, () => {
  it("listens on a socket no other account can reach", async () => {
    const socketPath = fresh();
    await build(socketPath).start();
    const stats = await fs.lstat(socketPath);
    assert.ok(stats.isSocket());
    assert.equal(stats.mode & 0o777, 0o600);
  });

  it("hands every connection on and counts it", async () => {
    const socketPath = fresh();
    const accepted: net.Socket[] = [];
    const counts: number[] = [];
    const server = build(socketPath, {
      onConnection: (socket) => accepted.push(socket),
      onConnectionsChanged: (count) => counts.push(count),
    });
    await server.start();

    const client = await connect(socketPath);
    await eventually(() => accepted.length === 1);
    assert.equal(server.connectionCount, 1);

    client.destroy();
    await eventually(() => server.connectionCount === 0);
    assert.deepEqual(counts, [1, 0]);
  });

  it("takes the socket with it when it stops", async () => {
    const socketPath = fresh();
    const server = build(socketPath);
    await server.start();
    await server.stop();
    assert.equal(server.listening, false);
    await assert.rejects(fs.lstat(socketPath), { code: "ENOENT" });
  });

  it("drops open connections when it stops", async () => {
    const socketPath = fresh();
    const server = build(socketPath);
    await server.start();
    const client = await connect(socketPath);
    const closed = new Promise((resolve) => client.once("close", resolve));
    await server.stop();
    await closed;
  });

  it("starting twice is starting once", async () => {
    const socketPath = fresh();
    const server = build(socketPath);
    await server.start();
    await server.start();
    assert.equal(server.listening, true);
  });

  it("refuses to bind over a socket someone is serving", async () => {
    const socketPath = fresh();
    const other = net.createServer();
    listeners.push(other);
    await new Promise<void>((resolve) => other.listen(socketPath, resolve));

    const error = await refusal(build(socketPath));
    assert.equal(error.code, "address-in-use");
    // The other server is still there, which is the point: an unconditional unlink
    // would have deleted a live socket and left its owner serving nothing.
    assert.ok((await fs.lstat(socketPath)).isSocket());
  });

  it("clears a socket whose owner was killed", async () => {
    const socketPath = fresh();
    const child = spawn(process.execPath, [
      "-e",
      `require("net").createServer().listen(${JSON.stringify(socketPath)}, () => console.log("up"))`,
    ]);
    await new Promise((resolve) => child.stdout.once("data", resolve));
    child.kill("SIGKILL");
    await new Promise((resolve) => child.once("exit", resolve));
    assert.ok((await fs.lstat(socketPath)).isSocket());

    const server = build(socketPath);
    await server.start();
    assert.equal(server.listening, true);
  });

  it("refuses a path holding something that is not a socket", async () => {
    const socketPath = fresh();
    await fs.writeFile(socketPath, "");
    const error = await refusal(build(socketPath));
    assert.equal(error.code, "listen-failed");
    assert.match(error.message, /not a socket/);
  });

  it("refuses when the directory is open to other accounts", async () => {
    const directory = path.join(scratch, "open");
    await fs.mkdir(directory, { recursive: true });
    await fs.chmod(directory, 0o755);
    const server = build(path.join(directory, "x.sock"), { directory });
    assert.equal((await refusal(server)).code, "unsafe-directory");
  });
});
