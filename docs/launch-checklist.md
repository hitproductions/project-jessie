# Launch checklist — QA/dev switches to flip for go-live

No launch date is set. This is the authoritative list of every QA/dev scaffold that must be
turned off (or decided) before Jessie serves real bookings. Verified against the **live** workflows
on 2026-09-21 by grepping each for the markers below — nothing else carries them (Book Session,
Find, Room Availability, Expand Series, Book Series, Prune are clean).

Also in CLAUDE.md → *Before launch*; this doc is the reviewable detail.

## 0. The flip, in one go (since 20 Oct)

Sections 1 and 2 are switched together by script, so no constant is missed and nothing else changes:

1. `./scripts/check-launch-switches` - every switch in what is live (the newest imported downloads). Must say
   **OK: QA**. MIXED means someone flipped part of it already; stop and find out.
2. `./scripts/flip-launch-switches` - writes the launch builds from the live downloads: each workflow that carries a
   switch, as its next build number titled `… — vN (launch switches)`, with YEAR_SHIFT 1 -> 0, DEV_REDIRECT -> `''`
   and main's prompt `.plus({ years: 1 })` removed. Nothing else in the files changes. (`--builds` starts from the
   newest builds instead, when candidates are waiting to go in at the same time.)
3. `./scripts/check-launch-switches --builds` - must say **OK: LAUNCH**.
4. Import every file it wrote, the same evening, by the usual routine (download before + `check-import before`,
   Cmd+A -> Delete, import, Save, Publish, download after + `check-import after`). Open Consent Request is imported
   from the 29 Sep snapshot's flip - never from the unimported `open-consent-request-v11.json` candidate.
5. `./scripts/check-launch-switches` again on the after downloads - **OK: LAUNCH**.

Expected after the flip: `./scripts/test-forms` on the launch builds fails exactly the checks that assert QA mode
(a date a year ahead, a notice redirected to Howard - 8 checks in build-b, step-c1, slice1-a, round-3, every-message,
reminders on 20 Oct) and `./scripts/test-gate` expects 2027 dates; anything else failing is a real problem.
Going back to QA = re-importing the builds the flip started from (they stay in the repo).

## 1. Year shift → 0 (flip both together)

QA runs on year-shifted 2027 dates. The model and the guards must agree, so both change at once.

| Where | Constant | Now | Launch |
|---|---|---|---|
| main → `Gate Context` node | `const YEAR_SHIFT = 1;` | `1` | `0` |
| main → agent system prompt (`Today's date is …`) | `.plus({ years: 1 })` | `+1 yr` | remove |
| `Jessie — Slack Interactions` → `Build Step 1` (the form's dates) and `My Window` (My bookings) | `const YEAR_SHIFT = 1;` | `1` | `0` |
| `Jessie — Reminders` → `Window` (which day / week the reminders read) | `const YEAR_SHIFT = 1;` | `1` | `0` |

If only one changes, "next Thursday" and "is this date in the past" break. `./scripts/test-gate`
expects 2027 dates today, so update those expectations too when you flip.

## 2. Notification dev-redirect → real people

While building, every authorized-change notification is rerouted to a dev inbox so real staff aren't
pinged. Flip one constant per sub-workflow and notifications go to the real booker + engineer.

| Where | Constant | Now | Launch |
|---|---|---|---|
| `Cancel Booking` → `Build Recipients` | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` |
| `Move Booking` → `Build Recipients` | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` |
| **`Open Consent Request` → `Build Request`** (consent engine) | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` | *(until Open Consent Request v12 is imported - from v12 the row keeps the real ids and the redirect is in Request Messages, below)*
| **`Jessie — Request Messages` → `Render`** (slice 2, 21 Oct: every message of a room request) | `const DEV_REDIRECT = '…';` (+ `ALL_TO_DEV = true`: every request message to Howard, the QA roster included - inert once the redirect is `''`) | `'U08V3CKDGJF'` (Howard) | `''` |
| **`Jessie — Slack Interactions` → `Request Act`, `Give Up Plan`** (v37: Howard answers a request for whoever it is for while testing) | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` |
| **`Jessie — Slack Interactions` → `Booked Notices`, `Series Notices`, `Change Notices`** (v18+, engineer / arranger notices) | `const DEV_REDIRECT = '…';` (one constant in `NOTICE_JS`, `scripts/build-slack-interactions-vN.py` - rebuild with `''`) | `'U08V3CKDGJF'` (Howard) | `''` |
| **`Jessie — Reminders` → `Build Reminders`** (the 4:00 PM day-before and Monday 9:00 AM DMs, since 20 Oct) | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard; a redirected reminder says "Test: this reminder is for X") | `''` |

