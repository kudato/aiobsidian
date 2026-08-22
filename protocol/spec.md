# The AIO protocol

Version 1.0.

This is what the AIO plugin speaks on its socket, and what `aiobsidian` is being built to
speak to it. It is written down so that a third implementation — another language, a
shell script, a different editor — can be written against it without reading either
side's source. Where this document uses the present tense about a client, it is stating
what a client must do, not reporting that one already does.

The machine-readable half is [`methods.json`](methods.json): every method, its
parameters, its result, its errors, and the protocol version. The plugin is tested
against that file today; the library will be as its transport lands. This document is
the part that cannot be expressed as data.

---

## 1. Transport

One vault, one socket. On macOS and Linux it is a unix domain socket; on Windows it is
a named pipe.

| | Path |
| --- | --- |
| Linux | `$XDG_RUNTIME_DIR/aiobsidian/<vault-id>.sock`, or `~/.aiobsidian/<vault-id>.sock` |
| macOS | `~/.aiobsidian/<vault-id>.sock` |
| Windows | `\\.\pipe\aiobsidian-<username>-<vault-id>` |

The containing directory is created `0700` and refused if it is not: on POSIX, the
directory is what decides who may connect at all. The socket itself is `chmod`ed to
`0600` once it is listening. Windows named pipes have no containing directory, which is
why §3 exists.

**The vault id** is the first sixteen hex characters of the SHA-256 of the vault's
path — resolved through `realpath`, NFC-normalised, lowercased on Windows only, with
trailing separators stripped. Both sides derive it independently from the same path, so
neither has to look it up. It is a **name, not a secret**: anyone who can list the
directory has it.

Obsidian's own vault ids are not reachable from the plugin API, which is why the name is
derived rather than borrowed. The only place Obsidian's id appears is the
`obsidian://open?vault=<id>` URL used to start a vault that is not running.

Several connections to one vault are normal and expected. Two scripts must both work.
Requests, subscriptions, upload handles and cancellation are all per-connection, and
none of them outlives the socket they were made on.

---

## 2. Framing

**NDJSON: one JSON object per line, LF-terminated, UTF-8.** The rules below are
normative, not stylistic.

- Exactly one message per line. Serialisers must not pretty-print.
- Empty lines are ignored, and are the resynchronisation unit.
- Note content cannot break this — every conforming JSON serialiser escapes control
  characters inside strings — but a stray debug print can, which is why it is written
  down.

A length prefix would be cheaper to parse and impossible to recover from: one bad length
and the stream is desynchronised for good. A delimiter resynchronises at the next
newline. It also means the protocol can be read and driven with `nc -U`, which is the
best debugging property this design has.

### The frame cap: 16 MiB

Enforced in both directions, by both sides, for different reasons.

**The sender checks first**, because only the sender can fail locally with a useful
message — naming the method whose answer this was, and pointing at the paged
alternative. A receiver cannot refuse what it has not yet delimited, nor name the id of
a frame it never parsed.

**The receiver's cap is normative anyway**, because "enforced by the sender" is not a
security property: a hostile peer is not *the sender*. A receiver **never retains more
than the cap while looking for a delimiter, and discards without buffering thereafter**,
then answers `messageTooLarge` and keeps the connection open. This is the only rule that
stops a peer from growing the plugin's buffer inside Obsidian's renderer with a frame
that has no newline in it.

**Large files never travel as one frame.** `files.read` and `files.write` are text only.
Binary is paged: `files.read_binary` returns one range at a time, read with a ranged
`fs.read` so the vault holds one chunk and not the file. Binary writes are transactional
— `files.upload_begin` → `files.upload_chunk`… → `files.upload_commit` — writing to a
temporary file inside the vault's config directory, under an unpredictable name, and
renaming it into place on commit. The rename is what makes the commit atomic, and it is
atomic only because both sides of it are on one filesystem, which is why the scratch file
lives there and not in the system's temporary directory.

**A handle belongs to the connection that opened it.** Closing the connection aborts
every upload open on it and deletes its scratch file, exactly as `files.upload_abort`
would have; so does unloading the plugin. Nothing survives to be resumed on a later
connection, and an abandoned upload is deleted rather than left behind. A hole in that
promise would be a growing pile of unnameable files inside the user's vault.

---

## 3. The handshake

Every connection begins the same way, and nothing else happens until it has finished.

```
vault  → {"jsonrpc":"2.0","method":"session.challenge","params":{"nonce":"<64 hex>"}}
client → {"jsonrpc":"2.0","id":1,"method":"session.hello",
          "params":{"protocol":[1],"proof":"<64 hex>"}}
vault  → {"jsonrpc":"2.0","id":1,"result":{"protocol":{"major":1,"minor":0},
          "server_proof":"<64 hex>","plugin_version":"…","obsidian_version":"…",
          "vault":{"id":"…","name":"…","path":"…"}}}
```

