# Project Jessie — n8n build

Slack bot that books studio time for Hit Productions. Moved out of a chat session into
this folder on 2026-08-30 so the workflows have version history and n8n's API is reachable
without export/import cycles.

## Ground rules

- **Before editing any file or pushing to n8n:** show Tara the change and wait for an
  explicit yes.
- **Pull before you change anything.** The n8n UI and this folder overwrite each other
  silently. Tara rearranges the canvas; a file built from a stale pull reverts her layout.
- **Build every file from a fresh pull and keep the full export shape.** Do not strip the
  file down to `name/nodes/connections/settings` — Tara imports these by hand and wants
  what n8n exports.
- **Run `./scripts/check-fromai` on every build.** An unescaped apostrophe in a `$fromAI`
  description takes the whole agent down, and it fails at runtime, not on save.
- **Run `./scripts/test-nodes` before shipping anything.** It runs every Code node that
  decides something — `Guard Probe`, `Check Conflicts`, `Check Ownership`, `Shape Results` —
  against a table of scenarios offline, then delegates to `./scripts/test-gate` for
  `Gate Context`. 58 checks. `--live` tests what is actually deployed; four explicit paths
  test a candidate before importing it. Every one of those nodes shipped a bug this weekend
  that was caught by reading output by hand.
- `Gate Context` is the one node every message passes through, so a scope or syntax error
  there takes Jessie down completely rather than degrading one feature. That has happened
  twice.
- **After changing any tool's inputs, or adding/removing a tool, toggle Active off and on.**
  Saving does not reload tool definitions — the agent keeps calling the old schema.
- **The API key lives in `.env` only.** Never in a message, a commit, or a shared file.
- Bookings in the live calendar are real. QA runs on year-shifted dates (2027) on purpose.

## The stack

```
Slack DM → n8n → agent (Gemini 3.5 Flash Lite, temp 0.2) → Airtable + Google Calendar → Slack
```

| Workflow | id | What it is |
|---|---|---|
| `Project Jessie v2` | `uVVYVB2M7kxpLleI` | main, 40 nodes including 7 lane notes |
| `Jessie — Book Session` | `EUG3sGXkfsJSYIMz` | the only way a booking is created |
| `Jessie — Cancel Booking` | `bAyDw7udhmY0NL38` | the only way one is deleted |
| `Jessie — Move Booking` | `t7lwR2km4tfN8DbM` | the only way one is rescheduled |
| `Jessie — Find Booking` | `yzirq12O227VTFp8` | shapes a day's events before the model sees them |
| `Jessie — Room Availability` | `e7tBQB458nstrqei` | what is free, computed not reasoned |

Airtable base `app8GQxEInqJi1NRP` · calendar `c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com`
· launch 2026-09-25.

People: Tara — Strategic Lead. Howard — dev. Tel — knowledge base. Trish, Camy, Jess, bp — QA.

Versions in `workflows/` are a local convention, not n8n's. The live build is whatever was
last imported and confirmed — check with `./scripts/n8n pull` rather than assuming.

## The one principle

Everything that must be true is enforced in a sub-workflow. Everything the prompt merely
asks for is unreliable.

That is not a design preference, it is what testing showed: every rule stated in the prompt
failed at least once — the conflict check, waiting for confirmation, the room ranking,
checking availability before summarising, even the rule against `**`. Every rule moved into
n8n has held on every run since.

A third place now does real work: **`Guard Probe`**, which rewrites the reply on the way out.
Use it for anything that must be true of the *text* rather than the action. It already
collapses `**` to `*`, corrects the weekday printed beside a date, removes the words
"priority room" and "last resort", and normalises the confirmation marker. Each of those was
a prompt rule first, and each failed as a prompt rule.

## What is enforced, and where

`Book Session` refuses before anything reaches the calendar:

```
MISSING_DETAILS · NO_REFERENCE_DATA · PAST_DATE · NOT_CONFIRMED · DURATION_INVALID
ROOM_UNSUITABLE · ROOM_NOT_PRIORITY · NO_ROOM · UNKNOWN_ROOM · ROOM_OCCUPIED · UNVERIFIABLE
```

`Cancel Booking` refuses with:

```
NOT_CONFIRMED · MISSING_DATE · MISSING_DETAILS · LOOKUP_FAILED
NOT_ON_CALENDAR · AMBIGUOUS_TITLE · NO_REFERENCE · NOT_YOURS
```

`Move Booking` refuses with the same ownership and confirmation checks plus
`MISSING_TIMES`, `DURATION_INVALID`, `ROOM_OCCUPIED`, and returns `PARTIAL` if the
replacement was created but the original could not be removed.

