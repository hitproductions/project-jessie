# Live QA run: the QA-sheet scenarios, through Slack

*28 Sep 2026, 21:50–23:05 PHT. Tara's DM with Jessie; main v168, then v170 from 22:49. Real bookings, said "yes",
then cancelled. Unlike the eval twin this run says yes, so it exercises the yes → booked path.*

## Results

| Scenario | Result | Notes |
|---|---|---|
| A2 list all rooms | ✅ | all 27 |
| A3 vocal booths / in-room vocals | ✅ | A, B, D / 7, 8, C, D, F — matches Airtable |
| A4 5.1 rooms | ✅ | 3, 4, 5, 6, C |
| F1a what's booked in Studio 4 next Thursday | ✅ | 7 Oct, correct and empty |
| F1b is Studio 7 free next Thursday 2pm | ✅ | |
| F2 what do I have this week | ✅ | 27 Sep–3 Oct correct; reply doesn't state the dates (bug 10) |
| E3a "studio one" / E3b "std 3" | ✅ | |
| M1 VO in Studio 3 | ⚠️ | deviation flagged correctly; first yes did not book (bug 1) |
| M2 Localization KUBA, Jek | ⚠️ | NET-KUBA / FP correct; "booths" list included Studio 6 and E (bug 2) |
| M3 celebrity recording | ⚠️ | Music-or-Audio-Post asked ✅; instruction leaked (bug 3) |
| M4 VO "at 2pm" only | ⚠️ | 1 h assumed and stated ✅; yes booked but reply was a fresh summary (bug 1) |
| M7 session for Spotify | ✅ | Spotify as client, new-client note; not confirmed (would write a New Clients row) |
| B3 two bookings in one thread | ✅ | second inherited nothing; "Richard" → Richard Genabe (RG); both booked via v170 |
| N2 "actually make it 3pm instead" | ❌ | became 3–4 PM, length dropped (bug 12) |
| C7 every Tuesday for the next month | ✅ | 5/12/19/26 Oct booked; model-written summary lacks Department / Booked by (bug 14) |
| E1 no date, no details | ✅ | asked everything including the date |
| E2 last Monday | ✅ | refused as past (27 Sep) |
| E3c "the big room" for a meeting | ✅ | asked which conference room |
| E4 "for Jem Lim's new ad" | ✅ | Jem Lim as client (eval: asked 5/5 before) |
| X4 cancel my Studio 7 booking on Oct 20 | ✅ | none found, said plainly |

**21 scenarios: 15 pass, 5 pass with a bug, 1 fail.** Every test booking was removed afterwards (11 events; the
booking log keeps their BOOKED rows — the 7 deleted directly from the calendar have no CANCELLED row).

## Bugs
1. "yes" to a prepared summary: Gemini re-called Prepare Booking instead of Book Session (M1: nothing booked; M4: booked but reply was a fresh "Confirm to book." summary). FIX: main v170 books a verified yes in code (live 14:49 UTC).
2. Localization booth list offered Studio 6 and Studio E as "booths" (M2). Vocal booths are only A, B, D.
3. Internal instruction leaked into reply (M3): "Suggest one of those instead of Studio 7. If they say to go ahead with what they asked for, book it."
4. Google Gemini 503 "high demand" on ~1 in 4 turns tonight (US morning); each gives "Whoops, I ran into a tiny hiccup". Retries: 3 x 2 s. Runs count as "success", so error sweeps miss them.
5. Cancel "yes" still goes through Gemini: a 503 there left M2 uncancelled; the user must ask again (a bare "yes" no longer counts after the hiccup message).
6. Cancel confirmation card written by the model without Find Booking; M4's card showed an invented room/time (Studio 8, 2-4 PM vs real Studio 7, 2-3 PM). Correct booking was still cancelled (Cancel Booking matches title+date).
7. (mine, fixed) v169 direct bookings lacked "Booked by ... | ref:" -> uncancellable. Rolled back after 10 min; v170 fixes; sim-book-direct.js guards it.
8. Minor: Gemini called Cancel_Booking before showing the booking (refused NOT_CONFIRMED, guard held) - M2, M4, ORBIT.
9. Minor: summaries inconsistent on "Booking Type" line (M1/M3 had it, M4/ORBIT did not). ROOT CAUSE (29 Sep): the line was left out whenever the model sent no booking type - Check Conflicts worked it out for the event, Render Summary showed the empty input. Fix: Book Session v64.
10. Minor: F2 "this week" reply did not state the dates checked.
11. Minor: Localization picked Studio 1 / booth Studio A itself without asking, then refused them as taken (M2); celebrity picked Studio 7 itself (M3).
12. QA-N2: "Book ... 2pm to 4pm" then "actually make it 3pm instead" -> 3:00-4:00 PM "Assuming 1 hour" (exec 15819). The requested 2-hour length was dropped; a start change should keep the length (3-5 PM).
13. Minor (same pattern as 11): QA-M7 no room given -> Jessie chose Studio 7 herself and put it in the summary without asking (exec 15832). Otherwise correct: Spotify as client, new-client note, one question per gap. Not confirmed (a yes writes a New Clients row for Tel).
15. Minor: v171 'is studio 7 free next thursday at 2pm?' -> 'free ... from 2:00 PM to 4:00 PM' (exec 15881): an end time nobody gave; v168 said 'at 2:00 PM'.
14. Minor: recurring-series summaries are model-written and omit Department and Booked by (C7). Prepared summaries for series are already on the after-launch list.

