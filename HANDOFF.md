# Project Jessie — handoff to Claude Code

> **Historical. Do not act on this file without checking it first.**
>
> Written 2026-08-30 at ~2am, before that day's work. It is kept for its design
> intent — *why* things were built the way they were — and several of its facts
> have since been proven wrong, including some that were wrong when written.
> Known examples: it says the `.item` → `.first()` conversion is done (it was
> not), and it describes a build many versions behind what is running.
>
> **Start with [ONBOARDING.md](ONBOARDING.md) instead.** That is the current
> entry point and is checked against the live build. For how the system is meant
> to think, read [CLAUDE.md](CLAUDE.md) and [DETERMINISM.md](DETERMINISM.md).
> Read this file only when you want the reasoning behind an early decision, and
> verify anything it asserts against the live workflow before relying on it.

Drop this in the repo root so a fresh Claude Code session reads it as context.

---

## 1. What Jessie is

A Slack bot that books studio time for Hit Productions, a Manila audio/video post house. Built in n8n.

```
Slack DM → n8n → AI agent (Gemini 3.5 Flash Lite) → Airtable reads + Google Calendar writes → Slack reply
```

- **n8n:** `signal.hitpromanila.net`
- **Main workflow:** `Project Jessie` (live, active)
- **Sub-workflow:** `Jessie — Book Session`, id `EUG3sGXkfsJSYIMz` (built and tested, **not yet wired**)
- **Airtable base:** `app8GQxEInqJi1NRP` — "Project Jessie Knowledge Base"
- **Calendar:** `c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com` — "KDC Bookings"
- **Model:** `models/gemini-3.5-flash-lite`, temperature 0.2
- **Launch:** Sep 25 2026. QA runs now, on **year-shifted dates** — a Set-style expression in the system
  prompt adds one year, so QA books in 2027 to avoid colliding with live bookings.

Owner: Tara (Strategic Lead). Devs pick up the workflow work; a separate group does QA.

---

## 2. Do this first — n8n API access

This is the whole reason for moving to Claude Code. Without it every change is an export/import cycle
through a chat window, which is how a whole evening disappeared.

1. n8n → Settings → n8n API → create an API key.
2. Put it in `.env` in the repo, **never** paste it into a conversation:
   ```
   N8N_BASE_URL=https://signal.hitpromanila.net
   N8N_API_KEY=...
   ```
3. Add `.env` to `.gitignore` before the first commit.

The endpoints that matter:

| Purpose | Call |
|---|---|
| Read a workflow | `GET /api/v1/workflows/{id}` |
| Update a workflow | `PUT /api/v1/workflows/{id}` |
| List workflows | `GET /api/v1/workflows` |
| **Read executions** | `GET /api/v1/executions?workflowId={id}&limit=20` |
| One execution in full | `GET /api/v1/executions/{id}?includeData=true` |

Auth header is `X-N8N-API-KEY`.

That executions endpoint is the important one. Several problems in this project went unsolved purely
because nobody could get an execution log into the conversation.

**Also worth versioning in the repo:** both workflow JSONs and the system prompt. Right now the only
history of the prompt is a chat transcript and the only history of the workflow is n8n's internal list.
Four weeks from launch with three people touching it, that's thin.

---

## 3. Current state

**Live:** `Project Jessie v36.json` — that file is the source of truth for what is running.

Version numbers v22–v36 are a local convention from the chat session, not n8n's. v36 is the last one
imported and confirmed working.

**Built but not wired:** `Jessie - Book Session v2.json`. Imported, tested standalone, both tests pass —
creates when the room is free, rejects with `ROOM_OCCUPIED` when it isn't. The agent does not call it yet.

---

## 4. The immediate task — wire Book Session to the agent

Right now the agent creates events with a raw Google Calendar tool and is *told* to check for conflicts
first. It doesn't reliably. The sub-workflow does the check and the create as one atomic call it cannot
skip or reorder.

### 4a. Add the tool node

In `Project Jessie`, add a **Call n8n Workflow Tool** (`@n8n/n8n-nodes-langchain.toolWorkflow`) pointing
at workflow `EUG3sGXkfsJSYIMz`. Name it `Book Session`. Connect to the agent's `ai_tool` port.

Seven inputs:

