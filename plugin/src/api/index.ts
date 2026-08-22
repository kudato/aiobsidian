/**
 * Every domain, registered in one place.
 *
 * This exists so there is exactly one answer to "what does the plugin serve". `main.ts`
 * calls it to build the registry it serves from, and `tests/contract.test.ts` calls the
 * same function to compare that registry against `protocol/methods.json`. Two
 * constructions would let a method be registered and undocumented at the same time,
 * with the test agreeing that all is well — which is why the registry is sealed on the
 * way out and why the same test refuses a `new MethodRegistry()` anywhere but here.
 *
 * The `api/` files are the domains, one file each, named exactly as the contract names
 * them — which is the rule `protocol/spec.md` §9 states and this directory keeps.
 *
 * A domain that needs a *value* out of `obsidian` — `TFile` to test with `instanceof`,
 * `normalizePath` — cannot simply import it: the `obsidian` package ships types and no
 * implementation, so `node --test` would fail on the import and the tempting fix is to
 * register that domain somewhere this file cannot see. It is the wrong fix. The right
 * one is a loader shim for the tests; registration stays here.
 */

import type { App } from "obsidian";

import { MethodRegistry } from "../server/registry.ts";
import type { Settings } from "../settings.ts";

/** What every domain is built against. */
export interface ApiContext {
  readonly app: App;
  /**
   * Read afresh on every call, never captured.
   *
   * The capability switches live in here, and a user who turns one off in the settings
   * tab expects the next call to be refused — not the next Obsidian restart.
   */
  readonly settings: () => Settings;
}

/**
 * Build the registry the plugin serves from.
 *
 * Args:
 *     _context: What the domains are built against. Nothing reads it until the first
 *         domain lands; it is threaded now so that landing one is adding a file rather
 *         than changing this signature and everything that calls it.
 *
 * Returns:
 *     A sealed registry holding every method this plugin answers. `session.*` and
 *     `rpc.*` are not among them: the connection answers those itself, before there is
 *     a session to dispatch on.
 */
export function buildRegistry(_context: ApiContext): MethodRegistry {
  const methods = new MethodRegistry();
  // Domains register here as they land. Until then it is empty, and the contract test
  // is what says so out loud rather than letting it pass unnoticed.
  methods.seal();
  return methods;
}
