# Handoff: Tara's session, 28 Sep 21:48 → 29 Sep 05:00 PHT

*For Howard. Build detail: [`../VERSIONS.md`](../VERSIONS.md). QA-night detail: [`qa/handoff-howard-2026-09-29.md`](qa/handoff-howard-2026-09-29.md).*

## Live now

| Workflow | Build |
|---|---|
| Project Jessie (main) | **v180** |
| Book Session | **v58** |
| Cancel Booking | **v18** |
| Room Availability · Find · Move | **v11 · v6 · v24** |
| Expand Series | **v4** |
| Refresh Reference Cache | **v2** (your v1, tidied) |
| Book Series, consent workflows | unchanged |

## The big one: Prepare Booking's "yes" was never really tested

Prepare Booking (v166, live 28 Sep 16:28) was tested up to the summary only: the eval twin never says yes, and the
one live booking happened to work. In QA, **2 of 4 yeses failed**: the model re-prepared instead of booking (once
nothing was booked, once it booked but replied with a fresh summary). **Fixed in v170:** a verified yes books in code.
**For QA and the SOP: always go through to the booking.** Tonight's live QA did, for book, cancel, move and series.

## What changed

1. **"Yes" skips the AI for book and cancel.** Book Direct (v170). Cancel: code writes the cancel card with a check
   code; a yes cancels exactly that booking or refuses (v177 / Cancel v18). Fixes QA bugs 5, 6, 8.
2. **Fallback model** (v171/v172): 3.8 Flash answers when Flash Lite returns Google's 503 (17 of 90 turns).
3. **Reference cache** (v173–v175): rooms, session types, staff and Get Booker from the data table. Staff changes
   take up to 15 min (Tara's call).
4. **Booking correctness** (ChatGPT review, checked in code): untitled or partial titles no longer match for
   cancel/move; all-day events are Manila midnight; a calendar read with a second page is refused, never "free";
   move keeps unflagged room attendees.
5. **Shorter replies:** "Book it? / Cancel it? / Move it? Reply yes or no." (old form still confirms); shorter notes,
   greetings, questions, series summary and error message.
6. **QA bugs 16–18** (v178–v180): "Friday next week" and "every Tuesday" read correctly; a repeated yes gets
   "That's already booked"; a series yes now books first time (the model is told the series is approved).

## Tested tonight (live, 2027 test bookings, all deleted)

Passed: book → yes (no AI) · cancel card → yes (no AI) · cancel someone else's booking → refused · Taglish request ·
conditional yes not booked · repeated yes · move an owned booking · series with a taken date (4 booked, 1 reported
skipped) · series yes after v180.

**Speed** (medians, same kinds of turns as the 28 Sep QA): all turns **16.4 s → 9.0 s**; booking request → summary
18.5 → 9.0 s; yes to a cancel 17.8 → 7.5 s; a 5-date series 40 → 36 s (Book Session per date, untouched).

## Waiting on you

1. **Consent rebuild**, built and tested offline, not imported. Needs first:
   - columns **Decision**, **Decision At**, **Placement Event Id** on the Consent Requests tab;
   - standing holds that block their booth set to **"Show as available"**: M1 - Rico, M4 - Tel, M4 - Japs, M8 - ANA.

   Then rebuild on the live main with `scripts/build-consent-fix.py`. In the same pass: **Read Pending Consent**
   costs ~1.1 s on every message. Keep the pending approvers in the cache; Open Consent Request must refresh it
   after writing a request and before DMing the holder.
2. **Recurring bookings review**: [`review-recurring-bookings.md`](review-recurring-bookings.md). Not yet checked
   against the code. The real gap: series summaries are still AI-written (a code-written summary with a check code
   would make the series yes deterministic, like Prepare Booking).

## Decided (Tara)

Flash Lite main, 3.8 Flash fallback · Get Booker cached · consent: never delete a hold · not now: prompt split,
trimming the booking summary, "what's free" wording · later: invented availability end time (bug 15).

## Open bugs

- **19 (new):** the series summary labelled December Tuesdays "(Mon)". Guard Probe fixes weekdays only on dates
  written with a year. The booking itself was right.
- 2 wrong rooms offered as vocal booths · 3 tool instruction leaked into a reply · 9 Booking Type line comes and
  goes · 10 "this week" doesn't state its dates · 11/13 room picked without asking · 12 "make it 3pm instead" drops
  the length · 14 series summary lacks Booked by · 15 invented availability end time · move summary lacks the old time.
