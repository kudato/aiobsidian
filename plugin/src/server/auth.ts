import { createHmac, randomBytes, timingSafeEqual } from "node:crypto";
import fs from "node:fs/promises";

import { errorCode, ServeError } from "../lib/errors.ts";

/** The shared secret, in bytes. */
const TOKEN_BYTES = 32;

/** The challenge nonce, in bytes. */
const NONCE_BYTES = 32;

/** What the token file must look like: hex, and nothing else. */
const TOKEN_TEXT = /^[0-9a-f]{64}$/;

/** Distinguishes the server's proof from the client's, so neither can replay the other. */
const SERVER_SUFFIX = Buffer.from("s", "utf8");

/**
 * Read this vault's token, creating one the first time.
 *
 * Its only job is to prove that the peer answering on the socket is this plugin. On
 * POSIX the socket's directory already decides who may connect; on Windows nothing
 * does, because libuv creates named pipes with no security descriptor and the pipe
 * namespace is global — any local account can register our name before we do, and the
 * vault id cannot detect it, since the id is part of the name being squatted. The
 * token is what a squatter does not have.
 *
 * Args:
 *     tokenFile: Where the token lives.
 *     checkMode: Whether to require `0600`. False on Windows, where the mode `lstat`
 *         reports is a fiction and the profile ACL is the real control.
 *
 * Returns:
 *     The 32 secret bytes.
 *
 * Raises:
 *     ServeError: The file exists and is readable by other accounts, holds something
 *         that is not a token, or could not be created.
 */
export async function loadOrCreateToken(tokenFile: string, checkMode: boolean): Promise<Buffer> {
  const existing = await readToken(tokenFile, checkMode);
  if (existing !== null) {
    return existing;
  }

  const token = randomBytes(TOKEN_BYTES);
  try {
    // "wx" so two windows starting at once cannot overwrite each other's secret; the
    // loser re-reads what the winner wrote.
    await fs.writeFile(tokenFile, token.toString("hex"), { encoding: "utf8", mode: 0o600, flag: "wx" });
  } catch (cause) {
    if (errorCode(cause) !== "EEXIST") {
      throw new ServeError("unsafe-directory", `cannot create the token at ${tokenFile}`, { cause });
    }
    const raced = await readToken(tokenFile, checkMode);
    if (raced === null) {
      throw new ServeError("unsafe-directory", `the token at ${tokenFile} is not readable`);
    }
    return raced;
  }
  return token;
}

/** A fresh challenge. */
export function challengeNonce(): Buffer {
  return randomBytes(NONCE_BYTES);
}

/** What the client must send to prove it can read the token. */
export function clientProof(token: Buffer, nonce: Buffer): Buffer {
  return createHmac("sha256", token).update(nonce).digest();
}

/** What the server sends back to prove the same, and that it is not a squatter. */
export function serverProof(token: Buffer, nonce: Buffer): Buffer {
  return createHmac("sha256", token).update(nonce).update(SERVER_SUFFIX).digest();
}

/**
 * Compare a proof against what it should be, in constant time.
 *
 * Args:
 *     expected: The proof computed here.
 *     offered: The hex string the peer sent.
 *
 * Returns:
 *     Whether they match. A malformed or wrong-length string is a mismatch; its length
 *     is not a secret, so failing early on it leaks nothing.
 */
export function proofMatches(expected: Buffer, offered: unknown): boolean {
  if (typeof offered !== "string" || offered.length !== expected.length * 2) {
    return false;
  }
  if (!/^[0-9a-f]+$/.test(offered)) {
    return false;
  }
  return timingSafeEqual(expected, Buffer.from(offered, "hex"));
}

/** Read the token, or `null` when there is not one yet. */
async function readToken(tokenFile: string, checkMode: boolean): Promise<Buffer | null> {
  let text: string;
  try {
    const stats = await fs.lstat(tokenFile);
    if (!stats.isFile()) {
      throw new ServeError("unsafe-directory", `${tokenFile} is not a file`);
    }
    if (checkMode && (stats.mode & 0o077) !== 0) {
      throw new ServeError(
        "unsafe-directory",
        `the token at ${tokenFile} is mode ${(stats.mode & 0o777).toString(8)}; ` +
          "other accounts on this machine can read it. Delete it and reload the plugin.",
      );
    }
    text = await fs.readFile(tokenFile, "utf8");
  } catch (cause) {
    if (cause instanceof ServeError) {
      throw cause;
    }
    if (errorCode(cause) === "ENOENT") {
      return null;
    }
    throw new ServeError("unsafe-directory", `cannot read the token at ${tokenFile}`, { cause });
  }

  const trimmed = text.trim();
  if (!TOKEN_TEXT.test(trimmed)) {
    throw new ServeError(
      "unsafe-directory",
      `the token at ${tokenFile} is not a token. Delete it and reload the plugin.`,
    );
  }
  return Buffer.from(trimmed, "hex");
}
