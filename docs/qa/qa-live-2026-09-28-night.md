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
9. Minor: summaries inconsistent on "Booking Type" line (M1/M3 had it, M4/ORBIT did not).
10. Minor: F2 "this week" reply did not state the dates checked.
11. Minor: Localization picked Studio 1 / booth Studio A itself without asking, then refused them as taken (M2); celebrity picked Studio 7 itself (M3).
12. QA-N2: "Book ... 2pm to 4pm" then "actually make it 3pm instead" -> 3:00-4:00 PM "Assuming 1 hour" (exec 15819). The requested 2-hour length was dropped; a start change should keep the length (3-5 PM).
13. Minor (same pattern as 11): QA-M7 no room given -> Jessie chose Studio 7 herself and put it in the summary without asking (exec 15832). Otherwise correct: Spotify as client, new-client note, one question per gap. Not confirmed (a yes writes a New Clients row for Tel).
14. Minor: recurring-series summaries are model-written and omit Department and Booked by (C7). Prepared summaries for series are already on the after-launch list.

## Fixed tonight

- **Bug 1 → main v170, live 22:49 PHT.** A verified yes to a prepared summary books in code (Book Direct), Gemini not called. Verified live twice (B3 1 and 2): "Booked." in ~14 s, calendar entry carries "Booked by … | ref:". `scripts/sim-book-direct.js` checks the direct path sends Book Session exactly what the tool would.
- v169 (22:36–22:46) dropped the booker reference and was rolled back; see its commit.

## Worth deciding

- **Bugs 4 + 5 (Gemini 503s):** a fallback model on the agent, or longer retries (5 × 5 s); and the cancel "yes" could go direct the way booking now does.
- **Bugs 2, 3, 6, 12:** each is the model writing or choosing something code already knows. Same approach as the date guard and Book Direct.
