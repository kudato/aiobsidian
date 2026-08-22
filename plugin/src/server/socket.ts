import fs from "node:fs/promises";
import net from "node:net";

import { errorCode, ServeError } from "../lib/errors.ts";
import { ensureRuntimeDirectory } from "./directory.ts";

/** How long a probe waits for an answer before deciding the socket is alive. */
const PROBE_TIMEOUT_MS = 1_000;

/** How long a stop waits for peers to close their own half before dropping them. */
const STOP_LINGER_MS = 1_000;

/**
 * How long to wait before asking a second time whether a socket is really alive.
 *
 * A plugin being disabled and enabled again is the ordinary case here: `onunload`
 * cannot be awaited, so the handle from the previous load may still be answering when
 * the next one probes, and a single look would refuse to serve a vault nothing else
 * wants. Something genuinely listening is still listening on the second look.
 */
const PROBE_RETRY_MS = 250;

/** What a connect probe found at a socket path. */
type Occupant =
  /** Nothing is there. */
  | "absent"
  /** Something is there and it is not answering. */
  | "dead"
  /** Someone is listening. */
  | "live";

export interface SocketServerOptions {
  /** The unix socket path, or the Windows pipe name. */
  readonly socketPath: string;
  /** The directory holding the socket, or `null` on Windows. */
  readonly directory: string | null;
  /** Hands every accepted connection on. */
  readonly onConnection: (socket: net.Socket) => void;
  /** Called whenever the number of open connections changes. */
  readonly onConnectionsChanged?: (count: number) => void;
  /** Called for errors the server reports after it started listening. */
  readonly onRuntimeError?: (error: Error) => void;
  /**
   * How many clients may be attached at once.
   *
   * Enforced by libuv, so the refusal costs nothing and writes nothing. Every request
   * runs on the renderer's single JS thread, competing with the editor the user is
   * typing in, and on Windows each pipe instance reserves 64 KiB in and 64 KiB out of
   * nonpaged pool.
   */
  readonly maxConnections?: number;
}

/** The default cap on attached clients. */
export const MAX_CONNECTIONS = 16;

/**
 * The listening half of the plugin: a socket, the connections on it, and the rules
 * about when it is allowed to exist.
 *
 * It knows nothing about the protocol. Accepted sockets go straight to
 * `onConnection`, which is where framing, the handshake and dispatch live.
 */
export class SocketServer {
  readonly #options: SocketServerOptions;
  readonly #connections = new Set<net.Socket>();
  #server: net.Server | null = null;

  constructor(options: SocketServerOptions) {
    this.#options = options;
  }

  get listening(): boolean {
    return this.#server !== null;
  }

  get connectionCount(): number {
    return this.#connections.size;
  }

  /**
   * Start listening, or do nothing if already listening.
   *
   * Raises:
   *     ServeError: The directory is not safe, the name is taken, or `listen()`
   *         failed for any other reason. The name being taken is a refusal and not a
   *         retry: on Windows the pipe namespace is global and unprivileged, so
   *         something else answering to our name is a fact worth stopping for.
   */
  async start(): Promise<void> {
    if (this.#server !== null) {
      return;
    }

    const { directory, socketPath } = this.#options;
    if (directory !== null) {
      await ensureRuntimeDirectory(directory, true);
      await clearDeadSocket(socketPath);
    }

    const server = net.createServer((socket) => this.#accept(socket));
    server.maxConnections = this.#options.maxConnections ?? MAX_CONNECTIONS;
    await listen(server, socketPath);
    this.#server = server;

    try {
      server.on("error", (error) => {
        this.#options.onRuntimeError?.(error);
      });

      if (directory !== null) {
        // The socket was created under the umask and has been accepting connections
        // since `listen()` returned. This closes the door on a permissive umask; the
        // directory above is what was holding it shut in the meantime.
        await fs.chmod(socketPath, 0o600);
      }
    } catch (cause) {
      // Anything left half-started is left listening, and a socket nobody knows about
      // is worse than no socket at all.
      await this.stop();
      throw new ServeError("listen-failed", `cannot secure ${socketPath}`, { cause });
    }
  }

  /**
   * Stop listening and drop every open connection.
   *
   * The socket file is removed by libuv when the handle closes, so there is nothing
   * to unlink here — and nothing that could unlink a socket belonging to someone
   * else, which is the failure this avoids by never binding over a live one.
   */
  async stop(): Promise<void> {
    const server = this.#server;
    this.#server = null;

    if (server === null) {
      for (const socket of this.#connections) {
        socket.destroy();
      }
      this.#connections.clear();
      this.#options.onConnectionsChanged?.(0);
      return;
    }

    // `end()` rather than `destroy()`: a session that has just been told why it is
    // being hung up on still has that goodbye in its write buffer, and destroying the
    // socket throws it away — worst for a client slow to read, which is the one the
    // explanation is most use to.
    for (const socket of this.#connections) {
      socket.end();
    }

    const closed = new Promise<void>((resolve) => {
      server.close(() => {
        resolve();
      });
    });
    // A peer under no obligation to close its own half must not hold the vault's
    // teardown open.
    const linger = setTimeout(() => {
      for (const socket of this.#connections) {
        socket.destroy();
      }
    }, STOP_LINGER_MS);
    linger.unref?.();
    await closed;
    clearTimeout(linger);

    this.#connections.clear();
    this.#options.onConnectionsChanged?.(0);
  }

  #accept(socket: net.Socket): void {
    // The socket carries small requests that are waited on, so Nagle's algorithm buys
    // nothing and costs a round trip. Obsidian's own CLI server does the same.
    socket.setNoDelay(true);
    this.#connections.add(socket);
    this.#options.onConnectionsChanged?.(this.#connections.size);

    const forget = (): void => {
      if (this.#connections.delete(socket)) {
        this.#options.onConnectionsChanged?.(this.#connections.size);
      }
    };
    socket.once("close", forget);
    // A client that dies mid-write raises here; without a listener it would take the
    // whole application down.
    socket.on("error", forget);

    this.#options.onConnection(socket);
  }
}

