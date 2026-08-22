/**
 * Every error code the socket can answer with.
 *
 * The table is the contract. Each code maps to exactly one Python exception class, so
 * a caller branches on a type rather than on the wording of a message, and adding a
 * failure means adding a row here rather than a special case at a call site.
 *
 * JSON-RPC 2.0 reserves -32768..-32000 for itself, so ours start at 1000.
 */
export const CODES = {
  /** The line was not JSON. */
  parseError: -32700,
  /** It was JSON, but not a request. */
  invalidRequest: -32600,
  /** No such method. */
  methodNotFound: -32601,
  /** The method exists; these arguments do not fit it. */
  invalidParams: -32602,
  /** A bug on this side. */
  internalError: -32603,

  /** A file, command, leaf or id that is not there. */
  notFound: 1001,
  /** Creating something that already exists. */
  alreadyExists: 1002,
  /** A compare-and-set lost its race. */
  conflict: 1003,
  /** The right request in the wrong app state: no active editor, a deferred leaf. */
  unavailable: 1004,
  /** A method arrived before a valid handshake, or the proof did not match. */
  unauthenticated: 1005,
  /** No protocol major in common. */
  unsupportedProtocol: 1006,
  /** The capability this method needs is switched off. */
  forbidden: 1007,
  /** A line longer than the frame cap. */
  messageTooLarge: 1008,
  /** Too many requests in flight on this connection. */
  tooManyRequests: 1009,
  /** The client withdrew the request before it finished. */
  cancelled: 1010,
} as const;

export type Code = (typeof CODES)[keyof typeof CODES];

/** A failure that is the caller's answer, not a crash. */
export class RpcError extends Error {
  readonly code: Code;
  readonly data: unknown;

  constructor(code: Code, message: string, data?: unknown) {
    super(message);
    this.name = "RpcError";
    this.code = code;
    this.data = data;
  }
}