**`session.hello`'s request shape is frozen forever.** Version negotiation must itself be
versionless, so no future major may change what a hello looks like on the way in.

**The proof.** Each vault has a 32-byte secret, `crypto.randomBytes`, written beside the
socket at mode `0600` — `%LOCALAPPDATA%\aiobsidian\<vault-id>.token` on Windows, where
the profile ACL is the control. It is deliberately **not** in
`.obsidian/plugins/aio/data.json`: that is inside the vault, and therefore inside Sync,
iCloud, Dropbox and git.

```
proof        = HMAC-SHA256(token, nonce)
server_proof = HMAC-SHA256(token, nonce ‖ "s")
```

Both as lowercase hex, compared in constant time. The suffix is what keeps either proof
from replaying the other. **The client verifies `server_proof` before it transmits any
note content.**

**State plainly what this buys, because it is narrower than it looks.** It does not keep
out another process running as the same user: that process can read the token file, and
on POSIX it could open the `0600` socket regardless. Its one job is **server
authentication**. libuv creates named pipes with `lpSecurityAttributes = NULL`, so the
default descriptor grants read to Everyone and to anything authenticated over `IPC$`, and
the Windows pipe namespace is global and unprivileged — any local account can register
our name before we do, and the vault id cannot detect it, because the id is part of the
name being squatted. Without the proof, a client hands its requests, whole note bodies
included, to whoever got there first, and reads back content of their choosing. In a
library whose caller is often a language model, a server that chooses which notes you
read is a prompt-injection channel, not merely a confidentiality bug.

**The vault id proves nothing.** It is a component of the socket path, so anyone who can
squat that path knows it and echoes it back verbatim. Checking it is still worth doing —
it catches derivation drift and symlink surprises — but it is not a defence.

**Nothing before the handshake.** The vault answers no method but `session.hello` and
writes nothing but the challenge until a valid proof arrives. A peer that can read the
pipe but cannot prove anything harvests a nonce. This is an invariant, not an accident of
the current method list: a banner, a version string or a startup event added later would
silently turn it back into a leak.

The one thing an unproven peer can learn is which protocol majors the vault speaks,
because negotiation has to come first — a future major is free to change how the proof is
computed, and only this order can tell an outdated client so, instead of failing it with
an authentication error it cannot act on. The majors are a published constant of the
release, not a fact about the vault.

**Five seconds** to complete the handshake, or the connection is dropped. "Connected but
silent" means the wrong server.

---

## 4. Requests, responses, ordering

JSON-RPC 2.0, with three deviations, all of them narrowing:

- **`params` is always an object.** Positional parameters are refused with
  `invalidParams`. Named parameters are what let a minor add an optional one.
- **Batches are refused** with `invalidRequest`. They complicate cancellation for no gain
  on a local socket.
- **Ids are numbers or strings, never null**, and **never reused on a connection** —
  which is what makes a late response safe to discard. A client that numbers its
  requests counts up; a client that names them need only not repeat itself. Nothing on
  the vault's side orders ids, so nothing on it requires them to be orderable.

**Responses arrive in completion order, never request order.** The vault dispatches each
request as its own task, so one slow method does not hold up the ones behind it, and the
client correlates by id. Events are ordered among themselves; responses may overtake
them.

**Mutations to one path serialise** behind a per-path lock in the vault. Obsidian's
`Vault.process` protects one call's read-modify-write; it does not protect two concurrent
calls from each other.

**Bounded from the start**: sixteen connections, thirty-two requests in flight per
connection, a thirty-minute idle timeout reset by any byte in either direction, and the
five-second handshake deadline. Every request runs on the renderer's single JavaScript
thread, competing with the editor the user is typing in, so an unbounded peer is a frozen
editor. On Windows each pipe instance also reserves 64 KiB in and 64 KiB out of *nonpaged
pool*, which makes it a kernel-memory question rather than a plugin-memory one.

**What is written is bounded too, and by the same reasoning.** A peer that asks and then
stops reading is spending the vault's memory, not its own: what does not flush is held
in the renderer. So the vault **stops reading from a connection whose writes are backing
up, and closes one whose unflushed queue passes twice the frame cap**. Enforcement by
the reader is not optional here either — this is reachable before the handshake, because
a refusal is itself something to write.

---

## 5. Cancellation, and one mutation per method

### What `mutates` means

