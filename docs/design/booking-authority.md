# Design — Booking authority (editing others' bookings)

Status: **in build (Phase 1)** · Started 2026-09-19 · Owner: Howard

## Problem

Jessie's Rule 1 is never-overridable: *never delete or alter a booking to make room for a
different one.* But real operations need exceptions — e.g. a last-minute **celebrity** session
needs Studio F, which holds an existing **VO recording**; the VO is relocated to Studio 7 and the
celeb takes F. A qualified coordinator must be able to move/cancel a booking that isn't theirs.

**These authorized roles are the explicit exceptions to Rule 1.**

## Decisions (2026-09-19)

- **Phase 1 = within-department only.** A qualified actor may relocate / edit / cancel / delete a
  booking **in their own department**. Cross-department is Phase 2 (needs a consent flow).
- **Qualifying authority (Phase 1):** Bookers `Authority` includes **`Dept Head`** OR
  **`Client Booking`** — acting **within their own `Department`**. (Client Booking is broad and
  temporary; a narrower dedicated tag comes later — see open items.)
- **Management authority is omitted for now** (not yet decided).
- **Notifications:** on any authorized move/cancel/delete, Jessie DMs the **booker** and the
  **assigned engineer** to inform them (Bookers holds everyone's Slack User ID).
- **Rule 1 stays for everyone else.** The exception is: an authorized actor may **relocate**
  (preferred) or cancel/delete an in-department booking, with confirmation; a relocation must land
  in a suitable free room.
- **Testing this weekend:** Howard's Slack id is **hard-coded** as an authorized actor (Howard is
  Audio Post / Standard, no real authority). Temporary — remove once a real tag exists.

## What already exists

- `Get Booker` matches the Slack sender to Bookers by **Slack User ID** and exposes Name,
  Initials, **Department**, **Authority**, Info to the agent every turn.
- Ownership is already enforced in the sub-workflows (the right place): Move Booking →
  `Resolve Booking` (`ref !== requester → NOT_YOURS`); Cancel Booking → `Check Ownership`. The
  `ref:` on the event description is the owner's Slack id.

## Two gaps this design closes

1. **Department isn't on the event.** Needed to scope "within their department." → **Stamp
   `Dept: X`** onto the event description at Book Session time (the agent computes the department
   for every studio booking). New bookings get it; older ones fall back to owner-only.
2. **The named coordinators (Letty/Jo Anne/Lea/Japs) weren't distinctly tagged** — all have
   `Client Booking`, so the Phase-1 rule covers them. A dedicated tag replaces this later.

## Enforcement (all in the sub-workflow, not the prompt)

Pass the requester's **Authority** + **Department** from `Get Booker` into Move & Cancel (same
pattern as `bookingType` / `series`). The check becomes:

```
may act =  requester is the owner (ref === requester)
        OR requester's Slack id is the hard-coded test id           (temporary)
        OR ( (Authority has 'Dept Head' OR 'Client Booking')
             AND booking.Dept === requester.Department )
```

The prompt gets a tightly-scoped exception describing who may, that it relocates/cancels within
department, and that Jessie informs the booker + engineer; Rule 1 otherwise stands.

## Build order

1. **Dept stamp** on events (Book Session) — `department` input → `Dept: X` description segment;
   Book Series passes it through.
2. **Authority in Move & Cancel** — pass requester Authority + Department; ownership check above.
3. **Prompt** — the scoped Rule-1 exception + the relocate-then-book flow for making way.
4. **Notifications** — Jessie DMs the booker + assigned engineer on an authorized change.
5. **Phase 2** — cross-department **consent flow**: Jessie asks the other department's coordinator
   (yes/no) before proceeding, and informs the booker.

## Parked / later

- **Cross-department consent (Phase 2)** — also likely reusable for **M-Booth** standing-hold
  concerns (Peemo, Nicole, etc. wanting their booth on a given day). Park together.
- **Dedicated authority tag** (e.g. `HAIST Dev` for testers, and a precise coordinator tag) —
  Tel to add in Airtable on Monday; then drop the Howard hard-code and narrow the Client-Booking rule.
- **Harden the Dept stamp** — currently the agent supplies `department`; consider deriving it
  deterministically from session type so a security-relevant field isn't model-supplied.
