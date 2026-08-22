import { CODES, RpcError } from "../protocol/codes.ts";

/** What a method is handed besides its parameters. */
export interface CallContext {
  /** Send a notification down the connection the call arrived on. */
  readonly notify: (method: string, params: Record<string, unknown>) => void;
  /**
   * Aborts when the caller withdraws the request or the connection dies.
   *
   * A method that can run long must observe it and stop: until it settles, its id
   * holds one of the connection's in-flight slots and the caller has no answer.
   *
   * A listener on this signal must not throw. It is called synchronously from the
   * socket's own handler, inside Obsidian's renderer, and Node turns a throwing abort
   * listener into an uncaught exception — which ends the user's application rather
   * than the request. Fail by resolving or rejecting the method instead.
   */
  readonly signal: AbortSignal;
}

export type Method = (
  params: Record<string, unknown>,
  context: CallContext,
) => Promise<unknown> | unknown;

/**
 * The methods this plugin answers to.
 *
 * Domains register into one registry so the dispatcher never grows a switch, and so
 * the set of live methods is a value that can be listed, tested and written to the
 * protocol contract rather than read out of control flow.
 */
export class MethodRegistry {
  readonly #methods = new Map<string, Method>();
  #sealed = false;

  /**
   * Refuse every later registration, and every later change to this object.
   *
   * A registration the contract test cannot see is a method served and undocumented,
   * so `add` stops working. `Object.freeze` is the other half: without it the object
   * accepts a replacement `get`, which would serve a method the name list never
   * mentions — sealed registration and an unsealed object is a promise only half kept.
   */
  seal(): void {
    this.#sealed = true;
    Object.freeze(this);
  }

  /**
   * Raises:
   *     Error: The name is already taken. Two domains claiming one name is a bug that
   *         must not resolve itself by silently picking a winner.
   *     Error: The registry is sealed. Registering outside `buildRegistry()` would put
   *         a method on the wire that no test compares against the contract.
   */
  add(name: string, method: Method): void {
    if (this.#sealed) {
      throw new Error(
        `the method ${name} is registered after the registry was sealed; ` +
          "every method belongs in buildRegistry(), which is what the contract is tested against",
      );
    }
    if (this.#methods.has(name)) {
      throw new Error(`the method ${name} is registered twice`);
    }
    this.#methods.set(name, method);
  }

  /**
   * Raises:
   *     RpcError: No method by that name.
   */
  get(name: string): Method {
    const method = this.#methods.get(name);
    if (method === undefined) {
      throw new RpcError(CODES.methodNotFound, `no method named ${name}`);
    }
    return method;
  }

  has(name: string): boolean {
    return this.#methods.has(name);
  }

  names(): string[] {
    return [...this.#methods.keys()].sort();
  }
}
