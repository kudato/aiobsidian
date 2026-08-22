/**
 * NDJSON framing: one JSON object per line, LF-terminated, UTF-8.
 *
 * A length prefix would be cheaper to parse and impossible to recover from — one bad
 * length and the stream is desynchronised for good. A delimiter resynchronises at the
 * next newline, which is what makes the frame cap survivable: an oversized line is
 * discarded and the connection carries on.
 */

/** The largest line either side will send or accept, in bytes. */
export const MAX_MESSAGE_BYTES = 16 * 1024 * 1024;

/** The line delimiter. */
const LF = 0x0a;

export interface LineReaderOptions {
  /** The cap on one line, not counting the delimiter. */
  readonly maxBytes: number;
  /** Called once per complete, non-empty line. */
  readonly onLine: (line: Buffer) => void;
  /** Called once per line that went over the cap, with the bytes seen so far. */
  readonly onOversize: (bytes: number) => void;
}

/**
 * Turns a byte stream into lines without ever holding more than the cap.
 *
 * The cap is what makes this safe against a peer that never sends a newline: past the
 * limit the bytes are counted and dropped rather than buffered, so an unbounded write
 * costs the receiver nothing but the reading. Enforcement by the sender is not a
 * security property — a hostile peer is not the sender.
 */
export class LineReader {
  readonly #options: LineReaderOptions;
  #pieces: Buffer[] = [];
  #length = 0;
  /** Past the cap on the current line: count the rest, keep none of it. */
  #discarding = false;

  constructor(options: LineReaderOptions) {
    this.#options = options;
  }

  /** Bytes held for the line being assembled. */
  get buffered(): number {
    return this.#length;
  }

  push(chunk: Buffer): void {
    let start = 0;
    for (;;) {
      const delimiter = chunk.indexOf(LF, start);

      if (delimiter === -1) {
        const rest = chunk.length - start;
        if (this.#discarding) {
          this.#length += rest;
          return;
        }
        if (this.#length + rest > this.#options.maxBytes) {
          this.#length += rest;
          this.#options.onOversize(this.#length);
          this.#pieces = [];
          this.#discarding = true;
          return;
        }
        if (rest > 0) {
          this.#pieces.push(chunk.subarray(start));
          this.#length += rest;
        }
        return;
      }

      const piece = chunk.subarray(start, delimiter);
      start = delimiter + 1;

      if (this.#discarding) {
        // The oversized line has ended; the next one starts clean.
        this.#reset();
        continue;
      }

      if (this.#length + piece.length > this.#options.maxBytes) {
        this.#length += piece.length;
        this.#options.onOversize(this.#length);
        this.#reset();
        continue;
      }

      const line =
        this.#pieces.length === 0
          ? piece
          : Buffer.concat([...this.#pieces, piece], this.#length + piece.length);
      this.#reset();
      // Empty lines are ignored, which is what makes them the resync unit.
      if (line.length > 0) {
        this.#options.onLine(line);
      }
    }
  }

  #reset(): void {
    this.#pieces = [];
    this.#length = 0;
    this.#discarding = false;
  }
}
