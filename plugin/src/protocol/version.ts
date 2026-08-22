/**
 * The protocol major this plugin speaks.
 *
 * A major is a break: a client that does not implement it is refused rather than
 * served a shape it will misread. Minors are additive and need no negotiation.
 */
export const PROTOCOL_MAJOR = 1;

/** The revision within the major. Additive only. */
export const PROTOCOL_MINOR = 0;

/** Every major this plugin can still speak, newest first. */
export const SUPPORTED_MAJORS: readonly number[] = [PROTOCOL_MAJOR];

/**
 * The highest major both sides implement.
 *
 * Args:
 *     offered: The majors the client says it implements.
 *
 * Returns:
 *     The major to speak, or `null` when there is no overlap.
 */
export function negotiate(offered: readonly number[]): number | null {
  let best: number | null = null;
  for (const major of offered) {
    if (SUPPORTED_MAJORS.includes(major) && (best === null || major > best)) {
      best = major;
    }
  }
  return best;
}