**The confirmation gate.** `Gate Context` reads Slack history and computes `confirmed`,
`confirmedCancel`, `confirmedMove` and the memory `epoch`. The model supplies no part of
them. Because `Send Reply` runs after the agent, a summary written this turn is not in
Slack yet, so a same-turn booking cannot pass. Approval must be an explicit yes — a literal
match against a fixed set. Before v81 any reply at all counted, including "no".

**Markers.** Summaries end `Confirm to book. (yes/no)`, `Confirm to cancel. (yes/no)` or
`Confirm to move. (yes/no)`. The gate matches the marker at the end of the message, so
`Guard Probe` normalises whatever the model writes — "Confirm to cancel both." broke the
gate before it did. The gate accepts the older `(y/n)` suffix too, because old messages sit
in the history window it reads.

**Rescheduling.** `Move Booking` does the whole move in one call and one confirmation, and
creates the replacement **before** deleting the original, so a failure leaves the booking
where it was. The old flow deleted first and needed a second yes to recreate — walk away in
between and the session was gone.

**Cancellation.** `Cancel Booking` fetches the event from Google and reads the booker
reference off the real record. The booking is resolved by the title shown to the requester,
so the model never has to hold or invent an event id.

**Memory.** The session key is `user-date-epoch`. Only a typed `reset` advances the epoch;
it also rolls over at midnight Manila. A completed booking used to advance it, which meant
"actually cancel that" had nothing to refer to.

## Reference data — read it, don't restate it

Do not trust any list of rooms, session types or capabilities written down in a document,
including this one. Several have been wrong. Read Airtable.

Injected into the prompt on every message by `Room Table`: the room ranking per session
type, the full session-type list, the room list, and a department-flavoured suggestion list.

Known contradictions in Rooms & Studios, and which field Jessie trusts:

- **Format questions read `Recording Format`.** `Room Type` marks nine rooms as `5.1 Mixing`
  including two whose own Equipment says "stereo only".
- **`Vocal Booth` is the flag, not the `Recording Booth` room type.**
- **`Room Requirements` is a capability string**, not a room list. The ranking is the list.
- `Clients.Preferred Rooms` returns record ids and is not sent to the agent. See PENDING.

## Before launch

`YEAR_SHIFT` at the top of `Gate Context` and the `plus({ years: 1 })` in the system prompt
are the QA year shift. **They must go to zero together.** Change one and the model and the
guards will disagree about what day it is — which decides what "next Thursday" means and
whether a date is in the past.

## Waiting on other systems

[PENDING.md](PENDING.md) — needs a change in Airtable, the Slack app, Google Calendar or the
n8n server. Each says how it was found and what it breaks.

## Gotchas that already cost time

1. A `throw` inside an **optional** collection like `additionalFields` does not fail the
   node — n8n drops the field. Guards only work in required top-level fields.
2. Never put a fan-out node in the agent's main chain without collapsing back to one item.
3. `$('Node').first()`, never `$('Node').item`.
4. A node chained after a multi-item node runs once per item. That is what made the conflict
   query fire 25 times and take 11 seconds. Use `executeOnce`.
5. Duplicate `$fromAI` keys in one node with different descriptions kill the agent on every
   message.
6. The prompt must not demonstrate what it forbids. Models copy context over instructions.
7. **An empty value in an Airtable formula matches every row.** `SEARCH(LOWER(''), ...)` is
   true for everything: a booking was once assembled from a stranger's client record. Every
   lookup now refuses rather than returning a table.
8. **A pulled file carries an `activeVersion` block** — n8n's snapshot of the *previous*
   version. Grep will find stale names and values in it. Check the nodes, not the whole file.
9. **Renaming a tool leaves dangling references** in the prompt, other tool descriptions and
   the sticky notes. Search for the old name everywhere before shipping.
10. `./scripts/n8n push` has reported success and changed nothing. Import by hand and verify
    with a pull.

## Not done

- `NOT_YOURS` — refusing to cancel a booking someone else made through Jessie — is still
  unproven in a live conversation, because every booking so far was made by one person.
  `ROOM_OCCUPIED` and `NO_REFERENCE` have both now fired for real.
- Titles are composed by the model; a wrong project title becomes a wrong calendar title.
- She still sometimes presents a summary without checking availability that turn. The guard
  catches it; the prompt rule does not.
- She sometimes asks for a date already given, and has invented a justification for a room
  choice. Both are free-text failures with nothing binding them to a source.
- QA groups: B, C, D, F, M, N, X done. The rest have not been run.

## Related

`../Projects/haist/` holds the HAIST programme docs. `HANDOFF.md` here is the 2026-08-30
handoff, kept for its design intent — but it has been wrong on several facts. Check anything
in it against the live workflow before acting on it.
