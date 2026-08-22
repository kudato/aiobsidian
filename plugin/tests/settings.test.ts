import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { DEFAULT_SETTINGS, parseSettings } from "../src/settings.ts";

describe("parseSettings", () => {
  it("serves by default, because serving is the whole plugin", () => {
    assert.equal(DEFAULT_SETTINGS.serve, true);
  });

  it("keeps a stored choice", () => {
    assert.deepEqual(parseSettings({ serve: false }), { serve: false });
  });

  it("falls back to the default for anything that is not settings", () => {
    for (const data of [null, undefined, 7, "serve", [], { serve: "yes" }, {}]) {
      assert.deepEqual(parseSettings(data), DEFAULT_SETTINGS);
    }
  });

  it("drops keys it does not know", () => {
    assert.deepEqual(parseSettings({ serve: false, port: 27123 }), { serve: false });
  });
});
