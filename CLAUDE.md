# Project Jessie — n8n build

Slack bot that books studio time for Hit Productions. Moved out of a chat session into
this folder on 2026-08-30 so the workflows have version history and n8n's API is reachable
without export/import cycles.

## Ground rules

- **Before editing any file or pushing to n8n:** show Tara the change and wait for an
  explicit yes.
- **Pull before you change anything.** The n8n UI and this folder overwrite each other
  silently.
- **Run `./scripts/check-fromai` on every build.** An unescaped apostrophe in a `$fromAI`
  description takes the whole agent down, and it fails at runtime, not on save. That has
  happened.
- **After changing any tool's inputs, toggle the workflow Active off and on.** Saving does
  not reload tool definitions — the agent keeps calling the old schema, and the execution
  shows the old input names. Several test results were misread because of this.
- **The API key lives in `.env` only.** Never in a message, a commit, or a shared file.
- Bookings in the live calendar are real. QA runs on year-shifted dates (2027) on purpose —
  the prompt adds a year to today, so "next Thursday" resolves to 2027.

## The stack

```
Slack DM → n8n → agent (Gemini 3.5 Flash Lite, temp 0.2) → Airtable + Google Calendar → Slack
```

| Workflow | id | What it is |
|---|---|---|
| `Project Jessie` | `uVVYVB2M7kxpLleI` | main, 32 nodes + 7 sticky notes |
| `Jessie — Book Session` | `EUG3sGXkfsJSYIMz` | the only way a booking is created |
| `Jessie — Cancel Booking` | `bAyDw7udhmY0NL38` | the only way one is deleted |
| `Jessie — Room Availability` | `e7tBQB458nstrqei` | what is free, computed not reasoned |

Airtable base `app8GQxEInqJi1NRP` · calendar `c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com`
· launch 2026-09-25.

People: Tara — Strategic Lead. Howard — dev. Tel — knowledge base. Trish, Camy, Jess, bp — QA.

Versions in `workflows/` are a local convention, not n8n's. The live build is the highest
numbered file that was imported and confirmed — check with `./scripts/n8n pull` rather than
assuming.

## The one principle

Everything that must be true is enforced in a sub-workflow. Everything the prompt merely
asks for is unreliable.

That is not a design preference, it is what a night of testing showed: every rule stated in
the prompt failed at least once — the conflict check, waiting for confirmation, the room
ranking, checking availability before summarising, even the rule against `**`. Every rule
moved into n8n has held on every run since.

So: if it must be true, put it in `Check Conflicts` or a guard. If Jessie needs to know it,
inject it as data the way the room ranking and session-type list are injected. Only tone,
phrasing and judgement belong in the prompt.

## What is enforced, and where

`Book Session` refuses in this order, before anything reaches the calendar:

```
MISSING_DETAILS        a partial tool call - answered, not crashed
NOT_CONFIRMED          no approved summary in Slack for this booking
DURATION_OUT_OF_RANGE  outside the session type's Min/Max      (overridable)
ROOM_UNSUITABLE        that session type is not run in that room (overridable)
ROOM_NOT_PRIORITY      a last-resort room while priority rooms are free (overridable)
NO_ROOM / UNKNOWN_ROOM
ROOM_OCCUPIED          the conflict check
UNVERIFIABLE           an event in the window whose room cannot be identified
```

The three overridable ones refuse once so the requester hears the standard, then allow it
when they say to go ahead. `duration_override` and `room_override` are model-supplied and
therefore soft; `confirmed` is not.

**The confirmation gate.** `Gate Context` reads Slack history and computes `confirmed`,
`confirmedCancel` and the memory `epoch`. The model supplies no part of them. Because
`Send Reply` runs after the agent, a summary written this turn is not in Slack yet, so a
same-turn booking cannot pass. A reply only counts as approval if it is not itself a fresh
instruction.

**Cancellation.** `Cancel Booking` fetches the event from Google and reads the booker
reference off the real record. The model supplies only an event id.

**Memory.** The session key carries an epoch that advances when a booking completes, so the
next request cannot inherit the last one's client or session type. A bare `reset` clears it
on demand.

**Formatting.** `Guard Probe` collapses `**` to `*` on the way out — Slack renders double
asterisks literally and the model emits them regardless of the prompt.

## Reference data — read it, don't restate it

Do not trust any list of rooms, session types or capabilities written down in a document,
including this one. Several have been wrong. Read Airtable.

What is already injected into the prompt on every message, from `Room Table`: the
Priority/Last Resort room ranking per session type, the full session-type list, and a
department-flavoured suggestion list for the booker.

Known contradictions in Rooms & Studios, and which field Jessie trusts:

- **Format questions read `Recording Format`.** `Room Type` marks nine rooms as `5.1 Mixing`
  including two whose own Equipment says "stereo only".
- **`Vocal Booth` is the flag, not the `Recording Booth` room type.** They cover different
  rooms.
- **`Room Requirements` is a capability string** like "Stereo Mixing", not a room list. The
  ranking is the room list.
- `Clients.Preferred Rooms` returns record ids and is no longer sent to the agent at all.
  See PENDING.md.

## Waiting on other systems

[PENDING.md](PENDING.md) — nine items needing a change in Airtable, the Slack app or the n8n
server. Each says how it was found and what it breaks.

## Gotchas that already cost time

1. A `throw` inside an **optional** collection like `additionalFields` does not fail the
   node — n8n drops the field. Guards only work in required top-level fields.
2. Never put a fan-out node in the agent's main chain without collapsing back to one item.
3. `$('Node').first()`, never `$('Node').item`.
4. A node chained after a multi-item node runs once per item. That is what made the conflict
   query fire 25 times and take 11 seconds. Use `executeOnce`.
5. Duplicate `$fromAI` keys in one node with different descriptions kill the agent on every
   message. `Search Events for Deletion` declares `booking_date` twice — identical text, so
   legal. Edit one copy and not the other and it breaks.
6. The prompt must not demonstrate what it forbids. Models copy context over instructions
   about context.

## Not done

- The two guards proven only in unit tests, never in a real conversation: `ROOM_OCCUPIED`
  reaching the agent, and `Cancel Booking` refusing someone else's booking.
- No test harness. Prompt changes are still shipped on a single run, which is how several
  regressions reached Tara.
- Titles are still composed by the model; a wrong project title produces a wrong calendar
  title silently.
- Nothing prevents booking in the past. The old `Create Event` had that guard and the
  sub-workflow does not.

## Related

`../Projects/haist/` holds the HAIST programme docs. `HANDOFF.md` here is the 2026-08-30
handoff, kept for its design intent — but it has been wrong on the session type count and
name, on what `Room Requirements` means, and on the `.item` conversion being finished. Check
anything factual in it against the live workflow before acting on it.
