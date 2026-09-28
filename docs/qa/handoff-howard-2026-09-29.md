# Handoff to Howard: 28 Sep night QA

*From Tara, 29 Sep 2026. Live QA through Slack, 21:50 PHT 28 Sep to about 01:40 PHT 29 Sep. Full results:
[`qa-live-2026-09-28-night.md`](qa-live-2026-09-28-night.md).*

## What is live now

| Workflow | Build | Changed tonight |
|---|---|---|
| Project Jessie (main) | **v172** | yes: Book Direct (v170), fallback model (v171/v172) |
| Book Session | v55 | no |
| Move Booking | v23 | yours; snapshot saved as `workflows/move-booking-v23.json` |
| Refresh Reference Cache | new | yours; snapshot saved as `workflows/refresh-reference-cache-v1.json`. Main does not read it yet |

The n8n title on main still reads "v168 (v167 fixed)". v170–v172 were pushed without renaming it.

## The big one: "yes" did not book (fixed, main v170)

With Prepare Booking (v166), a "yes" to a prepared summary sometimes sent Gemini back to **Prepare Booking** instead of
**Book Session**. In M1 nothing was booked; in M4 the booking was made, but Jessie replied with a new "Confirm to
book." summary as if it hadn't been.

**Why no earlier test found it:** the eval twin never says yes, so no test went from summary to booking.
Tonight's run said yes and followed each booking through to the calendar, and it showed up on the first try.
**Going forward, QA needs to go through to the booking, not stop at the summary.**

**Fix (main v170):** after a verified "yes", code books it directly (`Book Direct?` → `Book Direct` → `Book Direct
Reply`), and Gemini is not called at all. It is faster (about 14 s) and can't be hit by a Google overload.
`scripts/sim-book-direct.js` checks that the direct path sends Book Session exactly what the tool would.

v169, the first attempt, dropped `Booked by … | ref:` from the event description, which made its bookings
impossible to cancel. It was live 10 minutes, then rolled back. v170 is the corrected version.

## Also fixed: Google overload errors (main v171/v172)

Gemini returned 503 "This model is currently experiencing high demand" on **17 of 90 turns** (paid tier). Each one
shows the user "Whoops, I ran into a tiny hiccup", and n8n still records the run as a *success*, so an error sweep
misses them.

The AI Agent was upgraded 1.7 → 2.2 with **Enable Fallback Model**. The new node **Gemini Fallback**
(`models/gemini-3.8-flash`) takes over when Flash Lite fails. It was proven live by deliberately breaking the primary
model's name: every reply then came from 3.8.

## 3.8 Flash on its own (tested, not adopted)

About 18 turns with 3.8 answering everything:

- **Better:** cancelling (looked the booking up first and showed the correct details); "is Studio 7 free at 2pm"
  (no invented end time); series summary now included Department. No 503s.
- **Worse:** slower, 16–29 s per turn (56 s to book a series).
- **Same:** most of the minor bugs below.

Main is back on Flash Lite, with 3.8 as the fallback. Making 3.8 the primary model is a decision still to make:
it is more accurate but slower. Bugs 3, 11 and 13 were not retested on 3.8.

## Remaining bugs

| # | Bug | Seen on | Notes |
|---|---|---|---|
| 5 | Cancel "yes" still goes through Gemini | Lite | Could go direct the way booking now does |
| 6 | Cancel card written by the model without Find Booking, showing an invented room/time | Lite | 3.8 did it correctly. The right booking was still cancelled |
| 12 | "actually make it 3pm instead" drops the length (2–4 PM → 3–4 PM, "Assuming 1 hour") | Lite and 3.8 | 3.8 asked how long, but "same length" still gave 3–4 |
| 2 | Studio 6 / Studio E offered as vocal booths (booths are A, B, D) | Lite; 3.8 lists E with the booths | |
| 3 | Internal instruction leaked into a reply ("Suggest one of those instead of Studio 7…") | Lite | Not retested on 3.8 |
| 11 / 13 | Jessie picks the room herself without asking | Lite | Not retested on 3.8 |
| 14 | Series summaries (model-written) have no Booked by line | Lite and 3.8 | 3.8 did include Department. Prepared series summaries are already on the after-launch list |
| 8 | Cancel_Booking called before showing the booking (guard refused `NOT_CONFIRMED`) | Lite | Guard held |
| 9 | "Booking Type" line appears in some summaries, not others | Lite and 3.8 | |
| 10 | "What do I have this week" reply doesn't say which dates it checked | Lite and 3.8 | |
| 15 | "free at 2pm?" answered "free from 2–4 PM" | Lite (v171) | Not seen on 3.8 |
| new | "VO in Studio 3": 3.8 said VO "isn't run" there and gave no option to book it anyway | 3.8 | Flash Lite flagged it and allowed it |

Bugs 2, 3, 6 and 12 are the model writing or choosing something the code already knows. The same approach as the
date guard and Book Direct would fix them.

## Clean-up

Every test booking was removed from the KDC calendar, including the 5-date QATESTC7B series and the QATEST38 booking
made during the 3.8 run. The booking log keeps their BOOKED rows; the events deleted directly from the calendar have
no CANCELLED row.

## Waiting on you: consent rebuild (candidates, not imported)

Everything ChatGPT's consent review flagged was confirmed in the code, and a simpler rebuild is built and tested
offline (`scripts/sim-consent.js` 52/52): main v176, Open v11, Finalize v10, Sweep v2, Book Session v57, Move v25.
In short: only a clear yes/no tied to one request counts; holds are never deleted any more (the requester is booked
alongside a standing hold, ignoring only that exact hold); Finalize re-reads the row and writes only if it is still
PENDING; each expired row is processed separately; timeout messages say it went ahead under the timeout rule.

Before it can be imported:
1. Add three column headers to the **Consent Requests** tab of the Jessie Log sheet: **Decision**, **Decision At**,
   **Placement Event Id** (Tara cannot edit the sheet's structure).
2. Set the standing M-booth holds that still block their booth to **"Show as available"**: M1 - Rico, M4 - Tel,
   M4 - Japs, M8 - ANA (M6 - Marketing and M2 - Peemo already are).
3. Then main v176 needs rebuilding on top of whatever main is live by then (`scripts/build-consent-fix.py` works
   from fresh pulls).
