import { CODES, type Code } from "./codes.ts";

/** What a request id may be. Whatever arrives is echoed back unchanged. */
export type RequestId = number | string;

export interface RpcRequest {
  readonly id: RequestId;
  readonly method: string;
  readonly params: Record<string, unknown>;
}

export interface RpcNotification {
  readonly method: string;
  readonly params: Record<string, unknown>;
}

export type Inbound =
  | { readonly kind: "request"; readonly request: RpcRequest }
  | { readonly kind: "notification"; readonly notification: RpcNotification }
  | {
      readonly kind: "invalid";
      /** The id to answer with, when one could be recovered. */
      readonly id: RequestId | null;
      readonly code: Code;
      readonly message: string;
    };

/**
 * Read one parsed line as a JSON-RPC message.
 *
 * Args:
 *     value: The result of `JSON.parse` on one line.
 *
 * Returns:
 *     A request, a notification, or the refusal to answer with.
 */
export function readMessage(value: unknown): Inbound {
  if (Array.isArray(value)) {
    return invalid(null, CODES.invalidRequest, "batches are not supported; send one object per line");
  }
  if (typeof value !== "object" || value === null) {
    return invalid(null, CODES.invalidRequest, "a message must be a JSON object");
  }

  const message = value as Record<string, unknown>;
  const id = readId(message["id"]);

  if (message["jsonrpc"] !== "2.0") {
    return invalid(id, CODES.invalidRequest, 'every message must carry "jsonrpc": "2.0"');
  }

  const method = message["method"];
  if (typeof method !== "string" || method.length === 0) {
    return invalid(id, CODES.invalidRequest, "a message must carry a method name");
  }

  const rawParams = message["params"];
  if (rawParams !== undefined && (typeof rawParams !== "object" || rawParams === null)) {
    return invalid(id, CODES.invalidParams, "params must be an object");
  }
  if (Array.isArray(rawParams)) {
    return invalid(id, CODES.invalidParams, "params are named, never positional");
  }
  const params = (rawParams ?? {}) as Record<string, unknown>;

  if (id === null) {
    if ("id" in message && message["id"] !== undefined) {
      return invalid(null, CODES.invalidRequest, "an id must be a number or a string");
    }
    return { kind: "notification", notification: { method, params } };
  }
  return { kind: "request", request: { id, method, params } };
}

function readId(value: unknown): RequestId | null {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return value;
  }
  return null;
}

function invalid(id: RequestId | null, code: Code, message: string): Inbound {
  return { kind: "invalid", id, code, message };
}
