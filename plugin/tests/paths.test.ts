import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { ServeError } from "../src/lib/errors.ts";
import {
  assertVaultId,
  type Environment,
  runtimeDirectory,
  socketPath,
  tokenPath,
  vaultId,
} from "../src/lib/paths.ts";

function environment(overrides: Partial<Environment> = {}): Environment {
  return {
    platform: "darwin",
    home: "/Users/ada",
    username: "ada",
    variables: {},
    ...overrides,
  };
}

describe("vaultId", () => {
  it("is sixteen lowercase hex characters", () => {
    assert.match(vaultId("/Users/ada/Notes", "darwin"), /^[0-9a-f]{16}$/);
  });

  it("is stable for the same path", () => {
    assert.equal(vaultId("/Users/ada/Notes", "darwin"), vaultId("/Users/ada/Notes", "darwin"));
  });

  it("differs between vaults", () => {
    assert.notEqual(vaultId("/Users/ada/Notes", "darwin"), vaultId("/Users/ada/Other", "darwin"));
  });

  it("ignores unicode normal form", () => {
    // macOS hands back decomposed names; Python resolves to whatever it was given.
    assert.equal(vaultId("/Users/ada/Café", "darwin"), vaultId("/Users/ada/Cafe\u0301", "darwin"));
  });

  it("ignores a trailing separator", () => {
    assert.equal(vaultId("/Users/ada/Notes/", "darwin"), vaultId("/Users/ada/Notes", "darwin"));
  });

  it("folds case on Windows, where two spellings are one directory", () => {
    assert.equal(vaultId("C:\\Users\\Ada\\Notes", "win32"), vaultId("c:\\users\\ada\\notes", "win32"));
  });

  it("keeps case elsewhere, where two spellings can be two directories", () => {
    assert.notEqual(vaultId("/Users/ada/Notes", "linux"), vaultId("/users/ada/notes", "linux"));
  });

  it("keeps the separator that makes a path a root", () => {
    assert.notEqual(vaultId("/", "linux"), vaultId("", "linux"));
  });
});

describe("assertVaultId", () => {
  it("accepts what vaultId produces", () => {
    assert.doesNotThrow(() => {
      assertVaultId(vaultId("/Users/ada/Notes", "darwin"));
    });
  });

  for (const bad of ["", "../../etc", "0123456789ABCDEF", "0123456789abcde", "0123456789abcdef0"]) {
    it(`rejects ${JSON.stringify(bad)}`, () => {
      assert.throws(() => {
        assertVaultId(bad);
      }, ServeError);
    });
  }
});

describe("runtimeDirectory", () => {
  it("uses the XDG runtime directory on Linux", () => {
    const where = runtimeDirectory(
      environment({ platform: "linux", variables: { XDG_RUNTIME_DIR: "/run/user/1000" } }),
    );
    assert.equal(where, "/run/user/1000/aiobsidian");
  });

  it("falls back to the home directory when Linux has no XDG runtime directory", () => {
    assert.equal(runtimeDirectory(environment({ platform: "linux" })), "/Users/ada/.aiobsidian");
  });

  it("ignores the XDG runtime directory on macOS", () => {
    const where = runtimeDirectory(
      environment({ variables: { XDG_RUNTIME_DIR: "/run/user/1000" } }),
    );
    assert.equal(where, "/Users/ada/.aiobsidian");
  });

  it("has nothing to protect on Windows", () => {
    assert.equal(runtimeDirectory(environment({ platform: "win32" })), null);
  });
});

describe("socketPath", () => {
  const id = "0123456789abcdef";

  it("names a socket inside the runtime directory", () => {
    assert.equal(socketPath(environment(), id), `/Users/ada/.aiobsidian/${id}.sock`);
  });

  it("names a pipe on Windows", () => {
    const where = socketPath(environment({ platform: "win32" }), id);
    assert.equal(where, `\\\\.\\pipe\\aiobsidian-ada-${id}`);
  });

  it("keeps a domain account from breaking out of the pipe name", () => {
    const where = socketPath(environment({ platform: "win32", username: "CORP\\ada" }), id);
    assert.equal(where, `\\\\.\\pipe\\aiobsidian-CORP_ada-${id}`);
  });

  it("refuses an id that is not one", () => {
    assert.throws(() => socketPath(environment(), "../../../tmp/x"), ServeError);
  });

  it("says so when the path is longer than sun_path holds", () => {
    const home = `/Users/${"a".repeat(90)}`;
    let caught: unknown;
    try {
      socketPath(environment({ home }), id);
    } catch (error) {
      caught = error;
    }
    assert.ok(caught instanceof ServeError);
    assert.equal(caught.code, "path-too-long");
    assert.match(caught.message, /103/);
  });

  it("allows a longer path on Linux, which allows a longer sun_path", () => {
    // 104 bytes: over Darwin's 103, under Linux's 107.
    const home = `/home/${"a".repeat(64)}`;
    assert.doesNotThrow(() => socketPath(environment({ platform: "linux", home }), id));
    assert.throws(() => socketPath(environment({ platform: "darwin", home }), id), ServeError);
  });
});

describe("tokenPath", () => {
  const id = "0123456789abcdef";

  it("keeps the token beside the socket", () => {
    assert.equal(tokenPath(environment(), id), `/Users/ada/.aiobsidian/${id}.token`);
  });

  it("follows the socket into the XDG runtime directory", () => {
    const where = environment({ platform: "linux", variables: { XDG_RUNTIME_DIR: "/run/user/501" } });
    assert.equal(tokenPath(where, id), `/run/user/501/aiobsidian/${id}.token`);
  });

  it("keeps it under the profile on Windows, where the pipe has no directory", () => {
    const where = environment({
      platform: "win32",
      home: "C:\\Users\\ada",
      variables: { LOCALAPPDATA: "C:\\Users\\ada\\AppData\\Local" },
    });
    assert.equal(tokenPath(where, id), `C:\\Users\\ada\\AppData\\Local\\aiobsidian\\${id}.token`);
  });

  it("finds the profile on Windows without the variable", () => {
    const where = environment({ platform: "win32", home: "C:\\Users\\ada" });
    assert.equal(tokenPath(where, id), `C:\\Users\\ada\\AppData\\Local\\aiobsidian\\${id}.token`);
  });

  it("refuses an id that is not one, so nothing writes outside the directory", () => {
    assert.throws(() => tokenPath(environment(), "../../../tmp/x"), ServeError);
  });

  it("is not the socket, so neither can be mistaken for the other", () => {
    assert.notEqual(tokenPath(environment(), id), socketPath(environment(), id));
  });
});
