# Launch checklist — QA/dev switches to flip for go-live

No launch date is set. This is the list of every QA/dev scaffold that must be turned off (or decided) before Jessie
serves real bookings, and how to do it. **Rewritten 27 Oct** against the live downloads: `./scripts/check-launch-switches`
reports 15 switch spots in 6 workflows (main, Slack Interactions, Cancel, Move, Reminders, Request Messages); Book
Session, Book Series, Room Availability, Find, Expand Series, Open Consent Request, Finalize, Sweep, Room Check, Log
Booking and Prune carry none.

Also in CLAUDE.md → *Before launch*; this doc is the reviewable detail.

## Before the flip

1. **Every build waiting to go in is imported** (the flip starts from the live downloads), and every QA fix is tested.
2. **Clear the QA test bookings** (2027 dates). After the flip My bookings shows the real year, so 2027 events drop out of
   view and are hard to find. Ask Claude for the list from the calendar (read-only) and delete them by hand.
3. **Decisions made** (section 3 and 4 below; PENDING 33).
4. Pick a time **away from the reminder runs** (4:00 PM daily, Monday 9:00 AM) - main, Slack Interactions and Reminders
   disagree about the year until all three are in.
5. Say it in Slack: nobody imports anything else while the flip is going in.

## 0. The flip, in one go (since 20 Oct)

Sections 1 and 2 are switched together by script, so no constant is missed and nothing else changes:

1. `./scripts/check-launch-switches` - every switch in what is live (the newest imported downloads). Must say
   **OK: QA**. MIXED means someone flipped part of it already; stop and find out.
2. `./scripts/flip-launch-switches` - writes the launch builds from the live downloads: each workflow that carries a
   switch, as its next build number titled `… — vN (launch switches)`, with YEAR_SHIFT 1 -> 0, DEV_REDIRECT -> `''`
   and main's prompt `.plus({ years: 1 })` removed. Nothing else in the files changes. (`--builds` starts from the
   newest builds instead, when candidates are waiting to go in at the same time.) Six files: main, Slack Interactions,
   Cancel, Move, Reminders, Request Messages.
3. `./scripts/check-launch-switches --builds` - must say **OK: LAUNCH**.
4. Import every file it wrote by the usual routine (download before + `check-import before`, Cmd+A -> Delete, import,
   Save, Publish, download after + `check-import after`), **in this order**:
   1. Cancel, Move, Request Messages (only who gets messages changes - safe on their own);
   2. then Reminders, Slack Interactions and main **back to back** (the year).
5. `./scripts/check-launch-switches` again on the after downloads - **OK: LAUNCH**.

Expected after the flip: `./scripts/test-forms` on the launch builds fails only the checks that assert QA mode (a date a
year ahead, a notice redirected to Howard - recount them on the launch builds before importing: run `test-forms` on the
QA builds and on the launch builds and compare the lists) and `./scripts/test-gate` expects 2027 dates; anything else
failing is a real problem. Recounted 28 Oct on a trial flip of the live downloads: **17 checks in 8 sims** (build-b 3, step-c1 1, slice1-a 1, round-3 1,
every-message 1, request-for 1, reminders 3, approvals 6) - `docs/launch-review-2026-10-28.md`. Going back to QA = re-importing the builds the flip started from (they stay in the repo).

## 1. Year shift → 0 (flip together)

QA runs on year-shifted 2027 dates. The model, the forms and the reminders must agree, so all change at once.