## Fixed tonight

- **Bug 1 → main v170, live 22:49 PHT.** A verified yes to a prepared summary books in code (Book Direct), Gemini not called. Verified live twice (B3 1 and 2): "Booked." in ~14 s, calendar entry carries "Booked by … | ref:". `scripts/sim-book-direct.js` checks the direct path sends Book Session exactly what the tool would.
- v169 (22:36–22:46) dropped the booker reference and was rolled back; see its commit.

- **Bug 4 → main v171, live 23:16 PHT.** AI Agent upgraded 1.7 → 2.2 with *Enable Fallback Model*; a second model node **Gemini Fallback** (`models/gemini-3.8-flash` since v172, 23:20 PHT — first `gemini-2.5-flash`, swapped because Google limits 2.5 access and recommends 3.8 Flash; same credential and retries) takes over when Flash Lite fails. Proven live: with the primary model name deliberately broken for one message (exec 15884), both primary calls failed and the fallback answered correctly with a tool call; v171 restored 27 s later. Normal turn on v171 (exec 15881): tools, memory, Guard Probe and intermediate steps all working, primary only.

## Worth deciding

- **Bug 5:** the cancel "yes" could go direct the way booking now does (the fallback model already makes a 503 there much less likely).
- **Bugs 2, 3, 6, 12:** each is the model writing or choosing something code already knows. Same approach as the date guard and Book Direct.

## 3.8 Flash as the only model (about 23:21 PHT to 01:30 PHT)

Primary model name deliberately broken so the fallback (gemini-3.8-flash) answered every turn; main v172 restored
afterwards and verified identical. Raw log below. Comparison and next steps: [handoff-howard-2026-09-29.md](handoff-howard-2026-09-29.md).
### 3.8 Flash as the only model (fallback test window, from 15:21:51 UTC)
- A2 list rooms: all 27 ✅; grouped Studio E under "Recording / Vocal Booths" (Room Type says Recording Booth, Vocal Booth flag not set - prompt says use the flag). Same family as bug 2. "Studio M (Van)" is correct (Room Type: Van).
- M1 VO in Studio 3: 3.8 said "VO recording isnt run in Studio 3" and offered only 7/8/F - no option to proceed anyway (Flash Lite offered it). Overstates the rule; the ranking is a recommendation (exec 15895). F2 same as Flash Lite (no dates stated).

### 3.8-only — N2 "actually make it 3pm instead" (execs 15910/15913/15916)
- Asked "How long will the session run…?" instead of silently making it 3–4 (better than Flash Lite's bug 12).
- BUG 12 persists in another form: after "same length", Prepare Booking summary = 3:00–4:00 PM with
  "Assuming 1 hour, the usual VO Recording length". Original was 2–4 PM (2 h); expected 3–5 PM.
  Looks like 3.8 passed no end time and the code default filled 1 h.
- Bug 9 seen again: first summary had no *Booking Type:* line, the second one had "External".
- Speed: 24.5 s / 28.2 s / 19.9 s.

### 3.8-only — C7 series "every Tuesday in November" (execs 15923/15926)
- PASS: Expand Series gave Nov 2/9/16/23/30 2027 (correct Tuesdays); Book Series booked all 5, 10:00–12:00,
  Studio 7 resource accepted, description carries Booked by + ref:. All 5 deleted afterwards (test cleanup).
- Bug 14 partial: summary now has Department, but still no *Booked by:* line; Engineer shown without role;
  no *Booking Type:* line.
- No Room_Availability call before the series summary (Book Series checks at booking time, so no wrong booking).
- "yes" went through the model again (series isn't on Book Direct) — 56 s turn.

### 3.8-only — bug 15 check "is Studio 7 free at 2pm next Wednesday?" (exec 15935)
- PASS: "Yes, Studio 7 is free at 2:00 PM next Wednesday (October 6, 2027). How long would you need the room for?"
  No invented 2–4 PM window. Two Room_Availability calls (redundant, harmless). 18.3 s.
