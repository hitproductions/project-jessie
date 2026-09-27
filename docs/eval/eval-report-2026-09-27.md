# Jessie hallucination test: how it works and what it found

*Run on 27 September 2026 against live Jessie (main workflow as of 26 Sep). Internal: it contains staff and client names.*

## The short version

- We sent Jessie **245 test conversations** (49 scenarios × 5 repeats) through the **real Gemini model**, the real sub-workflows and the real Airtable and calendar data. Nothing was booked and nothing was posted to Slack.
- **What held up:** she never invented an engineer (67 of 67 correct; an unknown name was refused 5 of 5 times). Dates were 30 of 30 correct. "Booking for a colleague" was detected 15 of 15 times. She asked when details were missing (one exception: a request with no date got questions about everything *but* the date), refused past dates, and never claimed a booking she hadn't made.
- **The biggest find is not the model's reasoning, it's a bug in our code.** When Gemini adds stray characters to a time (for example `+08:00hq`), the Room Availability check reports **every room as free**. That happened on 40% of availability checks in the test (79 of 199), and on 4 of 27 real checks on live Jessie since 24 Sep. Jessie then offers a room that is already booked. Usually the booking is still stopped at "yes". But Book Session's own safety check has the same blind spot if the padding happens in the booking call, which hasn't been seen live yet. **Small, deterministic fix; recommended before launch.**
- **The prompt's own example leaks into answers.** It uses "Studio 8, Dhang's usual room" as an illustration, and the model repeats it. "Dhang" showed up as if a real client, and Jem Lim's usual room was given as Studio 8 (wrong; it's Studio F) in 10 replies.
- **Presentation drift.** The same request gets a differently shaped summary almost every time: five different date formats, "Project" vs "Project Title", sometimes a title line and usually not. That is the case for having code, not the model, write the summary (the "Prepare Booking" idea).
- **Speed:** a median of 9.9 s per turn on the test copy, with the 90th percentile at 11.8 s. Nothing we're proposing adds a model call.

## How the test works

### Is it the real AI?

Yes. Every test message goes through the same Google Gemini model live Jessie uses (Gemini 3.5 Flash Lite, temperature 0.2), with the same system prompt. The tools she calls are the real live sub-workflows (Room Availability, Book Session, Find Booking and the rest), reading the real Airtable tables and the real KDC calendar. Nothing on the AI side is simulated.

### The test copy ("twin")

Live Jessie can only be reached by DM-ing her in Slack, and her reply only goes back to Slack. We can't send hundreds of automated messages that way without spamming a real DM and the n8n history staff see. So there is a second workflow in n8n, **"ZZ Jessie Eval Twin (test copy - do not use)"**. It's a copy of live Jessie with only the Slack parts swapped:

| Live Jessie | Test copy |
|---|---|
| Waits for a Slack DM | Waits for a message from the test script (a private web address) |
| Reads the recent Slack conversation | Reads the conversation the script sends along |
| Posts the reply to Slack | Hands the reply back to the script, plus every tool Jessie called and what each one returned |
| Reads and writes the consent Sheet | Skips it (nothing pending) |

Everything else is identical: the prompt, the model, the confirmation gate, Guard Probe, Booked For, and all 13 tools. **42 of 53 nodes are byte-for-byte the same as live.** The script refuses to run if anything else differs. It is rebuilt from live at the start of every run, so it can never test an out-of-date copy. It's switched on only while a run is in progress.

### What the script does, automatically

`./scripts/eval-run` does the whole thing in one go:

1. Pulls the current live Jessie and rebuilds the test copy from it.
2. Uploads the copy, checks it against live, and switches it on.
3. For each scenario, sends the message (plus any earlier messages in that conversation) to the copy. Each scenario runs **5 times**, because the model doesn't answer the same way twice.
4. n8n runs the full Jessie pipeline, including the real Gemini call, and sends back the reply and the tool calls.
5. The script **grades each reply against the facts, not against a fixed expected answer.** Is the engineer on the Bookers list, or invented? Does the date match what Gate Context worked out? Did she name every room the availability check said was free? Did she say "Booked" without actually booking?
6. Switches the copy off and writes a report.

### Why it can't book anything

A booking needs a summary followed by an explicit "yes". The script refuses to send "yes" at all, and it stops the whole run if any booking, cancel or move ever reports success. None did.

### Where the results live

On Howard's Mac, in the project folder, not in Google Sheets:

- `eval/results/run-<date-time>.md`: the pass/fail report
- `eval/results/run-<date-time>.json`: every reply, for digging into a specific case
- n8n's execution list for the test-copy workflow, with each run's full tool calls, kept about 3 days