| Where | Constant | Now | Launch |
|---|---|---|---|
| main → `Gate Context` | `const YEAR_SHIFT = 1;` | `1` | `0` |
| main → agent system prompt (`Today's date is …`) | `.plus({ years: 1 })` | `+1 yr` | remove |
| Slack Interactions → `Build Step 1` (the form's dates), `My Window` (My bookings) | `const YEAR_SHIFT = 1;` | `1` | `0` |
| Reminders → `Window` (which day / week the reminders read) | `const YEAR_SHIFT = 1;` | `1` | `0` |

## 2. Notifications → real people

While testing, a message for anyone outside the QA roster (`ALLOW`: Howard, Camy) goes to Howard, marked "Test: this is
for X". At launch every `DEV_REDIRECT` becomes `''` and everyone gets their own.

| Workflow → node | What it routes |
|---|---|
| Cancel → `Build Recipients` | the cancel notice to the booker and the session's people |
| Move → `Build Recipients` | the move / change notice |
| Slack Interactions → `Booked Notices`, `Series Notices`, `Change Notices` | the engineer / arranger / "for" notices |
| Slack Interactions → `Request Act`, `Give Up Plan`, `Build Change C` | while testing Howard may answer a room request for anyone (a bypass, not a reroute) |
| Reminders → `Build Reminders` | the 4:00 PM and Monday 9:00 AM reminders |
| Request Messages → `Render` | every room-request message (the open request, the answers, the endings); `ALL_TO_DEV` beside it is `false` and inert once the redirect is `''` |

Since Open Consent Request v12 (21 Oct) the consent row keeps the real ids and carries no switch; the request messages
are routed in Request Messages. `ALLOW` is inert once the redirects are `''` - leave it or delete it.

Not a switch, but worth knowing: Slack Interactions' diagnostic messages (`Report Refused`, the `Report Open` fallbacks, `Ops Alert` since v46 - a failed sub-workflow call)
and the old hello test form (`Send Button`) are hard-coded to Howard - ops alerts keep going to Howard after launch.

## 3. `HAIST Dev` - decide (keep or pull)

`HAIST Dev` (Bookers `Authority` tag) bypasses the owner check **and** the department scope - a holder can move / cancel
**any** booking in **any** department, and request rooms as a coordinator. On **Howard, Genzo**. Decided 28 Sep to keep it
as an emergency backup (PENDING 33) - confirm before launch:

- **Keep:** do nothing.
- **Pull:** remove the tag from those Bookers records (Airtable). The code (`isHaistDev` in Cancel `Check Ownership`,
  Move `Resolve Booking`; the authority check in Slack Interactions `Build Step 2` / `Note Toggle`) can stay.

## 4. The model (Claude Haiku 5.5 since 8 Oct) - check before go-live

| What | Where | Launch |
|---|---|---|
| The Gemini fallback, once since memory was removed (main v243) | a test copy of main with a wrong model id on `Claude Haiku` | a short Slack round answered by Gemini (PENDING 101) |
| Console monthly spend limit | platform.claude.com -> Organization settings -> Billing / Limits | raise from $50 toward the monthly credit ($340) |
| Old Anthropic keys | platform.claude.com -> API keys | delete the two Organization-scoped keys; keep the workspace key behind `Anthropic account` |
| The `Claude Haiku` node | main | max tokens 8000, 2 tries; temperature / top P / top K / Enable Thinking unset |

## After flipping - verify (no n8n API access since 29 Sep: Slack and the downloads)

1. `./scripts/check-launch-switches` on the after downloads: **OK: LAUNCH**.
2. In Slack, as a non-dev colleague willing to help (not Howard): "hi" -> the menu; Book a room -> the date picker opens on
   **today's real date**; book a short test session with a colleague as the engineer -> **that colleague** gets the
   notice (no "Test: this is for …" line); cancel it -> the colleague gets the cancel notice.
3. "what do I have this week" -> the real week.
4. A room request (an M booth over a standing hold is the easiest): the **real holder** gets the message, not Howard.
   Deadlines: M booth - same day now + 3 h, tomorrow 10:00 on the booking day, 2+ days 24 h, capped at the start;
   priority - 24 h, but no later than 1 h before the session. Same-day and next-day requests only become reachable now
   (QA's 2027 dates always landed in the 24 h case), so watch the first ones.
5. The next 4:00 PM: the day-before reminders reach the real people.
6. Ask Howard to download one or two executions of each workflow from the first real bookings (Logs panel) if anything
   looks slow or silent.

## Already handled (no action)

- **`TEST_COORD`** (the hard-coded Howard coordinator) - removed 2026-09-21 (cancel-booking-v13, move-booking-v12).
  Authority is all real Airtable tags.

## How this list was verified (repeatable)

`./scripts/check-launch-switches` (live) and `--builds` (candidates) scan every Code node and main's prompt of the
switched workflows, check the ALLOW lists match and every DEV_REDIRECT points at the same person. They do not scan
Finalize, Sweep, Room Availability, Find, Expand Series or the Envoy Mirror (clean on 27 Oct) - a switch added there would
be missed, so add the workflow to the scripts' list if one ever is.