| Field | Value |
|---|---|
| `summary` | `{{ $fromAI('summary', 'The finished calendar title, per the title rules in the system prompt.', 'string') }}` |
| `start_iso` | `{{ $fromAI('start', 'ISO 8601 start with +08:00. For an all-day booking, just the date.', 'string') }}` |
| `end_iso` | `{{ $fromAI('end', 'ISO 8601 end with +08:00. For all-day, the day after the booking date.', 'string') }}` |
| `rooms` | `{{ $fromAI('rooms', 'Exact room name, or comma-separated for paired rooms, e.g. Studio 1, Studio A', 'string') }}` |
| `description` | `{{ $fromAI('description', 'Engineer and tech requirements only.', 'string') }} \| Booked by: {{ $('Get Booker').first().json.Name }} \| ref: {{ $('Slack Trigger').first().json.user }}` |
| `all_day` | `{{ $fromAI('all_day', 'True only for an M Booth with no time given, or Lobby/Conference when the whole day was asked for.', 'boolean') }}` |
| `exclude_event_id` | `{{ $fromAI('exclude_event_id', 'During a reschedule, the id of the booking being moved. Empty otherwise.', 'string') }}` |

**The `description` field is load-bearing.** `ref: U...` is the requester's raw Slack ID, and the delete
guard authorises cancellations by comparing it to the live Slack trigger. Drop it and nobody can cancel
anything.

Then **disable** the old `Create Event` node rather than deleting it, so reverting is one click.

### 4b. Prompt surgery, same change

The sub-workflow now owns conflict checking and post-create verification, so the prompt must stop
instructing the model to do them or it will contradict the tool. In the agent's `systemMessage`:

1. Delete the whole `## THE CONFLICT CHECK` section (~450 words).
2. Delete the whole `## After creating` section (~200 words).
3. Replace rule 2 in "The three rules that are never overridable" — currently
   *"Never create an event without a conflict check in the same response. See THE CONFLICT CHECK below."*
   It should now say Book Session is the only way to create a booking, that it checks availability and
   creates in one call, and that a rejection must be relayed rather than worked around.
4. In `# Rescheduling`, step 4 says "including a fresh conflict check" — the tool does that now.
5. In `# Internal rooms`, the Shared rules paragraph says "the conflict check applies in full, in the
   same response as Create Event" — same.
6. Add a short note that Book Session returns a `human` field phrased for a person, and the agent should
   relay it more or less verbatim rather than re-describing what happened.

### 4c. Test after wiring

1. Book a studio session through Slack into a free slot — should work end to end.
2. Book the same room and window again — should refuse and name the conflicting booking.
3. Cancel a booking you made — should work.
4. Cancel someone else's — should refuse.

---

## 5. What was fixed on Aug 29–30

All of this is already in v36 unless noted.

1. **Tool name mismatch.** The prompt told the agent to call `Search Events for Deletion`; the node was
   named `Search Events for Detection`. Being told to call a tool that isn't in its list is why Jessie
   emitted `get_weather(location="Boston")` — that's the canonical function-calling example in Google's
   docs and it's what a model falls back to when tool selection collapses.
2. **QA date block.** It told Jessie never to resolve dates against the real year, then told it to call
   List Events to verify the date — which returns real dates. Self-contradicting. Replaced with 3 lines.
3. **System prompt rewritten** into intent branches (BOOK / INTERNAL / RESCHEDULE / CANCEL / VIEW), and
   fifteen blocks marked CRITICAL cut to three genuinely unoverridable rules.
4. **Nine tool descriptions written.** Four tools had none at all and were running on n8n's
   auto-generated text — including `Localization Projects`, which is why Jessie searched it for a Post
   project and reported "no such project."
5. **Temperature set to 0.2**, was unset and defaulting high.
6. **Session key** now includes the date, so conversations reset daily. Was the bare Slack user ID, which
   meant a five-day QA conversation was one unbroken session with no way to start fresh in a DM.
7. **Ownership guard on delete** — extracts `ref:` from the event description and compares to the live
   Slack user id. Closed a hole where anyone could cancel anyone's booking.
8. **Deletion search window** made deterministic — the model supplies one date, n8n builds a full Manila
   day. It was generating both ends of the range and sometimes producing a zero-width window.
9. **Session type asked before anything else**, and project titles are never looked up in any table
   unless the session type is Localization.
