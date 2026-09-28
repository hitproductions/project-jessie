# Handoff: Tara's session, 28 Sep 21:48 → 29 Sep 04:15 PHT

*For Howard. What changed, what is live, what is waiting on you. The QA-night detail (scenarios, bug list, 3.8
Flash comparison) is in [`qa/handoff-howard-2026-09-29.md`](qa/handoff-howard-2026-09-29.md). Build-by-build
detail: [`../VERSIONS.md`](../VERSIONS.md). Everything below is committed; nothing is pushed yet.*

## Live now

| Workflow | Build | Since (PHT) |
|---|---|---|
| Project Jessie (main) | **v177** | 29 Sep 04:08 |
| Book Session | **v58** | 29 Sep 04:08 |
| Cancel Booking | **v18** | 29 Sep 04:08 |
| Expand Series | **v4** | 29 Sep 04:08 |
| Room Availability | **v11** | 29 Sep 03:25 |
| Find Booking | **v6** | 29 Sep 03:25 |
| Move Booking | **v24** | 29 Sep 03:25 |
| Refresh Reference Cache | **v2** (your v1, tidied) | 29 Sep 02:54 |
| Book Series, consent workflows | unchanged | |

Last live check, 04:08: book → yes → cancel → yes, every node green, test booking removed.

## The big one: Prepare Booking's "yes" had not really been tested

Prepare Booking went live on 28 Sep at 16:28 PHT (main v166). What was tested before that was everything up to the
summary, not what happens when the requester says yes:
- **The eval twin never says yes.** By design it stops at the summary, so none of its 245 conversations reached a
  booking.
- **The one live booking** (v168, before QA) happened to work.

Tonight's QA said yes and followed each booking to the calendar, and the first tries failed. On **2 of 4 yeses** the
model called Prepare Booking again instead of Book Session:
- **M1:** nothing was booked.
- **M4:** it booked, but the reply was a fresh "Confirm to book." summary, as if it hadn't.

