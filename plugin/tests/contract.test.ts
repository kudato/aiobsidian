/**
 * The plugin against the contract.
 *
 * `protocol/methods.json` is the shared file, so nothing here restates what it says —
 * these tests read it and check that the plugin agrees. A method registered but not in
 * the contract is undocumented; a live method in the contract but not registered is a
 * promise the plugin does not keep. Both are failures here rather than at a caller.
 */

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";

import type { App } from "obsidian";

import { buildRegistry } from "../src/api/index.ts";
import { CODES } from "../src/protocol/codes.ts";
import { MAX_MESSAGE_BYTES } from "../src/protocol/framing.ts";
import { PROTOCOL_MAJOR, PROTOCOL_MINOR, SUPPORTED_MAJORS } from "../src/protocol/version.ts";
import { DEFAULT_LIMITS } from "../src/server/connection.ts";
import { MAX_CONNECTIONS } from "../src/server/socket.ts";
import { DEFAULT_SETTINGS } from "../src/settings.ts";

interface Contract {
  readonly protocol: { readonly major: number; readonly minor: number };
  readonly errors: Record<string, { readonly code: number }>;
  readonly methods: Record<string, { readonly status: string; readonly domain: string }>;
  readonly notifications: Record<string, { readonly status: string }>;
}

/** A source file split into the part that runs and the strings it holds. */
interface Source {
  readonly file: string;
  /** The file with every comment blanked out, so a grep cannot match one. */
  readonly code: string;
  /** The contents of every string and template literal in it. */
  readonly literals: readonly string[];
}

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.join(here, "..", "..");
const contract = JSON.parse(
  await fs.readFile(path.join(root, "protocol", "methods.json"), "utf8"),
) as Contract;
const sources = await readSources(path.join(root, "plugin", "src"));

/**
 * Read one TypeScript file the way a grep over it ought to see it.
 *
 * A test that greps raw source is a test a comment can satisfy — and one a comment can
 * also break, by mentioning a name the code never sends. So the file is walked once,
 * comments are replaced by spaces (offsets stay put, and nothing accidentally joins),
 * and every string literal is collected separately.
 */
function scan(text: string): { code: string; literals: string[] } {
  const code: string[] = [];
  const literals: string[] = [];
  let index = 0;
  while (index < text.length) {
    const two = text.slice(index, index + 2);
    if (two === "//") {
      const end = text.indexOf("\n", index);
      const stop = end === -1 ? text.length : end;
      code.push(" ".repeat(stop - index));
      index = stop;
      continue;
    }
    if (two === "/*") {
      const end = text.indexOf("*/", index + 2);
      const stop = end === -1 ? text.length : end + 2;
      code.push(text.slice(index, stop).replace(/[^\n]/g, " "));
      index = stop;
      continue;
    }
    const quote = text[index];
    if (quote === '"' || quote === "'" || quote === "`") {
      const start = index;
      let literal = "";
      index += 1;
      while (index < text.length && text[index] !== quote) {
        if (text[index] === "\\") {
          literal += text[index + 1] ?? "";
          index += 2;
          continue;
        }
        literal += text[index];
        index += 1;
      }
      index += 1;
      literals.push(literal);
      code.push(text.slice(start, index));
      continue;
    }
    code.push(text[index] as string);
    index += 1;
  }
  return { code: code.join(""), literals };
}

/** Every `.ts` file under a directory, scanned. */
async function readSources(directory: string): Promise<Source[]> {
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const found: Source[] = [];
  for (const entry of entries) {
    const full = path.join(directory, entry.name);
    if (entry.isDirectory()) {
      found.push(...(await readSources(full)));
    } else if (entry.name.endsWith(".ts")) {
      const { code, literals } = scan(await fs.readFile(full, "utf8"));
      found.push({ file: path.relative(root, full), code, literals });
    }
  }
  return found;
}

function source(relative: string): Source {
  const found = sources.find((candidate) => candidate.file === relative);
  assert.ok(found, `${relative} is not there any more; this test is about it`);
  return found;
}

