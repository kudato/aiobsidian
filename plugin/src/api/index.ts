/**
 * Every domain, registered in one place.
 *
 * This exists so there is exactly one answer to "what does the plugin serve". `main.ts`
 * calls it to build the registry it serves from, and `tests/contract.test.ts` calls the
 * same function to compare that registry against `protocol/methods.json`. Two
 * constructions would let a method be registered and undocumented at the same time,
 * with the test agreeing that all is well.
 *
 * The `api/` files are the domains, one file each, named exactly as the contract names
 * them — which is the rule `protocol/spec.md` §9 states and this directory keeps.
 */

import { MethodRegistry } from "../server/registry.ts";

/**
 * Build the registry the plugin serves from.
 *
 * Returns:
 *     A registry holding every method this plugin answers. `session.*` and `rpc.*` are
 *     not among them: the connection answers those itself, before there is a session to
 *     dispatch on.
 */
export function buildRegistry(): MethodRegistry {
  const methods = new MethodRegistry();
  // Domains register here as they land. Until then it is empty, and the contract test
  // is what says so out loud rather than letting it pass unnoticed.
  return methods;
}