Every method in `methods.json` carries a `mutates` flag, and it decides two things: what
cancellation does to a running call, and what a broken connection says about one. So it
has to mean something exact.

> **`mutates` is true when the method changes durable state** — anything that outlives
> the connection it was changed on.

Writing a note is a mutation; so is moving the cursor, because the cursor is Obsidian's
and stays where it was put after the client that put it there has gone. So is every step
of a binary upload, including `files.upload_begin` and `files.upload_abort`: the
temporary file is a real file on disk, and a `files.upload_chunk` whose answer never
arrived may or may not have appended its bytes — which is exactly what §11 has to be able
to say.

Reading is not a mutation. Neither is **state that belongs to one connection and dies
with it**: `session.hello` authenticates that connection and no other, `events.subscribe`
and `events.unsubscribe` add and remove a subscription that closing the socket would have
removed anyway, and an upload handle names a temporary file but is itself only a name on
this connection. That is the whole exception, and it is an exception about lifetime — not
about whether some method happens to report the change.

### Cancellation

A client withdraws a request by sending `rpc.cancel` with its id. The answer still
arrives — as a `cancelled` error — so nothing waits forever. It is the client's own
withdrawal that produces it: **the vault never sends `cancelled` for a request nobody
withdrew**, so the error always lands inside the call that asked for it.

The other half of that rule binds the client, and §7 depends on it just as much:
**`rpc.cancel` is sent only when the caller's own task was cancelled.** A library that
sent it for a timeout of its own, or to tidy up, would raise `asyncio.CancelledError`
into a task nobody cancelled — a `BaseException` past every `except Exception` its caller
wrote. A client-side timeout fails with a client-side error.

The vault drops the request if it is still queued. If it is already running: reads and
queries stop at their next await point; **single mutations do not** — they run to
completion and the cancellation merely marks the answer unwanted. Chunked uploads are
cancellable between chunks, and abandoning one costs nothing.

That is affordable only because of the law below.

> **One method, one mutation.** No method may be implemented as several dependent
> mutating calls. Anything that cannot be one atomic vault call goes through a
> begin/commit handle whose commit is a rename.

This is what makes "halfway through writing a file" a state the protocol cannot express.
It is enforced in review of `methods.json`, and a proposed method that would need two
mutations is a wrong method.

So: **a cancelled mutation either applied in full or did not apply at all, at the path
it was asked about.**

The promise is about that path and no other, and it is a promise **about a file**. Two
kinds of method reach further than that, and neither can promise more:

- **A method addressing a folder** is that method repeated over a tree. Copying a folder
  is N creates, deleting one is N deletes, and `files.create_folder` is one call per
  missing level. Obsidian has no call that makes a tree atomic, so `files.copy`,
  `files.delete` and `files.create_folder` say in their own summaries that an
  interruption leaves the tree half-done. The law above is not repealed for them: each
  step is still one vault call, and there is still no half-written file.
- **`files.move`** renames one file atomically, and then Obsidian rewrites the links that
  pointed at it, note by note, on its own schedule — work that is not part of the rename
  and not something a plugin can make atomic. The move either happened or did not; a
  crash in the middle of the rewrite leaves some notes updated and some not.

Cancelled is not the same as "did not happen" — a caller that needs to know must re-read.

### Compare-and-set

`files.read` returns the content **and its hash**: SHA-256 over the exact bytes.
`files.process` takes that hash back as `expect_hash` and writes only if the file still
hashes to it, under the per-path lock; otherwise it answers `conflict` and writes
nothing.

Not size-and-mtime: a concurrent edit within the same second passes that check, and the
client silently overwrites a user's write — the precise data loss this mechanism exists
to prevent.

---

## 6. Events

`events.subscribe` takes a list of event names and returns a subscription id;
`events.unsubscribe` ends one; closing the connection ends all of them. Events arrive as
`events.event` notifications carrying the subscription id and a sequence number.

An **unknown event name is `invalidParams`**, so a typo fails at once instead of silently
delivering nothing. So is `gap`: it is the one event nobody subscribes to, and it is
`invalidParams` rather than a harmless no-op because a client that thought it had asked
for it would be a client quietly unable to hear about losing events. Every event in
`methods.json` says which it is, in `subscribable`.

`queue` bounds the subscription, and it is the one size a peer picks: between 1 and
65536, defaulting to 1024, anything else `invalidParams`. The queue is spent in
Obsidian's renderer, so it is not the peer's to make unbounded.

```
vault → {"jsonrpc":"2.0","method":"events.event",
         "params":{"subscription":"s1","seq":7,
                   "event":{"name":"file.renamed","path":"b.md","old_path":"a.md",
                            "kind":"file"}}}
```

