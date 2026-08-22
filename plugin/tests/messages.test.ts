import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { CODES } from "../src/protocol/codes.ts";
import { readMessage } from "../src/protocol/messages.ts";

describe("readMessage", () => {
  it("reads a request", () => {
    const message = readMessage({
      jsonrpc: "2.0",
      id: 7,
      method: "files.read",
      params: { path: "a.md" },
    });
    assert.deepEqual(message, {
      kind: "request",
      request: { id: 7, method: "files.read", params: { path: "a.md" } },
    });
  });

  it("reads a string id, and hands it back untouched", () => {
    const message = readMessage({ jsonrpc: "2.0", id: "abc", method: "x" });
    assert.equal(message.kind === "request" && message.request.id, "abc");
  });

  it("defaults missing params to an empty object", () => {
    const message = readMessage({ jsonrpc: "2.0", id: 1, method: "x" });
    assert.deepEqual(message.kind === "request" ? message.request.params : null, {});
  });

  it("reads a notification as one, not as a request with no id", () => {
    const message = readMessage({ jsonrpc: "2.0", method: "rpc.cancel", params: { id: 3 } });
    assert.deepEqual(message, {
      kind: "notification",
      notification: { method: "rpc.cancel", params: { id: 3 } },
    });
  });

  it("refuses a batch, and says what to send instead", () => {
    const message = readMessage([{ jsonrpc: "2.0", id: 1, method: "x" }]);
    assert.equal(message.kind === "invalid" && message.code, CODES.invalidRequest);
    assert.match(message.kind === "invalid" ? message.message : "", /one object per line/);
  });

  for (const value of [null, 7, "hello", true]) {
    it(`refuses ${JSON.stringify(value)}, which is not a message`, () => {
      const message = readMessage(value);
      assert.equal(message.kind === "invalid" && message.code, CODES.invalidRequest);
    });
  }

  it("refuses a message without the version", () => {
    const message = readMessage({ id: 1, method: "x" });
    assert.equal(message.kind === "invalid" && message.code, CODES.invalidRequest);
  });

  it("answers a versionless message on its own id, so the caller can match it up", () => {
    const message = readMessage({ id: 42, method: "x" });
    assert.equal(message.kind === "invalid" && message.id, 42);
  });

  it("refuses a message without a method", () => {
    const message = readMessage({ jsonrpc: "2.0", id: 1 });
    assert.equal(message.kind === "invalid" && message.code, CODES.invalidRequest);
  });

  it("refuses positional params", () => {
    const message = readMessage({ jsonrpc: "2.0", id: 1, method: "x", params: ["a.md"] });
    assert.equal(message.kind === "invalid" && message.code, CODES.invalidParams);
    assert.match(message.kind === "invalid" ? message.message : "", /never positional/);
  });

  it("refuses params that are not an object", () => {
    const message = readMessage({ jsonrpc: "2.0", id: 1, method: "x", params: "a.md" });
    assert.equal(message.kind === "invalid" && message.code, CODES.invalidParams);
  });

  it("refuses an id that is neither a number nor a string", () => {
    const message = readMessage({ jsonrpc: "2.0", id: {}, method: "x" });
    assert.equal(message.kind === "invalid" && message.code, CODES.invalidRequest);
  });

  it("refuses a null id rather than reading it as a notification", () => {
    const message = readMessage({ jsonrpc: "2.0", id: null, method: "x" });
    assert.equal(message.kind, "invalid");
  });
});