10. **55 `**bold**` pairs converted to `*`** — the prompt was demonstrating the syntax it forbade.
11. **`retryOnFail` off on the agent.** Unverified but asymmetric: if n8n replays the node after a
    successful Create Event, it double-books. Worth confirming properly.
12. **Empty agent output can no longer crash** the run on Slack's `no_text`.
13. **Departments completed 8 → 11** (Finance, Management, Video Post were missing).
14. **Session type names** matched to Airtable's exact values ("Localization Dubbing", not "Loc Dubbing").
15. **Booth rules corrected** — always for Localization Dubbing, ask for Music Vox Recording and VO
    Recording, never for anything else.
16. **Past-date guard** on Create Event's start field.

---

## 6. Reference data — verified against Airtable, don't re-derive

**Departments (11):** Audio Post · Business Development · Finance · IT · Localization · Management ·
Marketing · Music · P&C · Sales & Accounts · Video Post
Title forms: Post · BD · Finance · IT · Loc · Mgmt · Marketing · Music · P&C · S&A · Video.
Note `Audio Post → Post` and `Video Post → Video`; never shorten Video Post to "Post".
P&C is stored in Airtable already abbreviated, unlike the others.

**Session types (12):** Band Recording · Celebrity Recording · Event · Localization Dubbing ·
Localization Editing · Localization Mixing · Meeting · Music Mixing · Music Vox Recording · Post Mixing ·
QC · VO Recording

**Engineer Role Required values (5):** Loc Engineer · Music Arranger · Music Engineer · None · Post Engineer

**Room Requirements:** Band Recording = Large Studio · Celebrity Recording = Large Studio + Holding Rooms ·
Localization Dubbing = Studio 1–6 + Booth (booth always) · Music Vox Recording and VO Recording =
Studio + Booth (booth **sometimes** — ask) · Localization Editing, Localization Mixing, Music Mixing,
Post Mixing, QC = Studio · Event = Lobby or Conference Rooms · Meeting = Conference Room

**Rooms (27):** Studio 1–8 · Studio A–F · Studio M · M1–M8 · Salin · Katha · Likha · Lobby.
Resource calendar ids are in the room map inside `Create Event`'s attendees expression and in the
sub-workflow's `Check Conflicts` node.

---

## 7. Gotchas — every one of these cost real time

1. **Expression guards only work in required top-level fields.** A `throw` inside an expression in
   `additionalFields` — an optional collection — does not fail the node; n8n just drops the field. A
   title guard put there produced calendar events with no title at all and never complained. The delete
   guard works because `eventId` is required. Check which kind of field you're in before relying on a throw.
2. **Don't put a fan-out node in the agent's main chain.** A Slack history node returning 6 messages took
   the agent's input from one item to six and broke paired-item resolution in the system prompt. The run
   died before Send Reply and Jessie went silent. If you add a multi-item node, collapse it back to one
   item with a Code node before the agent.
3. **Use `$('Node').first()`, not `$('Node').item`.** `.item` depends on paired-item tracing and breaks
   the moment item counts change upstream. All references in v36 are already converted.
4. **"Always Output Data" on any Get Many node feeding a check.** Zero results outputs nothing and the
   branch silently stops — skipping the check on exactly the case where everything looks fine.
5. **Never interleave UI edits with JSON imports.** Import replaces the canvas, so a file built from an
   older export silently reverts anything changed in the UI since. This happened once and cost a repeated
   change. With API access this stops being an issue.
6. **The prompt must not demonstrate what it forbids.** It contained 55 `**bold**` pairs and one line
   saying never use double asterisks; and it said "Loc Dubbing" while the tool description said never to
   abbreviate it. Models copy what's in context over what they're told about context.
7. **Read reference data out of Airtable rather than asserting it in the prompt.** Asking Jessie itself
   ("list every distinct Department in the Bookers table") is a fast way to audit — it found three
   missing departments and three wrong booth rules in about ten minutes.

---

## 8. Unresolved — the confirmation gate

> **Amended 2026-08-30, after reading execution 2048.** The diagnosis below is wrong. The
> v27–v29 runs died on `Duplicate key 'Rooms' found with different description or type` in
> the `Create Event` tool — the agent node threw before the model ran, on every message.
> `Gate Context` worked correctly (6 items in, 1 out, no error). The gate was never tested.
> v36 no longer has the duplicate. Full detail in CLAUDE.md, "What the logs settled".
> The rest of this section is kept as written, for the design and the alternative.

