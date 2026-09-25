# Launch checklist — QA/dev switches to flip for go-live

Launch: **12 October 2026** (amended 2026-09-21; dev freeze 23 Sep). This is the authoritative list of every QA/dev scaffold that must be
turned off (or decided) before Jessie serves real bookings. Verified against the **live** workflows
on 2026-09-21 by grepping each for the markers below — nothing else carries them (Book Session,
Find, Room Availability, Expand Series, Book Series, Prune are clean).

Also in CLAUDE.md → *Before launch*; this doc is the reviewable detail.

## 1. Year shift → 0 (flip both together)

QA runs on year-shifted 2027 dates. The model and the guards must agree, so both change at once.

| Where | Constant | Now | Launch |
|---|---|---|---|
| main → `Gate Context` node | `const YEAR_SHIFT = 1;` | `1` | `0` |
| main → agent system prompt (`Today's date is …`) | `.plus({ years: 1 })` | `+1 yr` | remove |

If only one changes, "next Thursday" and "is this date in the past" break. `./scripts/test-gate`
expects 2027 dates today, so update those expectations too when you flip.

## 2. Notification dev-redirect → real people

While building, every authorized-change notification is rerouted to a dev inbox so real staff aren't
pinged. Flip one constant per sub-workflow and notifications go to the real booker + engineer.

| Where | Constant | Now | Launch |
|---|---|---|---|
| `Cancel Booking` → `Build Recipients` | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` |
| `Move Booking` → `Build Recipients` | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` |
| **`Open Consent Request` → `Build Request`** (consent engine) | `const DEV_REDIRECT = '…';` | `'U08V3CKDGJF'` (Howard) | `''` |

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
holder can move/cancel **any** booking in **any** department. Currently on **Howard, Tel, Genzo**.
Not a code flip — a decision:

- **Keep** (devs retain god-mode after launch): do nothing.
- **Pull:** remove the `HAIST Dev` tag from those Bookers records (Airtable), and optionally remove
  the `isHaistDev` clause in `Check Ownership` (Cancel) and `Resolve Booking` (Move).

Enforced via `isHaistDev` in Cancel/Move. See `docs/design/booking-authority.md`.

## Already handled (no action)

- **`TEST_COORD`** (the hard-coded Howard coordinator) — **removed** 2026-09-21 (cancel-booking-v13,
  move-booking-v12). Authority is now all real Airtable tags.

## After flipping — verify

1. `./scripts/test-nodes --live` and `./scripts/test-gate` (update the 2027 date expectations first).
2. A live DM: confirm a relative date resolves to the **real** year, and that an authorized change
   DMs the **real** booker/engineer (no `[DEV]` prefix).
3. A consent request (an M-booth over a standing hold is the easiest): the **real holder** gets the DM,
   not Howard. Note the consent deadline tiers (same day = 3h, tomorrow = 10:00, 2+ days = 24h) become
   reachable only now; QA's 2027 dates always landed in the 24h tier. Watch the first same-day request.
4. `./scripts/health` — every node green.

## How this list was verified (repeatable)

Fetch each workflow and grep for: `YEAR_SHIFT`, `plus({ years`, `DEV_REDIRECT`, `TEST_COORD`,
`ALLOW =`, `isHaistDev`, `HAIST Dev`. Only main (year shift), Cancel/Move (redirect + HAIST Dev) and
Open Consent Request (redirect) should match. **Re-verified 2026-09-25 across all 12 live Jessie
workflows** (the nine plus Open Consent Request, Finalize Consent, Consent Sweep): exactly those four,
everything else clean.
