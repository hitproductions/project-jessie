# Pre-launch review - 28 Oct 2026 (afternoon)

What is live, what was checked, and what is left before the flip. Steps for the flip itself: [`launch-checklist.md`](launch-checklist.md).

## What is live

main v285 · Book Session v124 · Slack Interactions v52 · Move v41 · Cancel v33 · Room Availability v24 · Reminders v7 ·
Request Messages v5 · Consent Sweep v4 · Log Booking v3 · Room Check v2 · Find v8 · Book Series v8 · Open Consent Request v12 ·
Finalize v11. Every import this week matched its build before and after.

## Offline checks (files only, on the live downloads)

| Check | Result |
|---|---|
| `test-forms` (every Slack-app sim) | 53 of 53 pass |
| `test-nodes` (main, Book Session, Cancel, Find, Move downloads) | 574 checks + 69 gate scenarios pass |
| `audit-model-text`, `check-fromai` (main v285) | clean |
| `test-dates`, `test-consent`, the chat sims in `test-all` | pass |
| `check-launch-switches` | OK: QA (15 spots, ALLOW lists match) |
| Trial flip in a scratch copy (`flip-launch-switches`, then `--builds`) | OK: LAUNCH - six files: main v286, SI v53, Cancel v34, Move v42, Reminders v8, Request Messages v6 |

`test-all --local` reports test-gate / test-nodes failures: it reads its own pulls from before 29 Sep (`diagnostics/test-all/live/`,
main ~v190), not the live downloads. Not a live problem; run `test-nodes` with the five download paths instead.

**After the flip, `test-forms` on the launch builds fails 17 checks in 8 sims, all of them QA-mode checks** (a date a year
ahead, a message redirected to Howard / marked "Test: …", the year shift in the prompt): build-b 3, step-c1 1, slice1-a 1,
round-3 1, every-message 1, request-for 1, reminders 3, approvals 6. Anything else failing on the launch builds is real.

## Blocker found

**The Consent Requests tab still has no Claim column** (read 28 Oct: headers end at AC `_sweepAction`). Since Slack Interactions
v49 / Sweep v4 every request answer writes a claim to that column and reads it back; without the header nothing is read back,
so **every Approve / Give it up / Keep does nothing** (PENDING 121 / 122). Fix: type `Claim` in **AD1**. Then test one room request.

## Data to clear before the flip (Howard; Claude lists, never deletes)

- **Calendar:** 87 one-off test bookings dated 2027 (Jessie-made, from GUARDCHK on 10 Sep 2027 to BREAD STICKS on 10 Nov 2027).
  The 2027 instances of the standing series (KATHA - S&A, SALIN - BD, SALIN - MUSIC DEPT, M1 - Rico, M4 - Japs, M6 - Marketing,
  M7 - ANA) are real - leave them. No Jessie test bookings are on real 2026 dates from today on.
- **Jessie Booking Log sheet:** the test rows in Log (incl. the "LOGTEST / throwaway - delete me" row), Consent Requests,
  New Clients (all 2027 test clients) and New Projects (NET-BGC, NET-TST, TEST-QA-01, NET-TSTING). Keep the header rows. Turn Log is
  the old chat log - archive or leave.

## Slack tests still owed (all live, none tested yet)

1. **Room requests, after the Claim header** (121 / 122 / 126): a request on someone's booking -> answer it -> placed; two answers
   at once -> one counts; change the booking in the way -> the request follows it or ends; the placed booking's engineer is told;
   the request says who it is for.
2. **Launch fixes** (125 / 127 / 128 / 129): a note with a name in it is not read as a person (reminder, My bookings); Change ->
   "Did you mean …?" with the window closed -> Continue changing in the DM; Series / Change notices carry the "for" line; Move's
   notice says "changed" vs "moved".
3. **New clients** (133 / 135): a new client on Change -> a New Clients row with "Close to"; a new client booked by Business
   Development -> Type: Advertising, not Internal.
4. **Titles** (134): a project typed "Backyard Live // Test Session" -> "BACKYARD LIVE - TEST SESSION / …".
5. **Atmos** (136 / 138): Atmos Mixing -> Project title or code, Department, Studio C; at a taken time, Studio C's bookings that day
   under the notice.
6. **No ref:** (124): a hand-made booking with only "Booked by: <name>" -> Booked – ask to use offers it; an M booth hold reads
   "M6 · Marketing".
7. **Continue booking** (SI v45): close the window at step 2's question -> the DM reopens step 2.

QA round 4's own results are still not in the repo (PENDING 130) - if anything on Camy's sheet failed and was not reported, it is
not fixed.

## Decisions still open (Howard)

- **33 HAIST Dev** - keep (decided 28 Sep as a backup) or pull.
- **101 The model** - raise the Console spend limit from $50; delete the two Organization-scoped keys; test or accept the Gemini fallback.
- **123** Studio M posts to #isr--mrk--studio_m (Zapier) - keep or change.
- **118** Cancel a whole repeating booking at once - after launch is fine (each date can be cancelled now).

## Not code, still open

15 uptime monitor · 21 Cloudflare late deliveries (watch the first days) · 42 Envoy tablets · 43 the old Studio E calendar id
(IT) · 114 / 53 Airtable cleanup.

## Known, not built - fine to launch with

- Room Availability counts a room that declined an event, and a "free" (transparent) event, as taken - it can hide a free room, never
  double-book one.
- A request card shows the old time after the booking in the way was changed.
- 115 Coordinators cannot find someone else's booking by typing (they can through the form's taken-room list).
- 137 Hand-made bookings: backfill after the formal launch (decided today).
- `test-all --local` reads stale pulls (above).

## Recommendation

Freeze the builds: no new builds before the flip unless a Slack test fails. Order for tomorrow: Claim header -> the owed Slack
tests (request flow first) -> clear test data -> decisions 33 / 101 -> the flip (`launch-checklist.md` section 0) -> the after-flip
checks with a non-dev colleague.
