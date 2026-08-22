import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { after, describe, it } from "node:test";

import { ServeError } from "../src/lib/errors.ts";
import {
  challengeNonce,
  clientProof,
  loadOrCreateToken,
  proofMatches,
  serverProof,
} from "../src/server/auth.ts";

const scratch = await fs.mkdtemp(path.join(os.tmpdir(), "aio-auth-"));
await fs.chmod(scratch, 0o700);

after(async () => {
  await fs.rm(scratch, { recursive: true, force: true });
});

let counter = 0;

function fresh(): string {
  counter += 1;
  return path.join(scratch, `case-${counter}.token`);
}

async function refusal(tokenFile: string, checkMode = true): Promise<ServeError> {
  try {
    await loadOrCreateToken(tokenFile, checkMode);
  } catch (error) {
    assert.ok(error instanceof ServeError);
    return error;
  }
  return assert.fail("the token was accepted when it should have been refused");
}

describe("loadOrCreateToken", { skip: process.platform === "win32" }, () => {
  it("creates a token no other account can read", async () => {
    const tokenFile = fresh();
    const token = await loadOrCreateToken(tokenFile, true);
    assert.equal(token.length, 32);
    assert.equal((await fs.lstat(tokenFile)).mode & 0o777, 0o600);
  });

  it("returns the same token next time", async () => {
    const tokenFile = fresh();
    const first = await loadOrCreateToken(tokenFile, true);
    const second = await loadOrCreateToken(tokenFile, true);
    assert.deepEqual(first, second);
  });

  it("writes it as hex and nothing else", async () => {
    const tokenFile = fresh();
    const token = await loadOrCreateToken(tokenFile, true);
    assert.equal(await fs.readFile(tokenFile, "utf8"), token.toString("hex"));
  });

  it("refuses a token other accounts can read", async () => {
    const tokenFile = fresh();
    await loadOrCreateToken(tokenFile, true);
    await fs.chmod(tokenFile, 0o644);
    assert.match((await refusal(tokenFile)).message, /644/);
  });

  it("reads a world-readable token where the mode means nothing, as on Windows", async () => {
    const tokenFile = fresh();
    const token = await loadOrCreateToken(tokenFile, true);
    await fs.chmod(tokenFile, 0o644);
    assert.deepEqual(await loadOrCreateToken(tokenFile, false), token);
  });

  it("refuses a file that is not a token rather than trusting it", async () => {
    const tokenFile = fresh();
    await fs.writeFile(tokenFile, "hunter2", { mode: 0o600 });
    assert.match((await refusal(tokenFile)).message, /not a token/);
  });

  it("refuses a token that is too short to be one", async () => {
    const tokenFile = fresh();
    await fs.writeFile(tokenFile, "abcdef", { mode: 0o600 });
    assert.match((await refusal(tokenFile)).message, /not a token/);
  });

  it("tolerates a trailing newline, which any editor will add", async () => {
    const tokenFile = fresh();
    const hex = "a".repeat(64);
    await fs.writeFile(tokenFile, `${hex}\n`, { mode: 0o600 });
    assert.equal((await loadOrCreateToken(tokenFile, true)).toString("hex"), hex);
  });

  it("refuses a directory in the token's place", async () => {
    const tokenFile = fresh();
    await fs.mkdir(tokenFile);
    assert.match((await refusal(tokenFile)).message, /not a file/);
  });
});

describe("proofs", () => {
  const token = Buffer.alloc(32, 7);
  const nonce = Buffer.alloc(32, 9);

  it("the two proofs of one nonce are different, so neither replays the other", () => {
    assert.notDeepEqual(clientProof(token, nonce), serverProof(token, nonce));
  });

  it("a different token proves nothing", () => {
    assert.notDeepEqual(clientProof(token, nonce), clientProof(Buffer.alloc(32, 8), nonce));
  });

  it("a different nonce proves nothing", () => {
    assert.notDeepEqual(clientProof(token, nonce), clientProof(token, Buffer.alloc(32, 10)));
  });

  it("accepts the proof it expects", () => {
    assert.equal(proofMatches(clientProof(token, nonce), clientProof(token, nonce).toString("hex")), true);
  });

  for (const offered of [
    undefined,
    null,
    42,
    "",
    "not hex at all",
    "A".repeat(64),
    "a".repeat(63),
    "a".repeat(65),
  ]) {
    it(`refuses ${JSON.stringify(offered)}`, () => {
      assert.equal(proofMatches(clientProof(token, nonce), offered), false);
    });
  }

  it("a nonce is 32 bytes and never the same twice", () => {
    const first = challengeNonce();
    assert.equal(first.length, 32);
    assert.notDeepEqual(first, challengeNonce());
  });
});