The `eval/` folder is deliberately kept out of GitHub because the replies contain real names and schedule data. The scenarios themselves are in the repo, in `docs/eval/scenarios.json`.

## What we tested

49 scenarios, each run 5 times.

| Area | Scenarios | What it checks |
|---|---|---|
| Engineers | 8 | Nicknames ("Drey", "Topet", "Eli"), initials ("RG"), full names, an engineer who doesn't exist, engineer + arranger. Is the right person named, and are the title initials right? |
| Clients | 3 | Short names ("Pael", "sasa"), a client that isn't in Airtable |
| Dates | 5 | "next Friday", "this Thursday", "October 14", "tomorrow", "next Tuesday" |
| Booking for someone | 3 | "for Japs", "on behalf of Kristine", and "for Jem Lim" (a client, not a colleague) |
| Unusual lengths | 3 | 9 hours, 15 minutes, a normal 2 hours: is the heads-up line shown only when it should be? |
| What's free | 3 | "What rooms are free…": does she list every free room and no busy ones? |
| Missing details | 3 | Not enough info, so she must ask. Also details given over two messages. |
| QA sheet (round 2) | 21 | The automatable rows from `Jessie_QA_Sheet 0830`: room lists, vocal booths, 5.1, wrong room for the session type, dubbing booths, priority rooms, typical duration, a second booking, "make it 3pm instead", lookups, cancel not found, recurring, past date, room nicknames |

The QA-sheet rows that need a real "yes" or a calendar check (C1–C6, X1–X3, X5, N1, N3, N4, M6, B2) can't be automated safely and stay manual.

## Results: core scenarios (140 conversations)

| Check | Pass | Fail | Notes |
|---|---|---|---|
| Right engineer | 67 | 0 | No invented names. Nicknames, initials and first names all resolved. |
| Unknown engineer refused | 5 | 0 | "Juan Dela Cruz" was refused 5 of 5 times, with a request to check the name |
| Date correct | 30 | 0 | Every relative date matched Gate Context |
| Booked-for detected | 15 | 0 | "for Japs" → Japs Concepcion, "on behalf of Kristine" → Kristine Trocino, "for Jem Lim" → no one |
| "(for X)" in summary | 8 | 0 | |
| Heads-up on unusual length | 13 | 0 | Shown for 9 h and 15 min, not for 2 h, whenever a summary was shown |
| Asks when details are missing | 10 | 0 | |
| Project named | 46 | 1 | |
| Client correct | 40 | 4 | "Sasa Abella (Producer)": her Airtable role glued onto the name |
| Title line shown in summary | 23 | 74 | See finding 2 |
| Title initials (when shown) | 12 | 1 | The single failure is the garbled summary in finding 2. Engineer + arranger correctly gave "DR x BC". |
| All free rooms named | 11 | 4 | "Which studios are open": 4 of 5 left out Likha, Lobby and the M booths. Arguably right, since the question asked for studios. |

A few summaries that didn't appear were the right call: Studio F was genuinely taken (3), or the client wasn't in Airtable (3).

## Results: QA-sheet scenarios (105 conversations)

Scored the same way, 21 scenarios × 5. Where a check "failed" because my scenario was badly designed, the table says so.

| QA row | What it asks | Result |
|---|---|---|
| A2 | List all rooms | 3 of 5 exact. 2 of 5 added **M2 and M6**, which aren't in the Rooms table. It looks like she filled in the M1–M8 pattern. M6 does exist on the calendar ("M6 - Marketing"), so the Airtable Rooms table may be missing it. Worth checking. |
| A3 | Which rooms are vocal booths | 5 of 5 correct, read from the Vocal Booth flag |
| A4 | Which rooms can do 5.1 | 5 of 5 correct, read from Recording Format, not the misleading Room Type |
| M1 | VO in Studio 3 | 5 of 5 correctly say Studio 3 doesn't do VO and offer the free usual rooms. None suggest pairing a booth, which the QA sheet expected. |
| M2 | Dubbing, engineer "Jek" | Studio 1 and Studio A are genuinely taken (NET-BUGHAW); 5 of 5 said so and offered free rooms |
| M3 | Celebrity recording, no room given | 2 of 5 went straight to the priority room (Studio F). 3 of 5 asked "Music or Audio Post?" first. |
| M4 | VO, typical duration | 5 of 5 correct |
| M7 | "Book a session for Spotify…" | 5 of 5 asked "Who is the client?". Spotify wasn't taken as the client (see decision a). |
| B3 | A second booking in the same chat | My scenario asked for VO in Studio 3, so declining was right (5 of 5). Needs a better scenario. |
| N2 | "Actually make it 3pm instead" | 5 of 5 moved only the time and kept everything else. One reply carried the prompt's example name "Dhang" (finding 3). |
| F1a, F1b, F2 | What's booked / is Studio 7 free / what do I have this week | 15 of 15 answered from a lookup; none offered a booking |
| X4 | Cancel a booking that doesn't exist | 5 of 5 said it wasn't found |
| C7 | Every Tuesday for the next month | 5 of 5 used Expand Series and listed Tuesdays 5, 12, 19 and 26 Oct. The 2 "failures" are my scorer not reading that date format. |
| E1 | "Book Studio 7 from 2pm to 5pm" (no date) | 5 of 5 asked for the session type, client and project, but **not the date**. She'll probably ask next turn, but it should be in the first question. |
| E2 | Book last Monday | 5 of 5 refused a past date |
| E3a, E3b | "studio one", "std 3" | 5 of 5 understood both names correctly. My scenarios asked for VO in rooms that don't do VO, so she rightly declined. Needs a better scenario. |
| E3c | "the big room" for a meeting | 5 of 5 named a room or asked which one |
| E4 | "for Jem Lim's new ad" | 5 of 5 asked "Who is the client?" (see decision a) |

