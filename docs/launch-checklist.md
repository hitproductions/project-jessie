# Launch checklist — QA/dev switches to flip for go-live

Launch: **25 September 2026**. This is the authoritative list of every QA/dev scaffold that must be
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

Once `DEV_REDIRECT = ''`, the `ALLOW` list beside it is inert (everyone is notified for real), so it
needs no change — leave it or delete it. The **booker-only** rule (engineer redirects while
`DEV_REDIRECT` is set) also dissolves: at launch both booker and engineer get real DMs.

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
3. `./scripts/health` — every node green.

## How this list was verified (repeatable)

Fetch each workflow and grep for: `YEAR_SHIFT`, `plus({ years`, `DEV_REDIRECT`, `TEST_COORD`,
`ALLOW =`, `isHaistDev`, `HAIST Dev`. Only main (year shift) and Cancel/Move (redirect + HAIST Dev)
should match.
