import { createHash } from "node:crypto";
import os from "node:os";
import path from "node:path";

import { ServeError } from "./errors.ts";

/** The id is the front of a hash, so it is lowercase hex and it is fixed width. */
const VAULT_ID_PATTERN = /^[0-9a-f]{16}$/;

/** How many hex characters of the digest name the vault. */
const VAULT_ID_LENGTH = 16;

/**
 * The longest socket path each platform accepts.
 *
 * `sockaddr_un.sun_path` is 104 bytes on Darwin and 108 on Linux, one of which is the
 * terminator. Over the limit, `bind()` fails with an error naming neither the path nor
 * the limit, so the check happens here where both are known.
 */
const SUN_PATH_LIMIT: Record<string, number> = { darwin: 103, linux: 107 };

/** Windows pipe names are a flat namespace; keep the parts that name a pipe safely. */
const UNSAFE_IN_PIPE_NAME = /[^A-Za-z0-9._-]/g;

/** Everything about the machine the paths are derived from, so tests can supply it. */
export interface Environment {
  readonly platform: string;
  readonly home: string;
  readonly username: string;
  readonly variables: Readonly<Record<string, string | undefined>>;
}

/** The environment this process is actually running in. */
export function currentEnvironment(): Environment {
  return {
    platform: process.platform,
    home: os.homedir(),
    username: os.userInfo().username,
    variables: process.env,
  };
}

/**
 * Name a vault by its location on disk.
 *
 * Obsidian's own registry ids are not reachable from the plugin API, and the client
 * has to arrive at the same name from the outside, so the name is derived instead of
 * looked up: the vault's real path, NFC-normalised, hashed, and truncated. The hash is
 * not a secret — it is a stable name that does not put the user's directory layout
 * into a path other local processes can list.
 *
 * Args:
 *     vaultPath: The vault's base directory, already resolved through `realpath`.
 *     platform: The platform whose path rules apply.
 *
 * Returns:
 *     Sixteen lowercase hex characters.
 */
export function vaultId(vaultPath: string, platform: string): string {
  let normalised = vaultPath.normalize("NFC");
  // Windows paths are case-insensitive, so two spellings of one vault must not produce
  // two names. Elsewhere a volume may well be case-sensitive, and folding would merge
  // vaults that really are distinct.
  if (platform === "win32") {
    normalised = normalised.toLowerCase();
  }
  normalised = stripTrailingSeparators(normalised);
  return createHash("sha256").update(normalised, "utf8").digest("hex").slice(0, VAULT_ID_LENGTH);
}

/**
 * Reject anything that is not a vault id before it reaches a path.
 *
 * Raises:
 *     ServeError: The id is not sixteen lowercase hex characters.
 */
export function assertVaultId(id: string): void {
  if (!VAULT_ID_PATTERN.test(id)) {
    throw new ServeError("listen-failed", `${JSON.stringify(id)} is not a vault id`);
  }
}

/**
 * The directory holding this user's sockets, or `null` on Windows, whose pipe
 * namespace has no containing directory to protect.
 *
 * On Linux `$XDG_RUNTIME_DIR` is already a private tmpfs cleared at logout, which is
 * exactly what is wanted. macOS has no equivalent, and the home directory itself is
 * group `staff` — every local account — so the sockets get a directory of their own.
 */
export function runtimeDirectory(environment: Environment): string | null {
  if (environment.platform === "win32") {
    return null;
  }
  const xdg = environment.variables["XDG_RUNTIME_DIR"];
  if (environment.platform === "linux" && xdg !== undefined && xdg !== "") {
    return path.posix.join(xdg, "aiobsidian");
  }
  return path.posix.join(environment.home, ".aiobsidian");
}

/**
 * Where this vault listens.
 *
 * Args:
 *     environment: The machine the path is derived for.
 *     id: The vault id, as returned by `vaultId`.
 *
 * Returns:
 *     A unix socket path, or a Windows pipe name.
 *
 * Raises:
 *     ServeError: The id is malformed, or the path is longer than `sun_path` holds.
 */
export function socketPath(environment: Environment, id: string): string {
  assertVaultId(id);
  if (environment.platform === "win32") {
    const user = environment.username.replace(UNSAFE_IN_PIPE_NAME, "_");
    return `\\\\.\\pipe\\aiobsidian-${user}-${id}`;
  }
  const directory = runtimeDirectory(environment);
  if (directory === null) {
    throw new ServeError("unsupported-platform", `no socket directory for ${environment.platform}`);
  }
  const socket = path.posix.join(directory, `${id}.sock`);
  const limit = SUN_PATH_LIMIT[environment.platform] ?? 103;
  const length = Buffer.byteLength(socket, "utf8");
  if (length > limit) {
    throw new ServeError(
      "path-too-long",
      `the socket path is ${length} bytes and this platform accepts ${limit}: ${socket}`,
    );
  }
  return socket;
}

/**
 * Where this vault's shared secret is kept.
 *
 * Beside the socket on POSIX, in the verified `0700` directory. On Windows the pipe
 * has no containing directory, so the token goes under the user profile, whose ACL is
 * the control there. Never inside the vault: `.obsidian/` is inside Sync, iCloud,
 * Dropbox and git.
 *
 * Args:
 *     environment: The machine the path is derived for.
 *     id: The vault id, as returned by `vaultId`.
 *
 * Raises:
 *     ServeError: The id is malformed.
 */
export function tokenPath(environment: Environment, id: string): string {
  assertVaultId(id);
  if (environment.platform === "win32") {
    // The separators follow the platform the path is *for*, not the one this process
    // runs on, so the same environment always derives the same path.
    const local =
      environment.variables["LOCALAPPDATA"] ?? path.win32.join(environment.home, "AppData", "Local");
    return path.win32.join(local, "aiobsidian", `${id}.token`);
  }
  const directory = runtimeDirectory(environment);
  if (directory === null) {
    throw new ServeError("unsupported-platform", `no token directory for ${environment.platform}`);
  }
  return path.posix.join(directory, `${id}.token`);
}

/** Drop trailing separators, except the one that makes a path a root. */
function stripTrailingSeparators(value: string): string {
  let end = value.length;
  while (end > 1 && (value[end - 1] === "/" || value[end - 1] === "\\")) {
    end -= 1;
  }
  const stripped = value.slice(0, end);
  return /^[A-Za-z]:$/.test(stripped) ? `${stripped}\\` : stripped;
}