**The problem:** Jessie books without presenting a summary and waiting. It has been given the rule in the
system prompt *and* in the Create Event tool description, and ignores both. This is the largest remaining
hole and it is not fixable by prompting at this model size.

**The design that should work:** Send Reply runs *after* the agent, so within a single run Jessie's own
summary is not yet in Slack. If a guard checks Slack history for a marker line at the end of the last bot
message, a same-turn booking cannot pass — the message it would need to find hasn't been posted yet. Real
turn-boundary proof, using Slack data rather than anything the model supplies.

**Three attempts, all reverted:**

- **v27** — added the Slack history node straight into the main chain. Item-count fan-out, Jessie went silent.
- **v28** — added a Code node to collapse back to one item, converted `.item` to `.first()`. Chain ran, but
  the agent returned empty output and Send Reply failed with `no_text`.
- **v29** — added fallback text and told the agent not to retry the blocked tool. The fallback then fired
  on **every** message, not just bookings, meaning the agent was succeeding and returning nothing on
  everything. That rules out the retry-loop theory and nobody got further.

**What's needed:** one execution from a v28 or v29 run — did `Gate Context` error, how many items did it
output, what did the agent node actually return. With API access that's a single call. Do not attempt a
fourth blind fix.

**Alternative design if it stays stubborn:** split booking into two tools. `draft_booking` returns a
formatted summary and creates nothing; `confirm_booking` takes a draft id that only exists because the
draft ran. Booking in the same turn as asking becomes structurally impossible. Bigger build, no dependency
on Slack history.

---

## 9. Everything else still open

**Decisions for Tara:**

1. **Advertising Projects** — the node is disabled *and* incomplete (no filterByFormula, no description).
   Post/Advertising project titles are currently accepted as typed, which is the design. If that holds,
   delete the node; leaving it disabled-but-present is what caused Jessie to search Localization Projects
   for a Post project. If titles should be validated, it needs building and the prompt rules change.
2. **Should Jessie answer lookup questions about people at all?** Asked for a Slack user ID, it gave one.
   Not sensitive in itself, but nothing scopes what it will read out of the Bookers table, and that
   matters more once an Authority or notes field exists.
3. **Is Flash Lite still the right model?** Not a technical call. But every remaining failure is
   multi-step procedural discipline, which is what the smallest tier is worst at.

**Work:**

4. **Slack Trigger** is on `any_event` with `watchWorkspace: true` — fires on every event in the whole
   workspace and filters afterwards. Check the 24-hour execution count first; if it's in the thousands
   that's quota being burned and possibly throttling. Scoping it wrong makes Jessie deaf, so watch
   executions while changing it.
5. **Delete two dead nodes:** `Search records in Airtable` (disabled, disconnected, empty table value)
   and `Advertising Projects`, pending decision 1.
6. **Airtable schema additions** that would remove prompt rules entirely:
   - `Department` on Session Types — turns the role→department inference into a returned value
   - `Booth Requirement` on Session Types with Required / Optional / None — the Room Requirements field
     can't currently express "sometimes", which is why that exception is hardcoded
   - `Department Code` on Bookers, `Pairable Booths` on Rooms & Studios
7. **Verify the `retryOnFail` double-booking risk** properly rather than on the asymmetry argument.
8. **Duration min/max enforcement** — needs Session Types read at booking time, so it belongs inside the
   Book Session sub-workflow. Not built.
9. **Update the two HAIST project docs** — `haist/CLAUDE.md` and `haist/DECISIONS.md` are both stale.
   DECISIONS records the model as "Gemini Flash 3.5, Tier 1"; it is 3.5 Flash Lite. It also records
   Airtable reads as three; there are five active. CLAUDE.md says seven agent tools; there are nine.

---

## 10. Files to bring across

| File | What it is |
|---|---|
| `Project Jessie v36.json` | the live main workflow — source of truth |
| `Jessie - Book Session v2.json` | the tested sub-workflow, id `EUG3sGXkfsJSYIMz` |
| `check-conflicts.js`, `return-rejection.js` | the two Code node bodies, if you'd rather diff them separately |
| this file | |

Two artifacts also exist in Tara's Claude artifacts gallery: a **determinism spec** covering the larger
Guard A/B design, and a **change log** covering v22–v29 including the failures. The change log stops at
v29; versions v30–v36 are summarised in section 5 above.
