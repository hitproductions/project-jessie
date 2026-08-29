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
2. **Pull an execution for the confirmation-gate problem** — HANDOFF.md §8. Three blind
   fixes (v27–v29) were reverted; the next move is `./scripts/n8n execs` then
   `./scripts/n8n exec <id> --errors` on a v28 or v29 run. Do not attempt a fourth blind fix.
3. **Check the Slack Trigger's 24-hour execution count** — it is on `any_event` with
   `watchWorkspace: true`. Scoping it wrong makes Jessie deaf, so watch executions while changing it.
4. Everything else is in HANDOFF.md §9, including three decisions that are Tara's to make.

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
