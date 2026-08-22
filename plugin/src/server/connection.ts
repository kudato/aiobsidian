import type net from "node:net";

import { type Code, CODES, RpcError } from "../protocol/codes.ts";
import { LineReader, MAX_MESSAGE_BYTES } from "../protocol/framing.ts";
import { type Inbound, readMessage, type RequestId } from "../protocol/messages.ts";
import { negotiate, PROTOCOL_MINOR, SUPPORTED_MAJORS } from "../protocol/version.ts";
import { challengeNonce, clientProof, proofMatches, serverProof } from "./auth.ts";
import type { MethodRegistry } from "./registry.ts";

/** What `session.hello` answers with, beyond the parts the connection computes. */
export interface SessionDescription {
  readonly plugin_version: string;
  readonly obsidian_version: string;
  readonly vault: {
    readonly id: string;
    readonly name: string;
    readonly path: string;
  };
}

/**
 * Why the vault is hanging up.
 *
 * Two, not the three that were sketched, because a plugin cannot tell being disabled
 * from the application quitting: `onunload` is both. Saying "unloading" is true in
 * every case it covers, and a client that reconnects on a guess is worse off than one
 * told plainly that it does not know.
 */
export type GoodbyeReason = "stopped" | "unloading";

export interface ConnectionLimits {
  /** The cap on one line, in bytes, in both directions. */
  readonly maxMessageBytes: number;
  /** How long a connection has to complete the handshake. */
  readonly handshakeTimeoutMs: number;
  /** How long a connection may go without a byte in either direction. */
  readonly idleTimeoutMs: number;
  /** How many requests may be running at once on one connection. */
  readonly maxInFlight: number;
}

/** How long a hang-up waits for the peer to close its own half. */
const LINGER_MS = 1_000;

export const DEFAULT_LIMITS: ConnectionLimits = {
  maxMessageBytes: MAX_MESSAGE_BYTES,
  // The five seconds Obsidian's own CLI server gives a client that has not sent its
  // header, kept for the same job: dropping a peer that connects and says nothing.
  handshakeTimeoutMs: 5_000,
  idleTimeoutMs: 30 * 60_000,
  maxInFlight: 32,
};

export interface ConnectionOptions {
  readonly socket: net.Socket;
  readonly token: Buffer;
  readonly registry: MethodRegistry;
  /** Read when the handshake succeeds, so the answer is never stale. */
  readonly describe: () => SessionDescription;
  readonly limits?: Partial<ConnectionLimits>;
}

/**
 * One client, from the challenge to the last byte.
 *
 * The invariant that holds the security of this design together: **nothing but the
 * challenge is written, and no method but `session.hello` is answered, until a valid
 * proof arrives.** On Windows libuv creates named pipes with no security descriptor,
 * so the default one grants read to Everyone and to anything authenticated over
 * `IPC$`; a peer that can read but not prove anything must therefore harvest nothing
 * but a nonce. This is an invariant and not an accident of today's method list — a
 * banner, a version string or a startup event added later turns it back into a leak.
 *
 * The one thing an unproven peer can learn is which protocol majors this plugin
 * speaks, because negotiation has to come before the proof: a future major is free to
 * change how the proof is computed, and only this order can tell an outdated client so
 * instead of failing it with an authentication error it cannot act on. The majors are
 * a published constant of the release, not a fact about this vault.
 */
export class Connection {
  readonly #socket: net.Socket;
  readonly #token: Buffer;
  readonly #registry: MethodRegistry;
  readonly #describe: () => SessionDescription;
  readonly #limits: ConnectionLimits;
  readonly #nonce = challengeNonce();
  readonly #reader: LineReader;
  readonly #running = new Map<RequestId, AbortController>();
  readonly #closeHandlers: (() => void)[] = [];

  #authenticated = false;
  #closing = false;
  #closed = false;
  #handshakeTimer: ReturnType<typeof setTimeout> | null = null;
  #idleTimer: ReturnType<typeof setTimeout> | null = null;

