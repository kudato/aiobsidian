import type net from "node:net";

import {
  Connection,
  type ConnectionLimits,
  type GoodbyeReason,
  type SessionDescription,
} from "./connection.ts";
import type { MethodRegistry } from "./registry.ts";

export interface SessionsOptions {
  readonly token: Buffer;
  readonly registry: MethodRegistry;
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
  readonly #connections = new Set<Connection>();

  constructor(options: SessionsOptions) {
    this.#options = options;
  }

  get count(): number {
    return this.#connections.size;
  }

  accept(socket: net.Socket): Connection {
    const connection = new Connection({
      socket,
      token: this.#options.token,
      registry: this.#options.registry,
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