**The consent engine has its own switch** (added 2026-09-22; missing from this list until 2026-09-25).
It routes each consent row's Approver and Requester, which every consent DM downstream reads (Open,
Finalize, the main-workflow router). If Cancel/Move are flipped and this one isn't, every M-booth and
priority request at launch still DMs Howard instead of the real booth holder / incumbent. The real
booking is still the one moved or placed; only the messages go to the wrong person.

Once `DEV_REDIRECT = ''`, the `ALLOW` list beside it is inert (everyone is notified for real), so it
needs no change — leave it or delete it. During QA round 2 all three `ALLOW` lists hold the dev + QA
roster (Howard, Trish, Camy, Jess, Tel, Tara, Genzo), and since 2026-09-24 the Cancel/Move **engineer**
notice honors `ALLOW` too (it used to always redirect). All of that is moot once the redirects are `''`.

## 3. `HAIST Dev` god-mode — decide (keep or pull)

`HAIST Dev` (Bookers `Authority` tag) bypasses the owner check **and** the department scope — a
holder can move/cancel **any** booking in **any** department. Currently on **Howard, Genzo** (Tel left the dev team 19 Oct; her tag removed 21 Oct).
Not a code flip — a decision:

- **Keep** (devs retain god-mode after launch): do nothing.
- **Pull:** remove the `HAIST Dev` tag from those Bookers records (Airtable), and optionally remove
  the `isHaistDev` clause in `Check Ownership` (Cancel) and `Resolve Booking` (Move).

Enforced via `isHaistDev` in Cancel/Move. See `docs/design/booking-authority.md`.

## 4. The model (Claude Haiku 5.5 since 8 Oct) - check before go-live

| What | Where | Launch |
|---|---|---|
| The Gemini fallback, once since memory was removed (main v243) | a test copy of main with a wrong model id on `Claude Haiku` | a short Slack round answered by Gemini (PENDING 101) |
| Console monthly spend limit | platform.claude.com -> Organization settings -> Billing / Limits | raise from $50 toward the monthly credit ($340) |
| Old Anthropic keys | platform.claude.com -> API keys | delete the two Organization-scoped keys; keep the workspace key behind `Anthropic account` |
| The `Claude Haiku` node | main | max tokens 8000, 2 tries; temperature / top P / top K / Enable Thinking unset |

## Already handled (no action)

- **`TEST_COORD`** (the hard-coded Howard coordinator) — **removed** 2026-09-21 (cancel-booking-v13,
  move-booking-v12). Authority is now all real Airtable tags.

## After flipping — verify

1. `./scripts/test-nodes --live` and `./scripts/test-gate` (update the 2027 date expectations first).
2. A live DM: confirm a relative date resolves to the **real** year, and that an authorized change
   DMs the **real** booker/engineer (no `[DEV]` prefix).
3. A consent request (an M-booth over a standing hold is the easiest): the **real holder** gets the DM,
   not Howard. **Consent deadlines** (`Open Consent Request` → `Build Request`, v10 since 2026-09-25):
   M-booth uses the confirmed tiers (same day = now + 3h, tomorrow = 10:00 on the booking day, 2+ days =
   24h, capped at the session start); priority (PREEMPT) keeps *24h, but no later than 1h before the
   session*. Same-day and next-day requests only become reachable now (QA's 2027 dates always landed in the
   24h case), so watch the first ones. `./scripts/test-consent --live` checks both.
4. `./scripts/health` — every node green.

## How this list was verified (repeatable)

Since 20 Oct: `./scripts/check-launch-switches` (live) and `--builds` (candidates) scan every Code node and main's
prompt of every Jessie workflow for the switches, so a new one anywhere is listed; they also check that the ALLOW lists
match and that every DEV_REDIRECT points at the same person. The older manual method:

Fetch each workflow and grep for: `YEAR_SHIFT`, `plus({ years`, `DEV_REDIRECT`, `TEST_COORD`,
`ALLOW =`, `isHaistDev`, `HAIST Dev`. Only main (year shift), Cancel/Move (redirect + HAIST Dev) and
Open Consent Request (redirect) should match. **Re-verified 2026-09-25 across all 12 live Jessie
workflows** (the nine plus Open Consent Request, Finalize Consent, Consent Sweep): exactly those four,
everything else clean.
