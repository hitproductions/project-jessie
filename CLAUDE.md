# Project Jessie — n8n build

Slack bot that books studio time for Hit Productions. Moved out of a chat session into
this folder on 2026-08-30 so the workflows have real version history and so n8n's API
is reachable without export/import cycles.

## Ground rules

- **Before editing any file or pushing to n8n:** show Tara the change and wait for an
  explicit yes. Same rule as the rest of HAIST.
- **Never push to a workflow without pulling first.** The UI and this folder can diverge
  silently; a push overwrites whatever was changed in the browser since the last pull.
- **The API key lives in `.env` only.** Never in a message, a commit, or a file that gets
  shared.
- Bookings in the live calendar are real. QA runs on year-shifted dates (2027) on purpose.

## The stack

```
Slack DM → n8n → AI agent (Gemini 3.5 Flash Lite, temp 0.2) → Airtable reads + Google Calendar writes → Slack reply
```

| Thing | Value |
|---|---|
| n8n | `https://signal.hitpromanila.net` |
| Main workflow | `Project Jessie` — id `uVVYVB2M7kxpLleI`, live and active |
| Sub-workflow | `Jessie — Book Session` — id `EUG3sGXkfsJSYIMz`, tested, **not wired to the agent yet** |
| Airtable base | `app8GQxEInqJi1NRP` — Project Jessie Knowledge Base |
| Calendar | `c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com` — KDC Bookings |
| Model | `models/gemini-3.5-flash-lite`, temperature 0.2 |
| Launch | 2026-09-25 |

People: Tara — Strategic Lead. Howard — dev. Tel — knowledge base. Trish, Camy, Jess, bp — QA.

v22–v36 are a local numbering convention from the chat session, not n8n's. v36 is the last
version imported and confirmed working, and `workflows/project-jessie-v36.json` is the
source of truth for what is running.

## Next up, in order

1. **Wire Book Session to the agent** — full spec in HANDOFF.md §4. A Call n8n Workflow
   Tool node with seven `$fromAI` inputs, plus prompt surgery to delete the conflict-check
   and post-create sections the sub-workflow now owns. Disable the old `Create Event`
   rather than deleting it.
2. **Rebuild the confirmation gate** — HANDOFF.md §8, and read "What the logs settled"
   below first. The gate itself was never the problem and was never actually tested.
3. Everything else is in HANDOFF.md §9, including three decisions that are Tara's to make.
   The Slack Trigger scoping (§9.4) is lower priority than the handoff implies — see below.

## What the logs settled — 2026-08-30

First reading of real execution data, from execution `2048` (the v28 run) and `2045`/`2046`
(v27). HANDOFF.md §8 predates this and is wrong on the cause; §8 carries a pointer here.

**The v27–v29 failures were a duplicate `$fromAI` key, not the gate.**

```
Jessie AI Agent: 1 item(s) ERROR
    message: Duplicate key 'Rooms' found with different description or type
    from   : Create Event
```

`Create Event` called `$fromAI('Rooms', …)` twice with two different descriptions. n8n builds
the tool schema before the model is called, so the agent node threw on every message
regardless of content, returned nothing, and Slack rejected the empty text as `no_text`.

Consequences for the plan:

- `Gate Context` worked. Execution 2048 shows 6 items in, 1 item out, no error — v28's
  collapse fix did its job. The gate design is **untested, not disproven**. A fourth attempt
  is worth making.
- v29's "the fallback fires on every message" was the symptom of the same error, not
  evidence against a retry loop. There was never a retry loop.
- v27 had two independent faults: the fan-out (`Get Recent Messages: 6 → agent: 6 items`)
  *and* the duplicate key. Fixing the first in v28 only exposed the second.
- v36 has the duplicate gone and the last eight live runs show no agent error.

**Landmine.** v36's `Search Events for Deletion` still calls `$fromAI('booking_date', …)`
twice. It is legal only because the two copies are character-identical. Edit one and not the
other and the same failure comes back. Check every tool node's `$fromAI` keys for collisions
before and after any change that adds tool inputs — Book Session adds seven.

**Execution volume is about 107/day**, not thousands: 250 runs from Aug 27 09:24Z to Aug 29
17:21Z, 245 success, 4 error, 1 canceled. §9.4 is tidying, not an emergency, and scoping the
trigger wrong makes Jessie deaf — so it can wait until after launch.

**The repo matches the server.** Checked 2026-08-30 with `./scripts/n8n pull`. The only
differences are n8n stripping values equal to node defaults on save
(`contextWindowLength: 5`, `inputSource`, an empty `ai_tool` array on the dead
`Search records in Airtable` node). `Jessie — Book Session` is `active: true` on the server,
which for a sub-workflow means callable, not wired.

## Waiting on other people

[PENDING.md](PENDING.md) — nine things that need a change in Airtable, the Slack app or the n8n
server. Each entry says how it was found and what it breaks. Check it before re-deriving anything
about room capabilities: several fields in Rooms & Studios contradict each other, and which one
Jessie trusts is a decision that has already been made.

## Reference data

Verified against Airtable on 2026-08-30. Don't re-derive it; read it out of Airtable if
you doubt it.

**Departments (11)** — Audio Post · Business Development · Finance · IT · Localization ·
Management · Marketing · Music · P&C · Sales & Accounts · Video Post.
Title forms: Post · BD · Finance · IT · Loc · Mgmt · Marketing · Music · P&C · S&A · Video.
`Audio Post → Post`, `Video Post → Video`; never shorten Video Post to "Post". P&C is
already abbreviated in Airtable.

**Session types (12)** — Band Recording · Celebrity Recording · Event · Localization Dubbing ·
Localization Editing · Localization Mixing · Meeting · Music Mixing · Music Vox Recording ·
Post Mixing · QC · VO Recording.

**Engineer Role Required (5)** — Loc Engineer · Music Arranger · Music Engineer · None · Post Engineer.

**Rooms (27)** — Studio 1–8 · Studio A–F · Studio M · M1–M8 · Salin · Katha · Likha · Lobby.
Resource calendar ids live in two places: `Create Event`'s attendees expression in the main
workflow, and `ROOMS` in `code/check-conflicts.js`. Change one, change both.

**Booth rule** — always for Localization Dubbing; ask for Music Vox Recording and VO
Recording; never otherwise. Airtable's Room Requirements field can't express "sometimes",
which is why this is hardcoded.

## Gotchas that already cost time

Full list in HANDOFF.md §7. The four that bite hardest:

1. A `throw` inside an expression in an **optional** collection like `additionalFields`
   doesn't fail the node — n8n just drops the field. Guards only work in required
   top-level fields.
2. Don't put a fan-out node in the agent's main chain. Six items in means broken
   paired-item resolution and a silent Jessie. Collapse to one item with a Code node first.
3. `$('Node').first()`, never `$('Node').item`.
4. The prompt must not demonstrate what it forbids — it had 55 `**bold**` pairs alongside a
   rule against them. Models copy context over instructions about context.

## Related

`../Projects/haist/` holds the HAIST programme docs. `CLAUDE.md` and `DECISIONS.md` in
there are stale on Jessie specifics — model tier, Airtable read count, tool count — and
are listed for correction in HANDOFF.md §9.9.
