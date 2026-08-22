import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { after, describe, it } from "node:test";

import { ServeError } from "../src/lib/errors.ts";
import { ensureRuntimeDirectory } from "../src/server/directory.ts";

const scratch = await fs.mkdtemp(path.join(os.tmpdir(), "aio-dir-"));

after(async () => {
  await fs.rm(scratch, { recursive: true, force: true });
});

let counter = 0;

/** A path inside the scratch directory that nothing has created yet. */
function fresh(): string {
  counter += 1;
  return path.join(scratch, `case-${counter}`);
}

/** Run the check and hand back the refusal, or `null` when it accepted. */
async function refusal(directory: string): Promise<ServeError | null> {
  try {
    await ensureRuntimeDirectory(directory);
    return null;
  } catch (error) {
    assert.ok(error instanceof ServeError);
    return error;
  }
}

describe("ensureRuntimeDirectory", { skip: process.platform === "win32" }, () => {
  it("creates the directory closed to everyone else", async () => {
    const directory = fresh();
    assert.equal(await refusal(directory), null);
    const stats = await fs.lstat(directory);
    assert.equal(stats.mode & 0o777, 0o700);
  });

  it("accepts a directory that is already there and already private", async () => {
    const directory = fresh();
    await fs.mkdir(directory, { mode: 0o700 });
    assert.equal(await refusal(directory), null);
  });

  it("refuses a directory other accounts can traverse", async () => {
    const directory = fresh();
    await fs.mkdir(directory);
    await fs.chmod(directory, 0o755);
    const error = await refusal(directory);
    assert.equal(error?.code, "unsafe-directory");
    assert.match(error?.message ?? "", /755/);
  });

  it("refuses a group-writable directory", async () => {
    const directory = fresh();
    await fs.mkdir(directory);
    await fs.chmod(directory, 0o770);
    assert.equal((await refusal(directory))?.code, "unsafe-directory");
  });

  it("refuses a symlink, which is someone else's directory wearing our name", async () => {
    const target = fresh();
    await fs.mkdir(target, { mode: 0o700 });
    const link = fresh();
    await fs.symlink(target, link);
    assert.equal((await refusal(link))?.code, "unsafe-directory");
  });

  it("refuses a file", async () => {
    const file = fresh();
    await fs.writeFile(file, "");
    assert.equal((await refusal(file))?.code, "unsafe-directory");
  });
});
