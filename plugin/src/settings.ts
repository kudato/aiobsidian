/** Everything the plugin remembers between loads. */
export interface Settings {
  /**
   * Hold the socket.
   *
   * On, because serving the vault is the only thing this plugin does; a plugin that
   * has to be enabled twice is a plugin that looks broken. What is gated is authority,
   * not the listener — see the capability settings that arrive with the domains that
   * need them.
   */
  serve: boolean;
}

export const DEFAULT_SETTINGS: Settings = { serve: true };

/**
 * Read settings back from disk without trusting their shape.
 *
 * `loadData()` returns whatever JSON is in `data.json`, which a user, a sync
 * conflict or an older version may have left in any state.
 *
 * Args:
 *     data: The value `loadData()` returned.
 *
 * Returns:
 *     Settings, with anything missing or mistyped replaced by its default.
 */
export function parseSettings(data: unknown): Settings {
  const raw: Record<string, unknown> =
    typeof data === "object" && data !== null ? (data as Record<string, unknown>) : {};
  const serve = raw["serve"];
  return { serve: typeof serve === "boolean" ? serve : DEFAULT_SETTINGS.serve };
}
