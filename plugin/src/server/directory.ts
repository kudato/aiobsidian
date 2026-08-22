import fs from "node:fs/promises";

import { ServeError } from "../lib/errors.ts";

/** Bits that must not be set: anything granting group or other. */
const SHARED_BITS = 0o077;

/**
 * Create the runtime directory if it is missing, then prove it is ours.
 *
 * Creating it proves nothing on its own: `mkdir` masks the requested mode with the
 * umask, and it succeeds quietly when the directory already exists with any owner and
 * any mode. Nor is the socket's own mode the control — `listen()` creates the socket
 * under the umask, and it is already accepting connections before `chmod` runs. The
 * directory is what stands between another local account and this vault, so every load
 * checks that it is a directory, that this user owns it, and that nobody else can
 * traverse it.
 *
 * Args:
 *     directory: The directory sockets are created in.
 *
 * Raises:
 *     ServeError: The directory belongs to another user, is reachable by other
 *         accounts, is not a directory, or could not be created.
 */
export async function ensureRuntimeDirectory(directory: string): Promise<void> {
  try {
    await fs.mkdir(directory, { recursive: true, mode: 0o700 });
  } catch (cause) {
    throw new ServeError("unsafe-directory", `cannot create ${directory}`, { cause });
  }

  // `lstat`, not `stat`: a symlink pointing at a directory someone else owns passes
  // every check that follows the link.
  let stats;
  try {
    stats = await fs.lstat(directory);
  } catch (cause) {
    throw new ServeError("unsafe-directory", `cannot read ${directory}`, { cause });
  }

  if (!stats.isDirectory()) {
    throw new ServeError("unsafe-directory", `${directory} is not a directory`);
  }

  const uid = process.getuid?.();
  if (uid !== undefined && stats.uid !== uid) {
    throw new ServeError(
      "unsafe-directory",
      `${directory} belongs to uid ${stats.uid}, not to you (uid ${uid})`,
    );
  }

  const shared = stats.mode & SHARED_BITS;
  if (shared !== 0) {
    throw new ServeError(
      "unsafe-directory",
      `${directory} is mode ${(stats.mode & 0o777).toString(8)}; other accounts on this machine can reach it. ` +
        "Run chmod 700 on it, or remove it and reload the plugin.",
    );
  }
}