**Fixed in v170 (Book Direct):** a verified yes books in code, with no model call. The first attempt, v169, dropped
the booker reference from the event (so it couldn't be cancelled); it was live for 10 minutes before the rollback.
Tonight's live checks confirm the fix.

**The lesson for QA and the SOP testing: go through to the booking, not just to the summary.** The same gap exists
for **moves**: still model-written, and not tested with a real yes tonight. (A series was: 5 Tuesdays in November
booked correctly.)

## What changed, and why

**1. A "yes" no longer needs the AI (book and cancel).**
- Book (v170): a yes to a prepared summary books in code (see above).
- Cancel (v177 / Cancel v18): code writes the cancel card (with a check code over the event); a yes cancels
  exactly that booking, unchanged, or refuses. Fixes QA bugs 5, 6, 8.
- Live: book yes 9.6 s, cancel yes 7.5 s, **0 model calls**.

**2. Google overload no longer breaks turns (v171 / v172).** Gemini 503 "high demand" hit 17 of 90 turns. The agent
now has a fallback model (3.8 Flash) that takes over when Flash Lite fails.

**3. Reference data is cached (v173–v175).** Rooms, session types, staff and Get Booker come from the
`Jessie Reference Cache` data table (refreshed every 5 min, or on the spot if older than 15 min). About 3 s → 0.3 s
before the AI on every message. Your refresh workflow was writing blank rows because Build Cache passed 58 items
through; fixed in your 18:39 import, tidied in v2. Staff/authority changes now take up to 15 min (Tara's call).

**4. Booking correctness (ChatGPT review, verified in the code first).**
- Cancel/move no longer match an untitled event, and act only on one exact title or a verified id.
- All-day events are Manila midnight (a 6–7 AM booking used to slip past an all-day hold).
- A calendar read with a second page is refused, never read as "free" (not paged: busiest real day 16 events).
- Move keeps a room attendee even without the `resource` flag.

**5. Shorter replies.** One-line confirmation "Book it? / Cancel it? / Move it? Reply yes or no." (the old two lines
still confirm); shorter notes ("Assumed 1 hour (usual for VO Recording)."); one-line greetings; questions without
narration; series summary without an intro; "Something went wrong - please try again."

Every change: offline suites (test-nodes 462, gate 37, plus a new sim per change), then pulled back to confirm what
n8n stored.

## Waiting on you

1. **Consent rebuild** — built and tested (`sim-consent.js` 52/52), not imported. Needs, first:
   - three columns on the Consent Requests tab: **Decision**, **Decision At**, **Placement Event Id**;
   - the standing holds that still block their booth set to **"Show as available"**: M1 - Rico, M4 - Tel,
     M4 - Japs, M8 - ANA.
   Then rebuild on the live main (`scripts/build-consent-fix.py` works from fresh pulls). Details in the QA handoff.
   **Also in this pass — Read Pending Consent speed.** main reads the whole Consent Requests sheet on every message
   (~1.1 s, measured tonight, the biggest pre-AI cost left) to see whether the sender owes a consent answer. Fix: the
   cache refresh also stores who has a PENDING request; main reads the sheet only when the sender is on that list,
   and falls back to reading it when the list is unavailable. Open Consent Request must refresh the cache right after
   writing a request and **before** DMing the holder, or a quick "yes" is missed. Small remaining window: two
   refreshes overlapping could write an older list — say how you close it. Test it with the consent live test.
2. **Recurring bookings** — ChatGPT's review, below. Not yet checked against the code. Its earlier reviews were
   mostly right (one pagination claim was not worth the change), so verify each point before building.
3. **Push** everything to GitHub once you have pulled and looked.

## Decided tonight (Tara)

- Keep Flash Lite as the main model, 3.8 Flash as the fallback.
- Get Booker from the cache (15-minute delay on staff changes is fine).
- Consent: the simpler design — never delete a hold.
- Not now: splitting the prompt / per-task tools (the AI path already averages 1–2 calls a turn), trimming the booking
  summary's lines, "what's free today" listing style.
- Later: availability answers inventing an end time (bug 15).

## Live QA, 29 Sep ~04:30 PHT (on the live builds)

All test events deleted afterwards; the calendar was checked after every write.

| Test | Result |
|---|---|
| Cancel someone else's booking (seeded event, foreign booker) | ✅ refused at the card, nothing offered |
| Taglish booking ("pa-book … sa Friday next week … si Tara ang engineer") | ✅ right date, engineer and room |
| Conditional yes ("yes pero gawin mong 3pm to 5pm") | ✅ not booked |
| Yes → Book Direct | ✅ booked, 0 AI calls, exactly one event |
| A second "yes" after "Booked." | ⚠️ no double booking, but a confusing reply (bug 17) |
| Move an owned booking (first real-yes move since Prepare Booking) | ✅ moved, room kept, original removed |
| Series with one date taken | ⚠️ first yes did nothing (bug 18); second yes booked 4 and reported the skipped date correctly |

New bugs:
- **18 (major): a series "yes" can re-send the summary instead of booking.** The gate saw the yes; the AI called
  Expand Series again. Same failure Book Direct fixed for single bookings. Fix direction: a code-written series
  summary with a check code and a direct path (the recurring-bookings review, point 2). Intermittent: the 28 Sep
  series yes booked first time.
- **16: "Friday next week" is read by the date guard as this Friday** → a needless "October 1 or October 8?"
  question. Same family: "every Tuesday in November" set the date under discussion to this Tuesday (5 Oct), which
  likely confused the model in bug 18.
- **17 (minor): a repeated "yes" after "Booked."** gets "Studio 8 is taken … by QATESTTG" (their own booking) and
  alternatives. Should say "Already booked."
- Bug 9 again (Booking Type line on one summary only). Move summary doesn't show the old time.

## Still open from QA

Bugs 2, 3, 9, 10, 11/13, 12, 14, 15 — see the QA handoff. 5, 6, 8 are fixed by Prepare Cancel.

---

## Appendix: recurring bookings review (from ChatGPT, for Howard)

> Next, improve Jessie's recurring-booking workflows. Use the latest files and preserve the previous caching, booking,
> consent, confirmation, background-job, and AI optimizations. Focus on Expand Series, Book Series, and their
> connections to Project Jessie and Book Session.
>
> 1. **Fix recurrence validation.** Reject nonexistent dates instead of silently normalizing them (February 30 must
>    not become March 2). Validate hours 00–23 and minutes 00–59. Require a positive integer count when using count.
>    Require exactly one end condition: count or until_date, preserving the caller's existing "unused count"
>    convention, such as 0. Reject invalid weekday codes rather than silently dropping them. Preserve the existing
>    16-occurrence limit and one-year maximum. Handle overnight sessions explicitly according to existing booking
>    policy; never silently reinterpret reversed times.
> 2. **Keep preview and execution consistent.** Use one shared recurrence implementation, or verify both copies with
>    identical tests. The exact dates, times, rooms, and booking details confirmed by the requester must be the ones
>    executed. Do not regenerate a different series from new AI arguments after confirmation. Apply the existing
>    structured confirmation mechanism to series where needed.
> 3. **Resolve shared details once.** Resolve staff, client, session type, and room reference information once per
>    series and pass it to each occurrence. Use the existing cache and staff_data mechanism where appropriate. Inspect
>    Book Session's actual inputs and update mappings so the information reaches it. Preserve live authorization and
>    fresh conflict checks for each calendar mutation.
> 4. **Make partial completion and retries reliable.** Assign a stable series action ID and occurrence IDs. Persist
>    each occurrence's outcome and created event ID. On retry, reconcile uncertain outcomes and resume unfinished
>    occurrences without recreating successful ones. Preserve the existing behavior of retaining successful bookings
>    when other dates fail or conflict. Do not introduce automatic rollback of the entire series.
> 5. **Report every occurrence accurately.** Correlate results by occurrence ID rather than array position alone.
>    Distinguish created, conflict/skipped, pending consent, rejected, failed, and uncertain outcomes. Never say the
>    whole series was booked unless every occurrence succeeded. A failure after some successful writes must still
>    leave a recoverable record of those successes.
> 6. **Optimize without introducing booking races.** Reuse shared lookups first. Do not blindly parallelize calendar
>    writes. Any concurrency must respect resource overlap, existing locking, API limits, and retry behavior. Use the
>    background-job mechanism for reporting and secondary notifications.
> 7. **Test.** Cover leap years, invalid dates/times, fractional counts, both/neither end conditions, weekday
>    selection, overnight policy, Manila all-day boundaries, occurrence limits, partial conflicts, mid-series API
>    failure, duplicate requests, and retry after partial completion. Measure external lookup counts and execution
>    time where possible.
>
> Return corrected importable JSONs, tests and results, any required state-schema changes, and a short summary of the
> improvement.

Notes for checking it:
- The **series summary is still model-written** (the "after launch" item in CLAUDE.md). Point 2 is really "Prepare
  Series": code writes the series summary with a check code, like Prepare Booking and Prepare Cancel.
- "Background-job mechanism" and "existing locking" do not exist in Jessie — nothing like that was built tonight.
- Tonight's series test (Nov 2027, 5 Tuesdays) booked correctly; its summary lacked Booked by (bug 14).