Speed for this set: a median of 9.6 s per turn, 90th percentile 12.2 s. The padded-time bug showed up here too: 18 of 63 availability checks, all reporting everything free. **Across both runs that's 79 of 199 checks (40%).**

## Findings, most important first

### 1. Room Availability says "all free" when the model pads a time (bug, fix ready to build)

**What happens.** The model sometimes glues stray characters onto the end of a timestamp: `2027-10-07T16:00:00+08:00hq`, `…+08:00p`, `…+08:00Cllr`, an invisible emoji code, even Khmer letters. Room Availability sends that raw text to Google Calendar. Google rejects it, the node is set to carry on after errors, and the code then reads "no events" as "every room is free". It even cleans the time up afterwards for display, so the reply looks normal.

**How often.** 79 of 199 availability checks across both test runs (40%). Every padded check reported everything free, and every clean one was correct. On live Jessie it was 4 of 27 real checks since 24 Sep (15%).

**What the user sees.** Studio F is booked on Thursday 7 Oct 2027, 1–4pm (a QA test booking). Across 10 requests for that slot, Jessie offered Studio F **7 times**, each time straight after a padded check told her it was free. When the check was clean, she correctly said it was taken and offered alternatives.

**Does it reach a real booking? Not yet seen, but the backstop has the same gap.** Book Session re-checks the calendar at "yes". If the time it receives is *clean* (the usual case), it correctly refuses an occupied room (`ROOM_OCCUPIED`). But if the model pads the time *in the booking call itself*, Book Session's calendar lookup can't read it. It falls back to searching **the next 24 hours from now** instead of the requested slot, so the conflict check compares against the wrong day and finds nothing. The create step then gets the padded time and either fails with an error (safe), or, if Google accepts it leniently, books over an existing session. Which one happens is **unverified**: finding out needs a controlled test write. On live Jessie, **0 of 14** booking, move and series calls since 24 Sep had a padded time, so it hasn't happened in the history n8n keeps.

**Fix (small, deterministic, no speed cost).** In both Room Availability and Book Session (and Move Booking, which shares the pattern), clean the timestamps *before* the calendar query, not after. If the calendar query errors, answer "couldn't check" instead of "all free", and have Book Session refuse instead of searching a fallback window. Guard Probe already refuses a summary when the check errored, so this closes the loop. This is the same class as gotcha 16 (24 Sep); that fix cleaned the right values in the wrong step.

### 2. The summary looks different almost every time (the case for code writing the summary)

The same request produces differently shaped summaries across repeats:

- **Five date formats:** "October 8, 2027 (Fri)", "Friday, 8 October 2027", "Thursday, October 7, 2027", "October 8, 2027 (Tuesday)", "October 8, 2027 (Next Friday)"
- **Labels vary:** "Project" (31) vs "Project Title" (45); "Booking Type" appears in 14 of ~95
- **The calendar title** (`PROJECT / Client / initials`, what actually goes on the calendar) is shown in only **23 of 97** summaries
- **One summary was printed twice**, with a garbled first line: "KITE / Jem Lim / RG is Jem Lim's usual client type is External. Studio 7 is free."

None of this books anything wrong, since Book Session builds the real event. But people read the summary to decide whether to say yes, and the title they approve is often not shown. This is exactly the kind of thing prompt rules have never held. The durable fix is **"Prepare Booking"**: the model only collects the details, and a code node validates them and prints the summary in one fixed format, including the exact title that will go on the calendar. It adds no model calls; it replaces free text with a template.

### 3. The prompt's own example leaks into real replies

The system prompt explains preferred rooms with an example: *"Studio 8, Dhang's usual room, is free"*. The model copies it:

- "Dhang" appeared in **3 real summaries**, as if it were the client
- Jem Lim's usual room was given as **Studio 8 in 10 replies**. It's actually **Studio F**, which she said in 14 replies (and Studio 7 in 2).

The underlying problem: the Clients tool returns the preferred room as an Airtable record id (`rec36To…`), not a name. The model has no way to read it, so it guesses, and the prompt hands it a ready-made guess. Two fixes, both deterministic:

1. Resolve the id to the room name before the model sees it (the room list is already loaded in `All Rooms`).
2. Remove the named example from the prompt (gotcha 6: "the prompt must not demonstrate what it forbids").

### 4. Small text leaks

- **Tool instructions pasted into the reply:** 2 of 5 answers to "What rooms are free next Friday 2–5pm?" ended their list with "List exactly these and no others." That's the tool talking to Jessie, not something for the user. Guard Probe can strip it.
- **"last-resort" with a hyphen** gets past Guard Probe's filter, which only removes "last resort".
- **Client role glued on:** "Sasa Abella (Producer)" in 4 of 5 runs. "Pael" alternates between "Pael" and "Pael Laurena". A rendered summary (finding 2) would print the Airtable name.

### 5. Open decisions for next steps

These aren't bugs; they need a call on what Jessie *should* do.

| # | Situation | What she does now | Question |
|---|---|---|---|
| a | "Book ... **for Jem Lim**", "a session **for Spotify**", "**for Jem Lim's** new ad": the client given with "for" | Asks "Who is the client?", **20 of 20** across four scenarios | Should "for <someone not on staff>" be read as the client? That was Howard's rule on 25 Sep. Today it's safe, but it adds a turn to a very common phrasing. Booked For already knows who *is* staff, so this can be decided in code. |
| b | A client that isn't in Airtable ("Acme Records") | 3 of 5 ask to check the name; 2 of 5 go ahead | Refuse, go ahead, or go ahead and flag "new client"? Right now it's a coin flip. |
| c | 15-minute VO session | 3 of 5 show the summary with the heads-up; 2 of 5 ask first and say "minimum duration is 60 minutes" | Fine to ask? If so, the "minimum" wording should go, since Min/Max are what sessions usually run, not limits. |
| d | "Which **studios** are open?" | 4 of 5 leave out Likha, Lobby and M booths | Correct reading of "studios", or should she always list everything? |

| e | Celebrity recording, no room named | 2 of 5 go straight to the priority room; 3 of 5 ask "Music or Audio Post?" first | Is that question needed, or can the session type settle it? |

## Speed

| | Median | 90th percentile |
|---|---|---|
| One turn on the test copy (this run, 145 turns) | 9.9 s | 11.8 s |
| One turn on live Jessie (26 Sep, 19 turns, incl. Slack) | 11.8 s | 16.7 s |

The test copy is about 2 s faster because it skips the Slack round trips (reaction, history fetch, posting). Nothing proposed below adds a model call. Fix 1 changes one calendar request. Prepare Booking replaces model-written text with a template, which should make replies slightly shorter and faster.

## Proposed next steps

1. **Fix the padded-time bug now** (finding 1) in Room Availability, Book Session and Move Booking: clean before the query, and fail closed ("couldn't check", or refuse) on a calendar error. Test offline, then re-run this eval to confirm the padded cases come back correct. Small enough to land well before the 5 Oct pre-launch cut-off.
2. **Fix the preferred-room leak** (finding 3): resolve the record id to a room name, and drop the "Dhang / Studio 8" example from the prompt.
3. **Strip leaked tool text and "last-resort"** in Guard Probe (finding 4). Same size.
4. **Settle the five open decisions above**, then enforce the answers in code rather than the prompt.
5. **Prepare Booking** (finding 2): design it this week, and weigh building it before launch against after, given the 5 Oct cut-off.
6. **Model comparison:** re-run this exact test with Gemini Flash (non-Lite), and with Claude Haiku 4.5 if we add an Anthropic key in n8n. The test copy makes that a like-for-like comparison, speed included.
7. **Fix the scenarios that tested the wrong thing** (B3, E3a, E3b) and the C7 scorer. Then **re-run this eval after every change** that touches the prompt or a guard. It takes about 45 minutes for the full set and nobody has to watch it.

## Appendix: running it again

```
./scripts/eval-run                  # everything, 5 repeats each (~45 min)
./scripts/eval-run --only QA        # just the QA-sheet scenarios
./scripts/eval-run --only ENG --repeat 3
```

Needs the n8n key in `.env`, like every other script. Scenarios live in `docs/eval/scenarios.json`; add one by copying an entry and changing the message and what to expect.