/**
 * Everything the plugin should have in its registry.
 *
 * The `session` domain is not in it: the connection answers `session.hello` itself,
 * before there is an authenticated session to dispatch on.
 */
function expectedMethods(): string[] {
  return Object.entries(contract.methods)
    .filter(([, method]) => method.status === "live" && method.domain !== "session")
    .map(([name]) => name)
    .sort();
}

describe("the plugin against protocol/methods.json", () => {
  it("speaks the version the contract names", () => {
    assert.equal(PROTOCOL_MAJOR, contract.protocol.major);
    assert.equal(PROTOCOL_MINOR, contract.protocol.minor);
  });

  it("still speaks the major it ships", () => {
    assert.ok(SUPPORTED_MAJORS.includes(PROTOCOL_MAJOR));
  });

  it("uses exactly the error codes the contract defines", () => {
    const fromContract = Object.fromEntries(
      Object.entries(contract.errors).map(([name, error]) => [name, error.code]),
    );
    assert.deepEqual({ ...CODES }, fromContract);
  });

  it("registers exactly the methods the contract calls live", () => {
    // The registry the server is actually given, not one assembled here to match: a
    // method registered and undocumented has to fail, and it cannot if the test builds
    // its own.
    const registry = buildRegistry({ app: {} as App, settings: () => DEFAULT_SETTINGS });
    assert.deepEqual(registry.names(), expectedMethods());
  });

  it("hands out a registry nothing can add to afterwards", () => {
    // The check above compares a registry built here against the contract, and the one
    // the plugin serves is built the same way — which makes the two the same set only
    // while neither can be added to after it is built.
    const registry = buildRegistry({ app: {} as App, settings: () => DEFAULT_SETTINGS });
    assert.throws(
      () => {
        registry.add("files.sneaky", () => null);
      },
      /sealed/,
      "a method could be served without the contract ever hearing of it",
    );
  });

  it("builds its registry in exactly one place", () => {
    // And that place is the one the test above calls. Anywhere else and the comparison
    // is against a registry nothing serves.
    const builders = sources
      .filter((candidate) => candidate.code.includes("new MethodRegistry("))
      .map((candidate) => candidate.file);
    assert.deepEqual(builders, [path.join("plugin", "src", "api", "index.ts")]);
    assert.match(source(path.join("plugin", "src", "main.ts")).code, /buildRegistry\(/);
  });

  it("names every notification the contract calls live", () => {
    // Nothing dispatches these through a registry, so the names live in the source as
    // string literals. Reading them out of it is what makes a rename on one side fail
    // here rather than at a client. Only literals count: a comment naming one proves
    // nothing, and blanking comments out is what keeps it from proving anything.
    const live = Object.entries(contract.notifications)
      .filter(([, notification]) => notification.status === "live")
      .map(([name]) => name)
      .sort();
    const known = new Set(Object.keys(contract.notifications));
    const spoken = new Set(
      sources.flatMap((candidate) => candidate.literals).filter((text) => known.has(text)),
    );
    assert.deepEqual([...spoken].sort(), live);
  });

  it("caps a frame at the 16 MiB the specification names", () => {
    assert.equal(MAX_MESSAGE_BYTES, 16 * 1024 * 1024);
    assert.equal(DEFAULT_LIMITS.maxMessageBytes, MAX_MESSAGE_BYTES);
  });

  it("holds to the bounds the specification names", () => {
    assert.equal(MAX_CONNECTIONS, 16);
    assert.equal(DEFAULT_LIMITS.maxInFlight, 32);
    assert.equal(DEFAULT_LIMITS.handshakeTimeoutMs, 5_000);
    assert.equal(DEFAULT_LIMITS.idleTimeoutMs, 30 * 60_000);
    assert.equal(DEFAULT_LIMITS.maxQueuedBytes, 2 * MAX_MESSAGE_BYTES);
  });
});