The envelope carries `name` and nothing else of its own; the rest of the object is the
event's own fields, flattened in beside it, exactly as the table in `methods.json`
declares them. That is why **no event may have a field called `name`**. A client
dispatches on `name` and reads the rest as that event's shape.

**Backpressure.** A consumer that stops reading must not grow Obsidian's memory. Each
subscription has a bounded queue; on overflow the oldest events are dropped and a `gap`
event says how many were missed. **The gap is delivered in the stream, in order**, so the
decision to re-read state is made where the events are read.

`seq` is what makes that exact. It counts from 1 within a subscription, never repeats,
and **numbers every event the subscription produced, including the ones it dropped** — so
a jump in it is itself the news that events were lost. The `gap` event is an event like
any other and takes **the next number after the run it reports**, which is what keeps it
ordered against everything still queued behind it. Dropping 5 through 9 out of a queue
therefore reads on the wire as `…4`, then `gap` at 10 with `missed: 5`, then 11. A client
can check the count against the numbers, and the two always agree.

No debouncing. A socket handles the volume a human generates, and silently thinning a
stream is worse than reporting a gap.

Events carry **identity, never content** — paths and ids. Fetching after an event is one
cheap local call, and fat events are how the frame cap gets hit.

`unstable.raw` is the one event that rests on an Obsidian event outside its public API.
It is the only way to observe changes inside the vault's config directory — settings,
themes, plugin state — and it may vanish in any Obsidian release. The warning is in the
name the caller types.

---

## 7. Errors

Errors use the JSON-RPC error object. Reserved JSON-RPC codes keep their meanings;
ours live in the application range from 1000. The full table, with the Python exception
each code maps to, is in `methods.json`.

```json
{"jsonrpc": "2.0", "id": 7, "error": {"code": 1001, "message": "no file at projects/aio.md"}}
```

Every code maps to **exactly one** exception class on the client, so a caller branches on
a type rather than on the wording of a message. Adding a failure means adding a row to
the table, not a special case at a call site.

Several codes may share a class, but only where the caller would do the same thing about
them: `ProtocolError` covers `parseError`, `invalidRequest` and `methodNotFound` — three
ways of not speaking this protocol, with one answer to all of them. Where the answers
differ, the classes do. `messageTooLarge` has its own, because it is an ordinary outcome
with an ordinary answer — read the thing in pages — and not a sign that either side is
failing to speak the protocol. `forbidden` means a
person has to turn a switch on and no amount of retrying substitutes; `tooManyRequests`
means wait for the answers already asked for; `internalError` means file a bug. Folding
those three together would leave the two a program most needs to tell apart catchable
only alongside plugin bugs, so each has its own class.

`cancelled` maps to `asyncio.CancelledError`, which is safe only because of the rule in
§5: it answers a withdrawal the caller itself sent, and so is raised inside the call that
withdrew. A vault that sent it unbidden would be throwing a `BaseException` past every
`except Exception` a caller wrote.

`methods.json` lists per method only the errors *that method* can raise. Nine are
universal and are not repeated: `parseError`, `invalidRequest`, `methodNotFound`,
`invalidParams`, `internalError`, `unauthenticated`, `messageTooLarge`,
`tooManyRequests`, `cancelled`.

An `internalError` never carries what was actually thrown. The vault's developer console
does.

---

## 8. Versioning

The protocol version is `MAJOR.MINOR`, **independent of the plugin's version and the
library's**. It lives in `methods.json`, and the rule for every implementation is that it
is tested against that file rather than against another implementation — two sides
agreeing with each other and not with the contract is the failure this arrangement exists
to prevent. The plugin keeps that rule today; the library keeps it as its transport
lands.

A **minor** may add methods, optional parameters, result fields, event types and error
codes. It may not remove, rename or retype anything, and it may not promote an optional
parameter to a required one.

Two consequences follow, and both are rules:

- **Wire models ignore unknown fields.** A model that forbids them turns every compatible
  plugin upgrade into a client crash.
- **Both sides ignore notifications they do not recognise.**

A **major** is a break: a client that does not implement it is refused rather than served
a shape it will misread. `session.hello` offers every major the client implements and the
vault answers with the highest it shares; when there is none, `unsupportedProtocol` says
**which side to update**. Obsidian updates plugins automatically and `pip` does not, so
drift is nearly always plugin-ahead-of-library.

**Features are gated on the protocol version only**, never sniffed from the Obsidian
version.

---

## 9. Method and field naming

`domain.verb`, lowercase, dotted: `files.read`, `metadata.get`, `links.backlinks`,
`workspace.open`.