  constructor(options: ConnectionOptions) {
    this.#socket = options.socket;
    this.#token = options.token;
    this.#registry = options.registry;
    this.#describe = options.describe;
    this.#limits = { ...DEFAULT_LIMITS, ...options.limits };

    this.#reader = new LineReader({
      maxBytes: this.#limits.maxMessageBytes,
      onLine: (line) => {
        this.#onLine(line);
      },
      onOversize: (bytes) => {
        // The connection survives: the line was dropped, not the stream, and the next
        // newline is a clean start. This is the whole reason for a delimiter.
        this.#sendError(
          null,
          CODES.messageTooLarge,
          `a message of at least ${bytes} bytes was discarded; the cap is ${this.#limits.maxMessageBytes}`,
        );
      },
    });

    this.#socket.on("data", (chunk: Buffer) => {
      this.#touch();
      this.#reader.push(chunk);
    });
    this.#socket.once("close", () => {
      this.#onClosed();
    });
    this.#socket.on("error", () => {
      this.#onClosed();
    });

    this.#send({
      jsonrpc: "2.0",
      method: "session.challenge",
      params: { nonce: this.#nonce.toString("hex") },
    });
    this.#handshakeTimer = setTimeout(() => {
      this.close();
    }, this.#limits.handshakeTimeoutMs);
    this.#handshakeTimer.unref?.();
    this.#touch();
  }

  get authenticated(): boolean {
    return this.#authenticated;
  }

  get closed(): boolean {
    return this.#closed || this.#closing;
  }

  /** Register a callback for when this connection is gone. */
  onClose(handler: () => void): void {
    if (this.#closed) {
      handler();
      return;
    }
    this.#closeHandlers.push(handler);
  }

  /** Say why, then hang up. */
  goodbye(reason: GoodbyeReason): void {
    this.#send({ jsonrpc: "2.0", method: "session.goodbye", params: { reason } });
    this.close();
  }

  /**
   * Hang up.
   *
   * `end()` rather than `destroy()`, so a goodbye written a moment ago actually
   * leaves; and a timer behind it, because a peer that never closes its own half would
   * otherwise hold the connection — and one of the sixteen — open for as long as it
   * likes.
   */
  close(): void {
    if (this.#closed || this.#closing) {
      return;
    }
    this.#closing = true;
    this.#socket.end();
    const linger = setTimeout(() => {
      this.#socket.destroy();
    }, LINGER_MS);
    linger.unref?.();
    this.#socket.once("close", () => {
      clearTimeout(linger);
    });
  }

  #onLine(line: Buffer): void {
    const text = line.toString("utf8").trim();
    if (text.length === 0) {
      return;
    }

    let value: unknown;
    try {
      value = JSON.parse(text);
    } catch {
      this.#sendError(null, CODES.parseError, "the line is not JSON");
      return;
    }

    const message = readMessage(value);
    this.#dispatch(message);
  }

  #dispatch(message: Inbound): void {
    if (message.kind === "invalid") {
      this.#sendError(message.id, message.code, message.message);
      return;
    }
    if (message.kind === "notification") {
      this.#onNotification(message.notification.method, message.notification.params);
      return;
    }

    const { id, method, params } = message.request;

    if (method === "session.hello") {
      this.#hello(id, params);
      return;
    }
    if (!this.#authenticated) {
      this.#sendError(
        id,
        CODES.unauthenticated,
        "send session.hello with a valid proof before anything else",
      );
      this.close();
      return;
    }
    if (this.#running.size >= this.#limits.maxInFlight) {
      this.#sendError(
        id,
        CODES.tooManyRequests,
        `at most ${this.#limits.maxInFlight} requests may be in flight on one connection`,
      );
      return;
    }
    if (this.#running.has(id)) {
      this.#sendError(id, CODES.invalidRequest, `id ${JSON.stringify(id)} is already in flight`);
      return;
    }

    this.#run(id, method, params);
  }

  #onNotification(method: string, params: Record<string, unknown>): void {
    // Withdrawing a request is the one notification a client sends, and it is answered
    // by aborting rather than by a reply. Everything else is ignored in silence, which
    // is what JSON-RPC asks for.
    if (method === "rpc.cancel" && this.#authenticated) {
      const id = params["id"];
      if (typeof id === "string" || typeof id === "number") {
        this.#running.get(id)?.abort();
      }
    }
  }

  #run(id: RequestId, method: string, params: Record<string, unknown>): void {
    let handler;
    try {
      handler = this.#registry.get(method);
    } catch (error) {
      this.#fail(id, error);
      return;
    }

    const controller = new AbortController();
    this.#running.set(id, controller);

    // Each request is its own task: answers arrive in completion order and the client
    // correlates by id, so one slow method does not hold up the ones behind it.
    void (async () => {
      try {
        const result = await handler(params, {
          notify: (name, notificationParams) => {
            this.#send({ jsonrpc: "2.0", method: name, params: notificationParams });
          },
          signal: controller.signal,
        });
        if (controller.signal.aborted) {
          this.#sendError(id, CODES.cancelled, "the request was withdrawn");
        } else {
          this.#sendResult(id, result);
        }
      } catch (error) {
        // A method that answers an abort by raising is answering the withdrawal, not
        // failing: what it raised is the caller's own doing and not worth logging.
        if (controller.signal.aborted) {
          this.#sendError(id, CODES.cancelled, "the request was withdrawn");
        } else {
          this.#fail(id, error);
        }
      } finally {
        this.#running.delete(id);
      }
    })();
  }

  #hello(id: RequestId, params: Record<string, unknown>): void {
    if (this.#authenticated) {
      this.#sendError(id, CODES.invalidRequest, "session.hello is sent once per connection");
      return;
    }

    const offered = params["protocol"];
    if (
      !Array.isArray(offered) ||
      offered.length === 0 ||
      !offered.every((major) => typeof major === "number")
    ) {
      this.#sendError(
        id,
        CODES.invalidParams,
        "protocol must be a non-empty list of the majors the client implements",
      );
      return;
    }

    const major = negotiate(offered as number[]);
    if (major === null) {
      const older = Math.max(...(offered as number[])) < Math.max(...SUPPORTED_MAJORS);
      this.#sendError(
        id,
        CODES.unsupportedProtocol,
        `this vault speaks protocol ${SUPPORTED_MAJORS.join(", ")} and the client speaks ` +
          `${(offered as number[]).join(", ")}; update the ${older ? "client" : "plugin"}`,
        { server: SUPPORTED_MAJORS, client: offered },
      );
      this.close();
      return;
    }

    if (!proofMatches(clientProof(this.#token, this.#nonce), params["proof"])) {
      this.#sendError(
        id,
        CODES.unauthenticated,
        "the proof does not match; this client cannot read this vault's token",
      );
      this.close();
      return;
    }

    this.#authenticated = true;
    if (this.#handshakeTimer !== null) {
      clearTimeout(this.#handshakeTimer);
      this.#handshakeTimer = null;
    }

    const description = this.#describe();
    this.#sendResult(id, {
      protocol: { major, minor: PROTOCOL_MINOR },
      server_proof: serverProof(this.#token, this.#nonce).toString("hex"),
      ...description,
    });
  }

  #fail(id: RequestId, error: unknown): void {
    if (error instanceof RpcError) {
      this.#sendError(id, error.code, error.message, error.data);
      return;
    }
    // A handler that threw something else is a bug here, not a caller's mistake, and
    // its message is not the caller's business.
    console.error("AIO: a method failed", error);
    this.#sendError(id, CODES.internalError, "the vault failed to answer");
  }

  #sendResult(id: RequestId, result: unknown): void {
    const payload = { jsonrpc: "2.0", id, result: result === undefined ? null : result };
    let encoded: string;
    try {
      encoded = JSON.stringify(payload);
    } catch {
      this.#sendError(id, CODES.internalError, "the result could not be encoded");
      return;
    }
    if (Buffer.byteLength(encoded, "utf8") > this.#limits.maxMessageBytes) {
      this.#sendError(
        id,
        CODES.messageTooLarge,
        `the result is larger than the ${this.#limits.maxMessageBytes} byte cap; read it in pages`,
      );
      return;
    }
    this.#write(encoded);
  }

  #sendError(id: RequestId | null, code: Code, message: string, data?: unknown): void {
    const error: Record<string, unknown> = { code, message };
    if (data !== undefined) {
      error["data"] = data;
    }
    let encoded: string;
    try {
      encoded = JSON.stringify({ jsonrpc: "2.0", id, error });
    } catch {
      encoded = JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } });
    }
    if (Buffer.byteLength(encoded, "utf8") > this.#limits.maxMessageBytes) {
      encoded = JSON.stringify({ jsonrpc: "2.0", id, error: { code, message } });
    }
    this.#write(encoded);
  }

  #send(message: Record<string, unknown>): void {
    this.#write(JSON.stringify(message));
  }

  #write(encoded: string): void {
    if (this.closed || this.#socket.destroyed) {
      return;
    }
    this.#socket.write(`${encoded}\n`);
    this.#touch();
  }

  /** Restart the idle clock. Any byte in either direction counts as being alive. */
  #touch(): void {
    if (this.#idleTimer !== null) {
      clearTimeout(this.#idleTimer);
    }
    this.#idleTimer = setTimeout(() => {
      this.close();
    }, this.#limits.idleTimeoutMs);
    this.#idleTimer.unref?.();
  }

  #onClosed(): void {
    if (this.#closed) {
      return;
    }
    this.#closed = true;
    if (this.#handshakeTimer !== null) {
      clearTimeout(this.#handshakeTimer);
      this.#handshakeTimer = null;
    }
    if (this.#idleTimer !== null) {
      clearTimeout(this.#idleTimer);
      this.#idleTimer = null;
    }
    for (const controller of this.#running.values()) {
      controller.abort();
    }
    this.#running.clear();
    this.#socket.destroy();
    for (const handler of this.#closeHandlers) {
      handler();
    }
    this.#closeHandlers.length = 0;
  }
}
