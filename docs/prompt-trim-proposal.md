# Prompt trim — proposal

**Status: draft for Howard's review. Nothing is live.** Prepared 2026-09-26.

| | Live (main v156) | Draft |
|---|---|---|
| Characters | 47,084 | 29,223 — **38% smaller** |
| Words | 8,241 | 4,955 |
| `{{ }}` data insertions | 22 | 22 — identical, same order |
| `**double asterisk**` runs | 9 | 0 |

- Baseline, exactly as live: [`prompts/system-prompt-live-2026-09-26.md`](../prompts/system-prompt-live-2026-09-26.md)
- Draft: [`prompts/system-prompt-TRIM-DRAFT.md`](../prompts/system-prompt-TRIM-DRAFT.md)
- Side by side: `git diff --no-index --word-diff prompts/system-prompt-live-2026-09-26.md prompts/system-prompt-TRIM-DRAFT.md`

(`prompts/system-prompt-live.md` is from 30 August and is not what is live.)

## Why

Jessie runs on Gemini 3.5 Flash Lite, a small model. The QA round-2 failures traced to the model, not the workflows: in Camille's run every tool returned the right answer, and Gemini checked the wrong date anyway and invented an engineer's surname. The prompt has grown from ~31,000 characters in August to 47,000. The more rules a small model juggles, the more it drops on any given turn. This does not replace enforcing things in code — it reduces how much the model is asked to hold.

## What was cut

**1. Rules the code already enforces, cut to what the model needs to know.** Room suitability, off-list rooms, conflicts, past dates, the confirmation marker, ownership on cancel and move, and unusual durations are all refused by a sub-workflow or rewritten by Guard Probe. The prompt still tells Gemini they exist and to relay the refusal; it no longer explains the mechanism at length.

**2. Incident history.** Lines recording how a rule once broke are useful to us and noise to the model — gotcha 6 notes the model copies what is in front of it. Moved here, not deleted:

- Reporting one room as busy because another room in the busy list was.
- Listing a booking as an option in the same turn a search showed it cancelled.
- Inventing a middle initial in a client's name.
- Working series dates out mentally and putting a series on the wrong days.
- The explanation that Book Session cannot see a summary written in the same response, because the reply has not reached Slack yet.

**3. Duplication.** "Never book in the past" appeared three times; "relay the tool's reason, don't invent one" three times; the ambiguity rules across three sections; the project-title rules three times; the title format twice; the making-way logic in four places. Each now appears once.

**4. Wording.** Rationale sentences and restatements tightened throughout. Formats, examples, title patterns and the department table are kept.

## Decisions for Howard

These came up while reading the whole prompt. The draft takes a position on each; check it.

1. **Stale fact removed.** The Rooms section said *"Studios 7 and 8 are typed as 5.1 Mixing but record in stereo only."* PENDING 1 records that as fixed in Airtable on 21 Sep. The rule (use Recording Format, not Room Type) is kept; the stale example is gone.

2. **Two conflicting "Booked by" rules.** One section said an on-behalf booking records the *other person* as the booker. The newer on-behalf paragraph (v151) says Booked by stays the requester with `(for <name>)`, via `booked_for`. The draft keeps only the newer rule, since the `Booked For` node (v154) backs it. Confirm the older one is dead.

3. **Two making-way flows.** *Requesting a held room* (Book Session opens a consent request; the holder decides) and *relocating as a coordinator* (a coordinator moves the session via Move Booking, then books). They were in different sections and read as contradictory. Both are kept, in one section, labelled. Confirm both are meant to be live.

4. **A reference that points at nothing.** "No record means stop" lists an exception for *"client names on Music sessions — covered in the booking section"*. Nothing in the booking section covers it. The draft keeps the exception as stated; decide whether it is real, and if so what the rule is.

5. **A self-contradicting duration clause, removed.** *"The requester may override, but only after explicitly acknowledging the mismatch"* sat next to *"Book the length they asked for. Never … ask them to shorten or lengthen it."* Also, the live prompt says to pass the duration note on *after* the booking is confirmed, while v155 made that flag deterministic *before* the yes. The draft's wording ("if Book Session notes an unusual length, pass that on once") works either way.

6. **Nine `**bold**` runs removed.** Slack formatting uses single asterisks, and the prompt was demonstrating exactly what it forbids (gotcha 6).

7. **Misfiled lines moved.** "If the request matches the records, say nothing" and "Typical Session Length is not a deviation" were stranded inside the making-way section. Both are now under *Deviations*.

## Deliberately not done

- **No behavior was added.** This is a trim. It does not attempt to fix the date bug from QA round 2 — that needs a guard in code, not another rule.
- **Rare flows are still in the prompt.** In the draft, recurring bookings and making way are about 3,000 characters sent with every message (4,700 in the live prompt). The next step would be returning those instructions from the tools only when those flows actually run. That is a workflow change, so it is out of scope here.

## Before it goes live

`test-nodes` exercises the Code nodes, not the prompt, so it will pass and prove little. The real check is a conversation pass covering each trimmed rule:

- happy-path booking · missing fields asked in one message · past date
- ambiguous client (numbered options) · exact-match client · "produ" · a name in both Clients and Bookers
- music with arranger · Celebrity Recording (Music vs Audio Post) · Localization (Project Code title, booth)
- off-list room refused, then insisted on · a deviation note · preferred room proposed first
- on-behalf booking (`booked_for`) · External vs Personal
- recurring series (including over 16) · M Booth (no confirmation) · conference room · Lobby
- cancel own · cancel someone else's · move own · move someone else's · PARTIAL wording
- making way: consent request, and coordinator relocation
- "show my bookings" · a vague "show bookings"

**Timing.** The End User SOP is written 29 Sep – 2 Oct from Jessie's behavior as it stands. Landing this during or after that risks the SOP describing a bot that then changes. Either land it and retest before 29 Sep, or hold it until after launch on 12 Oct.

**Deploying.** Build from a fresh pull of main. Replace the agent node's `systemMessage` with the draft, keeping the leading `=`. Push with `./scripts/n8n-write put`, then run `./scripts/reapply-main-fixes --check`.
