# Claude Haiku swap: test summary (8 Oct 2026)

Jessie's agent moved from Gemini 3.5 Flash Lite to Claude Haiku (4.5, then 5.5) on 8 Oct, with Gemini kept as the
fallback. Every test below was run through Slack in a tester's DM, on 2027 dates (QA year shift). Times are PHT.
Details per build: `VERSIONS.md`; open items: `PENDING.md` item 99.

**Where it stands (21:00):** live main v245 / Book Session v98 / Book Series v8 / Cancel Booking v24 / Move Booking v26 on
Claude Haiku 5.5. The last three Slack rounds passed 24/25, 7/7 and 13/13, with no made-up or withdrawn cards, and the
one failure among them was a code bug that is now fixed.

## Compared with the last Gemini build (main v236, 8 Oct 13:34-13:45)

| | Gemini 3.5 Flash Lite (main v236) | Claude Haiku 5.5 (main v244-v245) |
|---|---|---|
| Smoke test (same 14 steps) | 14/14 | 24/25 on the longer v244 round (one code bug, now fixed), then 7/7 |
| QA round 3 scenarios | Not run on v236 | 13/13 |
| Made-up or withdrawn cards | 0 | 0 since v244 (Haiku 4.5 and 5.5 had 9 before the fixes) |
| Reply time, through the model | median 12 s (all reply types) | 10-16 s, median about 13 s |
| Reply time, handled in code (yes to a card) | - | 5-13 s |
| Availability answer | Named the booking but not its time | Booking, its time and the free rooms; still no "free the rest of the day" |
| Series date formats | Two formats | Three formats (card, result, single cards) - not changed by the swap |
| Follow-ups ("move it", "cancel that one", "book it") | Worked with memory | Work with the transcript (memory removed in v243) |
| Cost per message | about $0.004 | about $0.005-0.007, paid from the plan's monthly API credits |
| Needed changes | None | v237-v245, five sub-workflow builds, a new audit script |
| Fallback | 3.8 Flash | Gemini 3.5 Flash Lite (not yet tried since memory was removed) |

What the swap showed: Haiku follows tool and prompt text more literally than Gemini did. That exposed old instructions
("end with the line Confirm to ...") that Gemini had been working around, and a long-standing "cancel it" bug. All of those
fixes make Jessie more reliable on either model. Haiku also copies whatever its own earlier replies look like, which is why
conversation memory was replaced by a code-written transcript.

## Slack rounds

| Time | Build / model | What was tested | Result |
|---|---|---|---|
| 13:34-13:45 | main v236 / Gemini (baseline) | 14-step smoke test: book, yes, repeat yes, move, cancel, same request twice, conditional yes, no, series, cancel one date, availability | 14/14 |
| 14:40-15:01 | v237-v239 / Haiku 4.5 | Same list | Stopped at step 7: cancel cards written by the model, then a false "has been cancelled" |
| 15:11-15:22 | v239 / Haiku 4.5 | Rest of the list, with resets | 6 of ~19 model turns skipped the tool (copied cards, withdrawn by the guard) |
| 15:34-15:37 | v240 / Haiku 5.5 | Cleanup cancels | 3 of 6 cancels withdrawn on the first try |
| 19:44-19:49 | v242 / Haiku 5.5 (memory notes) | Cancels, book, availability | No copied cards; extra "shall I prepare it?" questions; availability answered with a note-style line |
| 20:03-20:04 | v243 / Haiku 5.5 (transcript) | First cancel after reset | Withdrawn twice: old tool text told the model to write the card |
| 20:20-20:32 | v244 + Book v98 + Series v8 + Cancel v24 + Move v26 | Full list in one conversation, plus "move it", "no wait, keep it at 10am", four cancels in a row | **24/25**; the one miss was a code bug ("cancel it" after "Moved") |
| 20:39-20:41 | v245 | Book, "move it", "cancel it" after Moved, repeat "cancel it" | **7/7** |
| 20:44-20:57 | v245 | 13 QA round 3 scenarios (B1, B3, E2, E4, E5, E6, F1, F3, N1, N2, X4, Taglish, early room check) | **13/13** |

## Issues found, and what happened to each