/** Bind, turning the two failures worth telling apart into `ServeError`. */
function listen(server: net.Server, socketPath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const onError = (error: Error): void => {
      server.removeListener("listening", onListening);
      reject(
        errorCode(error) === "EADDRINUSE"
          ? new ServeError(
              "address-in-use",
              `something is already listening on ${socketPath}; refusing to serve this vault`,
              { cause: error },
            )
          : new ServeError("listen-failed", `cannot listen on ${socketPath}: ${error.message}`, {
              cause: error,
            }),
      );
    };
    const onListening = (): void => {
      server.removeListener("error", onError);
      resolve();
    };
    server.once("error", onError);
    server.once("listening", onListening);
    server.listen(socketPath);
  });
}

/**
 * Remove a socket left behind by a process that is gone.
 *
 * Obsidian's own CLI unlinks the path unconditionally, but it does so once per
 * machine, behind `requestSingleInstanceLock()`. A plugin has no such lock: it loads
 * per vault, per window, per enable, so an unconditional unlink is one instance
 * deleting another's live socket — after which the first serves an inode nobody can
 * reach and reports no error at all. So two things have to be true before anything is
 * deleted: nothing answered, and what is there is a socket. Neither is enough alone —
 * a live socket must survive, and a file that is not a socket is not ours to remove,
 * whatever `connect()` said about it. Platforms disagree on that last point: Darwin
 * refuses a regular file with `ENOTSOCK` and Linux with `ECONNREFUSED`, so `lstat`
 * decides rather than the error code.
 *
 * Raises:
 *     ServeError: Something is listening there, or the path holds something that is
 *         not a socket.
 */
async function clearDeadSocket(socketPath: string): Promise<void> {
  let occupant = await probe(socketPath);
  if (occupant === "live") {
    // Possibly the handle from this plugin's own previous load, which `onunload` had
    // no way to await. Ask once more before refusing to serve the vault.
    await new Promise<void>((resolve) => {
      const timer = setTimeout(resolve, PROBE_RETRY_MS);
      timer.unref?.();
    });
    occupant = await probe(socketPath);
  }
  if (occupant === "absent") {
    return;
  }
  if (occupant === "live") {
    throw new ServeError(
      "address-in-use",
      `something is already listening on ${socketPath}; refusing to serve this vault`,
    );
  }

  let stats;
  try {
    stats = await fs.lstat(socketPath);
  } catch (cause) {
    if (errorCode(cause) === "ENOENT") {
      return;
    }
    throw new ServeError("listen-failed", `cannot inspect ${socketPath}`, { cause });
  }
  if (!stats.isSocket()) {
    throw new ServeError(
      "listen-failed",
      `${socketPath} exists and is not a socket; remove it and reload the plugin`,
    );
  }

  try {
    await fs.unlink(socketPath);
  } catch (cause) {
    if (errorCode(cause) !== "ENOENT") {
      throw new ServeError("listen-failed", `cannot remove the stale socket ${socketPath}`, {
        cause,
      });
    }
  }
}

/** Ask a socket path whether anyone is home. */
function probe(socketPath: string): Promise<Occupant> {
  return new Promise((resolve) => {
    const socket = net.connect(socketPath);
    const finish = (occupant: Occupant): void => {
      socket.destroy();
      resolve(occupant);
    };
    socket.setTimeout(PROBE_TIMEOUT_MS, () => {
      finish("live");
    });
    socket.once("connect", () => {
      finish("live");
    });
    socket.once("error", (error) => {
      const code = errorCode(error);
      if (code === "ENOENT") {
        finish("absent");
      } else if (code === "ECONNREFUSED" || code === "ENOTSOCK") {
        finish("dead");
      } else {
        // Anything unrecognised counts as occupied. Treating a path we failed to
        // understand as free is the one outcome here with no way back.
        finish("live");
      }
    });
  });
}