**A domain is one Python resource and one file under the plugin's `api/`, bearing the
name it has here** — one name, three places, no translation table. It is a rule for
adding a domain, kept in review; the two sides are filled in domain by domain, so the
three lists match only where a domain has actually landed on both. Method names within a
domain need not match the Python method one for one: `files.read_binary` and the upload
trio exist to serve
`files.read_binary()` and `files.write_binary()`, whose paging is the library's business
and not the caller's.

Two naming rules that decide many signatures at once:

- **Paths address files.** No method takes a wikilink-style name except `links.resolve`,
  whose whole job is names. A `path_or_name` parameter would make every method ambiguous
  and every `notFound` vague.
- **Wire fields are `snake_case`.** Obsidian's own camelCase is translated at the plugin
  boundary — `displayText` becomes `display_text`, `listItems` becomes `list_items` — so
  the client needs no aliases anywhere.

**Positions keep Obsidian's zero-based counting, untranslated.** They feed straight back
into `editor` calls, and a translation layer at the boundary is where off-by-ones live.

**`editor` targets panes, not files.** The same note open in two panes has two cursors, so
keying editor operations by path can never be truthful. Every `editor` method takes an
optional `leaf`; without one it means the active markdown editor. No editor available, or
a deferred pane that will not load, is `unavailable` — a defined failure rather than a
silent no-op.

---

## 10. Capabilities

Two capabilities, both off until the user switches them on. `app.info` reports which,
so a caller can learn what is gated without provoking a refusal; a call the switch
forbids answers `forbidden`.

**`commands`** — running an arbitrary Obsidian command is code execution by proxy. It
reaches every enabled plugin, including ones that talk to the network.

**`unstable`** — methods and events resting on undocumented Obsidian internals. The
public `App` class exposes `keymap`, `scope`, `workspace`, `vault`, `metadataCache`,
`fileManager`, `lastEvent`, `renderContext` and `secretStorage` — no `commands`, no
`plugins`, no `setting`. Anything reaching past that list may break in any Obsidian
release.

### `gated` and `gates` are different questions

`methods.json` answers both, and conflating them is how a gate ends up decorative.

**`gates`** is the list of capabilities a method may refuse on — the whole answer to
"can this method ever return `forbidden`". A method with a non-empty `gates` declares
`forbidden` among its errors, and one with an empty `gates` does not; nothing else may
raise it.

**`gated`** says the method is off in its entirety while any of those capabilities is
off. `commands.execute` is gated: without `commands` and `unstable` there is nothing it
will do. `events.subscribe` is **not** gated but still gates on `unstable` — it works
whether or not that capability is on, and refuses only the argument that needs it. So a
gated method must name what gates it, but naming a gate does not make a method gated.

**`unstable` the flag and `unstable` the gate travel together.** The flag is the
warning, the gate is the switch, and either without the other is a trap: a warning
nobody has to accept, or an acceptance nobody was warned about. `commands.*` carry both
capabilities for that reason — listing commands reads `app.commands`, which is not on
the public list above.

---

## 11. Connection lifecycle

**`session.goodbye`** is sent before a graceful close, with a reason: `stopped` when
serving was switched off, `unloading` when the plugin is going away. There are two
reasons and not three because a plugin cannot tell Obsidian quitting from the vault
closing from being disabled — all three are `onunload`, and a guess dressed up as a
reason is worse than the honest word.

**In-flight calls fail loudly and are never retried.** When a connection dies mid-call
the client cannot know whether the mutation applied — a transparent retry of
`files.append` appends twice. Every pending call raises, and for mutations the message
says plainly that the operation may or may not have landed.

**The next call reconnects.** Nothing is replayed, so re-running discovery, connect and
handshake lazily is safe: a script survives an Obsidian restart at the cost of exactly
one honest failure.

**Reconnection never launches Obsidian.** `obsidian://open` is emitted on the initial
connect only, where starting the script is the user's intent. If the user closed the
vault window, a library that re-opens it is picking a fight with the user.

Terminal, never retried: a reconnection whose handshake reports a different vault id, a
protocol major the client does not speak, or a `server_proof` that does not verify.

---

## 12. What a minimal client does

1. Derive the vault id from the vault's real path; build the socket path.
2. Connect. Read one line: `session.challenge`.
3. Read the token file; compute `HMAC-SHA256(token, nonce)`.
4. Send `session.hello` with the majors you implement and that proof.
5. Verify `server_proof` **before** sending anything else.
6. Send requests with ids you never reuse; read lines; match responses by id; treat a
   line with a `method` and no `id` as a notification.
7. On `session.goodbye`, stop; on a closed socket with pending calls, fail them.
