import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { LineReader } from "../src/protocol/framing.ts";

interface Collected {
  readonly lines: string[];
  readonly oversize: number[];
  readonly reader: LineReader;
}

function collector(maxBytes = 1024): Collected {
  const lines: string[] = [];
  const oversize: number[] = [];
  const reader = new LineReader({
    maxBytes,
    onLine: (line) => lines.push(line.toString("utf8")),
    onOversize: (bytes) => oversize.push(bytes),
  });
  return { lines, oversize, reader };
}

describe("LineReader", () => {
  it("splits on newlines", () => {
    const { lines, reader } = collector();
    reader.push(Buffer.from("one\ntwo\n"));
    assert.deepEqual(lines, ["one", "two"]);
  });

  it("joins a line split across chunks", () => {
    const { lines, reader } = collector();
    reader.push(Buffer.from("on"));
    reader.push(Buffer.from("e\nt"));
    reader.push(Buffer.from("wo\n"));
    assert.deepEqual(lines, ["one", "two"]);
  });

  it("holds an unterminated line until its newline arrives", () => {
    const { lines, reader } = collector();
    reader.push(Buffer.from("one"));
    assert.deepEqual(lines, []);
    reader.push(Buffer.from("\n"));
    assert.deepEqual(lines, ["one"]);
  });

  it("joins a character split across chunks", () => {
    const character = Buffer.from("é", "utf8");
    const { lines, reader } = collector();
    reader.push(character.subarray(0, 1));
    reader.push(character.subarray(1));
    reader.push(Buffer.from("\n"));
    assert.deepEqual(lines, ["é"]);
  });

  it("ignores empty lines, which is what makes them the resync unit", () => {
    const { lines, reader } = collector();
    reader.push(Buffer.from("\n\none\n\n"));
    assert.deepEqual(lines, ["one"]);
  });

  it("reports an oversized line once and carries on", () => {
    const { lines, oversize, reader } = collector(8);
    reader.push(Buffer.from("123456789012345\nshort\n"));
    assert.equal(oversize.length, 1);
    assert.ok(oversize[0] !== undefined && oversize[0] > 8);
    assert.deepEqual(lines, ["short"]);
  });

  it("reports an oversized line that arrives in pieces, and keeps none of it", () => {
    const { lines, oversize, reader } = collector(8);
    reader.push(Buffer.from("12345"));
    reader.push(Buffer.from("67890"));
    assert.equal(oversize.length, 1);
    assert.equal(reader.buffered, 10);
    reader.push(Buffer.from("more and more and more"));
    assert.equal(oversize.length, 1, "one report per line, however many chunks it takes");
    reader.push(Buffer.from("\nshort\n"));
    assert.deepEqual(lines, ["short"]);
  });

  it("never holds more than the cap once a line is over it", () => {
    const { reader } = collector(8);
    for (let chunk = 0; chunk < 100; chunk += 1) {
      reader.push(Buffer.alloc(1024, 0x61));
    }
    // The count keeps rising, but nothing is retained: the pieces were dropped at the
    // first overrun, which is the property that makes an endless line survivable.
    reader.push(Buffer.from("\nshort\n"));
    assert.equal(reader.buffered, 0);
  });

  it("accepts a line of exactly the cap", () => {
    const { lines, oversize, reader } = collector(8);
    reader.push(Buffer.from("12345678\n"));
    assert.deepEqual(oversize, []);
    assert.deepEqual(lines, ["12345678"]);
  });
});
