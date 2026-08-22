/**
 * Why the plugin refused to serve.
 *
 * The code is what the user interface branches on; the message is what it shows.
 */
export type ServeErrorCode =
  /** Not a real filesystem — a mobile or in-memory adapter. */
  | "unsupported-platform"
  /** The socket path is longer than `sun_path` holds. */
  | "path-too-long"
  /** The runtime directory exists but belongs to someone else, or is readable by them. */
  | "unsafe-directory"
  /** Something is already listening on the name. */
  | "address-in-use"
  /** Anything else `listen()` reported. */
  | "listen-failed";

/** A refusal to serve, carrying a reason the status item can render. */
export class ServeError extends Error {
  readonly code: ServeErrorCode;

  constructor(code: ServeErrorCode, message: string, options?: { cause?: unknown }) {
    super(message, options);
    this.name = "ServeError";
    this.code = code;
  }
}

/** The `code` Node puts on a system error, when there is one. */
export function errorCode(error: unknown): string | undefined {
  if (typeof error === "object" && error !== null && "code" in error) {
    const code = (error as { code: unknown }).code;
    if (typeof code === "string") {
      return code;
    }
  }
  return undefined;
}
