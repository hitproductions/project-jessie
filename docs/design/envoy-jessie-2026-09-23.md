# Envoy ↔ Jessie — status & decisions (2026-09-23)

Dated snapshot of the Envoy/Jessie booking-source work. The living design doc is
[`envoy-calendar.md`](./envoy-calendar.md) — this file freezes where things stand today.

## The goal (Howard's priority)

Whatever is booked through **Envoy** (door tablets) must be **recognized by Jessie** (so she never
double-books over it) and **reflected in our calendar**, and bookers must be able to **see** those
bookings through Jessie.

## Validated today

- **Jessie → Envoy works.** A Jessie test booking ("TEST JESSIE ENVOY", Studio 7, 23 Sep 2027
  10:00–18:00) was confirmed on Studio 7's resource calendar with the room accepted — the exact
  surface Envoy reads. So Jessie's bookings already show in Envoy.
- **Envoy is connected** to the room resource calendars.
- **All studios/booths are managed Google Workspace resources**, and **IT holds super-admin**.
- **The reverse gap is real and already live:** a scan (22 Sep–12 Oct) found bookings that live only on
  resource calendars (e.g. Via on Studio 5, Anne on Studio 6) — structurally identical to an Envoy
  booking. Jessie can't see these today because her checks read only the KDC Bookings group calendar.

## Decisions (2026-09-23)

- **Tablets are a real booking source**, not just a display.
- **No prompt change needed** — availability/conflict is enforced in sub-workflows, and the prompt
  already routes availability to `Room Availability` and refuses bookings with no booker reference.
- **Scope = 3 workflows:**
  - **Prevent double-booking** — `Check Conflicts` (in `Book Session`) + `Room Availability` read the
    resource calendars (freeBusy), so Jessie won't book over a tablet booking.
  - **Booker visibility** — `Find Booking` reads the resource calendars, so lookups include tablet
    bookings.
- **Tablet bookings are read-only in Jessie:** visible and blocking, but no Jessie `ref:` marker, so
  Cancel/Move still refuse them (change them in Envoy).

## Bug found (fix required)

- **Studio E resource id is wrong.** `Book Session` maps Studio E → `c_18807te03d2sqh0lmtal9sbb04gao`,
  which does not resolve (deleted). The live Studio E resource is `c_1888r4bbc2lhqgndmprism70nft64`.
  Jessie is inviting a dead Studio E resource — her Studio E bookings don't reach the real calendar and
  availability there is unreliable. Prerequisite for the read-side change; also a live bug on its own.

## Open questions

- **"Reflected in our calendar" — which calendar?** The read-side change gives Jessie recognition +
  booker visibility. Whether Envoy bookings should *also* appear on the **KDC Bookings master calendar**
  (a new mirror/sync workflow) vs. overlaying the resource calendars in the master view is still open.
- **n8n Google credential access** to the resource calendars' free/busy — to verify at build/QA time.

## Next steps

- Draft the read-side change as a **post-launch** candidate (built from a fresh pull, tested with
  `test-nodes`, not imported) — it touches the load-bearing availability path, dev freeze is 2026-09-23,
  launch 2026-10-12.
- Decide whether to ship the **Studio E id fix** sooner as its own small change.