| # | Issue | Found | Cause | Fix | Status |
|---|---|---|---|---|---|
| 1 | Org-scoped API key rejected in n8n ("Bad request") | 14:20 | The key had no workspace | Key made inside a workspace (gotcha 33) | Fixed |
| 2 | Cancel card written by the model, with a stale time | 14:43 | Model skipped Prepare Cancel | v238: a card no tool made is withdrawn | Fixed (guard) |
| 3 | "...has been cancelled" with nothing cancelled | 15:01 | Claim check only read the start of the reply | v239: done-claims checked anywhere in the reply | Fixed |
| 4 | Haiku copied cards from earlier in the conversation | 14:43-15:37 | Memory kept only text, so cards looked like Jessie's own replies | v242 memory notes, then v243: memory removed, code-written transcript instead | Fixed |
| 5 | Haiku copied the v242 memory notes' style | 19:49 | Same habit as #4 | v243 (transcript), and bracket-only replies withdrawn | Fixed |
| 6 | Extra "shall I prepare the cancellation?" questions | 19:45 | Prompt sent cancels through Find Booking first | v243: a named booking goes straight to Prepare Cancel | Fixed |
| 7 | Cancel by a short title ("QATEST") withdrawn | 20:03 | Old Cancel Booking text told the model to write the card itself | Cancel v24: one close title match shows that booking's card | Fixed |
| 8 | Same old "write the confirmation" text elsewhere | Review 20:10 | Move Booking, Book Session (3 replies), Book Series, prompt Rescheduling, 2 tool descriptions | Move v26, Book Session v98, Book Series v8, main v244; new `scripts/audit-model-text` on every build | Fixed |
| 9 | Markdown headings would show as "##" in Slack | Review 20:10 | Claude copies the prompt's headings | v244: headings become bold | Fixed |
| 10 | "cancel it" after "Moved" got "That's already moved" | 20:23 | "cancel it" is on the yes list; the repeat-yes guard took it as a second yes (long-standing) | v245: it repeats only the same action | Fixed |
| 11 | Haiku settings | 18:00 | Haiku 5.5 rejects temperature / top P / top K and n8n's thinking budget | Left unset; max tokens 8000, 2 retries | Done |
| 12 | Availability doesn't say the rest of the day is free | 14:41 | Wording | - | Open |
| 13 | The reply to "no" is wordy | 20:27 | Wording | - | Open |
| 14 | Three date formats (series card, series result, single cards) | 15:19 | Wording | - | Open |
| 15 | O'Brien: "Did you mean Brian Cua?" (a staff member offered as client) | 20:53 | Client close-match check (code) | - | Open |
| 16 | All-day holds listed as "(12:00 AM)" in the not-found list | 20:55 | Cancel Booking wording | - | Open |
| 17 | "You asked for 2:00 to 3:00 PM earlier" when only 2pm was said | 20:48 | Model phrasing, harmless | - | Open (minor) |
| 18 | Leftover QA event "YES / O'Brien / HL", Studio 7, 14 Oct 2027 2-5 PM (6 Oct) | 20:44 | Project "YES" looks like a yes taken as the title on that day's build | For the booker to remove; worth a look | Open |
| 19 | Gemini fallback not yet tried without memory | - | - | One forced-fallback check | Open |

## Builds on 8 Oct

| Build | What it did |
|---|---|
| main v237 | Claude Haiku 4.5 primary, Gemini 3.5 Flash Lite fallback |
| main v238 | Withdraws a card no tool made |
| main v239 | Checks "done" claims anywhere in the reply |
| main v240 | Haiku 5.5 (changed in the n8n UI) |
| main v241 | Length changes after "Booked." + prompt tidy (built by another team member, included in v242) |
| main v242 + Cancel v23 | Memory notes in place of cards |
| main v243 | No memory; code-written transcript of the conversation |
| Cancel v24 + Move v26 | A close title match shows the real booking's card |
| main v244 + Book Session v98 + Book Series v8 | No tool or prompt text tells the model to write a card |
| main v245 | "cancel it" / "book it" repeat only the same action |

## Test tools added
- `scripts/audit-model-text`: every text the model reads, checked for instructions to write a card or confirmation.
- `scripts/sim-transcript.js`: the transcript builder against made-up Slack histories (23 checks).
- `scripts/test-nodes`: 50+ new checks (card guard, claim forms, memory notes, transcript format, near titles, headings).
- `scripts/sim-repeat-yes.js`: 6 new cases for "cancel it" / "book it".

## Later on 8 Oct (21:44-23:26)

| Time | Build | What was tested | Result |
|---|---|---|---|
| 21:44 | v245 | "what time is studio 7 free tom" | **Wrong read**: "taken all day" for a 1-3 PM booking (Room Availability gave no times for a room asked about) |
| 22:02-22:09 | RA v20 + v246, Book v99 + v247 | Same question two ways, a set time, details, "no" to booking and cancel cards | Fixed: "booked 1:00 PM - 3:00 PM (...) - free the rest of the day" + "Free all day" (code); code replies to "no". New: a reasoning leak and an engineer ask; the Studio 3 reply still model-worded |
| 23:08-23:10 | RA v21 + v248 | Details, Studio 3 | Leak and engineer ask fixed; Studio 3 traced to Book Session's ROOM_UNSUITABLE |
| 23:25 | Book v100 | Studio 3 for VO, "still studio 3", "no" | Fixed: one fixed question, word for word; card with the note; code "no" reply |

| # | Issue | Fix | Status |
|---|---|---|---|
| 20 | Availability for a named room said "taken all day" for a part-day booking | RA v20 + main v246: times and free gaps for every room asked about, reply written in code | Fixed |
| 21 | Long model-written replies (the "no" reply, details questions, filler, recaps) | main v247 + Book v99: code "no" replies, brevity pass, length rule | Fixed (details questions that offer a choice are still model-worded) |
| 22 | Internal reasoning in a reply; an engineer asked for an engineer | main v248 | Fixed |
| 23 | "Not a usual room" replies worded by the model | Book v99 (last-resort rooms), RA v21 (availability), Book v100 (rooms in neither list) | Fixed |
| 24 | Booking lists ("what do I have booked", a set-time check answered from Find Booking / List Events) still written by the model | Phase 2: booking lists in code, List Events off the agent | Open (next) |
