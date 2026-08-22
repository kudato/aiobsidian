import type net from "node:net";

import { type ApiContext, buildRegistry } from "../api/index.ts";
import {
  Connection,
  type ConnectionLimits,
  type GoodbyeReason,
  type SessionDescription,
} from "./connection.ts";
import type { MethodRegistry } from "./registry.ts";

export interface SessionsOptions {
  readonly token: Buffer;
  /**
   * What the domains are built against.
   *
   * A context and not a registry, deliberately. A `registry` option would be a seam:
   * whatever built one could build another, and the contract test would go on
   * comparing a registry nothing serves. There is no way to hand this class a method
   * set of your own, so the set it serves is the one `buildRegistry` returns.
   */
  readonly context: ApiContext;
  readonly describe: () => SessionDescription;
  readonly limits?: Partial<ConnectionLimits>;
}

/**
 * Every client currently attached to this vault.
 *
 * The connection cap lives on the server rather than here, so a seventeenth peer is
 * refused by `accept()` in libuv and never reaches a line of ours.
 */
export class Sessions {
  readonly #options: SessionsOptions;
  readonly #registry: MethodRegistry;
  readonly #connections = new Set<Connection>();

  constructor(options: SessionsOptions) {
    this.#options = options;
    // Once, not per connection: the registry is the same for every peer, and building
    // it here is what leaves no way to serve a different one.
    this.#registry = buildRegistry(options.context);
  }

  get count(): number {
    return this.#connections.size;
  }

  accept(socket: net.Socket): Connection {
    const connection = new Connection({
      socket,
      token: this.#options.token,
      registry: this.#registry,
      describe: this.#options.describe,
      ...(this.#options.limits === undefined ? {} : { limits: this.#options.limits }),
    });
    this.#connections.add(connection);
    connection.onClose(() => {
      this.#connections.delete(connection);
    });
    return connection;
  }

  /** Tell everyone why, then hang up on all of them. */
  closeAll(reason: GoodbyeReason): void {
    for (const connection of [...this.#connections]) {
      connection.goodbye(reason);
    }
    this.#connections.clear();
  }
}
