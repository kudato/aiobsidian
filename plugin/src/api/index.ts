/**
 * Every domain, registered in one place.
 *
 * This exists so there is exactly one answer to "what does the plugin serve". `Sessions`
 * calls it and takes no registry of its own, so there is no way to hand the server a
 * different method set; the registry is sealed on the way out, so there is no way to
 * add to the one it gets. What the contract test compares against
 * `protocol/methods.json` is neither of those, though — it is `Connection.answers`, read
 * off a connection the plugin built, because a registry compared with itself agrees
 * with itself and says nothing about what a peer can reach.
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
 * **Registration is unconditional.** Every domain registers every one of its methods,
 * whatever the context says — a capability that is off, an Obsidian internal that is
 * missing, a vault of the wrong kind. Those are answered inside the method, with
 * `forbidden` or `unavailable`, which is what the contract promises a caller. A method
 * registered only when some condition holds is a method the contract test cannot see,
 * because the test's context is a stub and every such condition takes its off-branch —
 * and gated domains are exactly where that shape is tempting.
 *
 * Args:
 *     _context: What the domains are built against. Nothing reads it until the first
 *         domain lands; it is threaded now so that landing one is adding a file rather
 *         than changing this signature and everything that calls it. When one does read
 *         it, it reads it inside a method and not around a registration.
 *
 * Returns:
 *     A sealed registry holding every method this plugin answers except the ones the
 *     connection answers itself, before there is a session to dispatch on.
 */
export function buildRegistry(_context: ApiContext): MethodRegistry {
  const methods = new MethodRegistry();
  // Domains register here as they land. Until then it is empty, and the contract test
  // is what says so out loud rather than letting it pass unnoticed.
  methods.seal();
  return methods;
}
