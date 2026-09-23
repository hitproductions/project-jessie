# Backfill checklist — existing GCal events (made outside Jessie)

Sprint task (row 79, Howard + Tel): so Jessie can **cancel / move / preempt / notify on** bookings it did
not create, those events need the same metadata Jessie stamps on its own. Scope: **future events only**
(real dates from now onward — past ones can't be acted on anyway). Put everything in the event
**Description**. Slack IDs come from the **Bookers table → `Slack User ID`** column.

## What to add, by priority

### 🔴 CRITICAL — `ref: <booker's Slack ID>`
The functional owner id. Without it Jessie can't act on the booking at all:
- **Cancel** refuses (`NO_REFERENCE` / `NOT_YOURS`)
- **Move** refuses (same ownership check)
- **Change notifications** can't reach the booker
- **Preemption** can't tell whom to ask for consent

### 🟡 RECOMMENDED
- **`Dept: <department>`** — powers the department-scope permission (a dept-head / coordinator can act on
  bookings *in their department*). Without it, only the booker themselves or a HAIST Dev can act on it.
- **`SType: <session type>`** — makes the booking **preemptible** (its priority rank is read from here).
  Without it → `INCUMBENT_RANK_UNKNOWN` → it's never bumped (safe, but the priority feature won't apply to
  that event). Add it if you want existing lower-priority bookings to be bumpable at launch. (This is also
  what marks an M-booth recurring hold as a hold — the ones already tagged.)

### 🟢 NICE-TO-HAVE (parity / display)
`Booked by: <Name>` (the name shown in summaries; `ref:` is the real key), `Engineer: <Name> (<Role>)`,
`Type: External|Personal`, `Tech requirements: …`.

## Exact format

Match how Jessie writes it — a pipe-separated line, then `SType` on its own line:

```
Engineer: <Name> (<Role>) | Booked by: <Name> | ref: <Uxxxx> | Type: External | Dept: <Dept> | Tech requirements: None
SType: <Session Type>
```

**Minimal viable** (if you only do the essentials):

```
Booked by: <Name> | ref: <Uxxxx> | Dept: <Dept>
SType: <Session Type>
```

## What you DON'T need to backfill

- **Rooms** — Jessie detects the room from the event's room-resource / location, which existing events
  already have.
- **Titles** — they don't have to match Jessie's `PROJECT / Client / Initials` format; they just need to be
  recognizable so someone can say "cancel the *elephant* session" (Find / Cancel / Move resolve by the
  title people use).

## Notes

- `ref:` and `SType:` are exactly what preemption + the M-booth engine read off the incumbent/hold (see
  `docs/design/consent-engine.md`). Backfilling them makes existing bookings first-class for those features.
- Field names and the pipe/newline layout are parsed by regex, so keep the labels exactly: `ref:`,
  `Dept:`, `SType:`, `Booked by:` (case-insensitive, but keep the colons and the `\n` before `SType`).
- The recurring **M-booth holds** (M1/M2/M4/M6, + ANA/japs) are already tagged with `ref:` — 2026-09-23.
