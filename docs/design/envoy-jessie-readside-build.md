# Draft — Envoy↔Jessie read-side change (3 workflows)

Status: **draft, not implemented (post-launch)** · Owner: Tel · Drafted 2026-09-23

Implementation draft for making tablet (Envoy) bookings visible to Jessie. Companion to
[`envoy-calendar.md`](./envoy-calendar.md) and the [2026-09-23 snapshot](./envoy-jessie-2026-09-23.md).
**Nothing here is built or imported.**

## How this draft was made (read before building)

- **No live pull was possible here** — this environment has no `.env`/n8n API key, so the draft is
  based on the `workflows/live/` backup snapshots (last hand-refreshed ~2026-09-17). **Before building,
  pull each workflow fresh** (`./scripts/n8n pull <id> <file>`) and re-base these changes on it — the
  live build may have moved (a consent engine landed recently).
- **Offline tests are partial.** `test-nodes` exercises the Code nodes, not the HTTP/calendar calls, so
  the new fetch path must be verified live in n8n, not just by `test-nodes`.

## The one change

Every availability/lookup read today hits **only** the group calendar
`c_re5mcrg9om0macp9doqhlsi83g@group.calendar.google.com`. A tablet booking lands on the room's
**resource calendar**, not there — so Jessie can't see it. The change: **source the reads from the
room resource calendars** (where both Jessie's and Envoy's bookings live). Only the *fetch* changes;
the room-matching/interpretation logic in each Code node stays.

## Per-workflow

### 1. Room Availability — `e7tBQB458nstrqei` (hot path)

- **Now:** `Get Events In Window` (HTTP GET) → group calendar events → `Compute Availability` derives
  `busy{room}` by matching each event's resource-attendee email / location / title to the room.
- **Change:** determine busy from the **resource calendars**. Recommended: a **freeBusy** POST
  (`POST /calendar/v3/freeBusy`, body `{ timeMin, timeMax, items: [{id: <each resource cal>}] }`) — one
  call, ≤50 calendars (we have 27), returns busy intervals **per calendar id = per room**. That is more
  reliable than title-matching and captures tablet bookings.
  - `Compute Availability` is rewritten to build `busy{}` from the freeBusy response (calendar id →
    room via the existing `ROOMS` map) instead of scanning event items. Everything downstream
    (`asked`, priority/last-resort, booths, `human`) is unchanged.
  - **Tradeoff:** freeBusy has no titles, so `taken_by "<title>"` is lost. Keep it for Jessie's own
    bookings by *also* GETting the group calendar (fast, one extra call) purely to enrich titles; a
    resource-only (tablet) booking is reported busy with a generic "booked outside Jessie."

### 2. Check Conflicts — inside Book Session `EUG3sGXkfsJSYIMz` (hot path)

- **Now:** Book Session GETs the group calendar for the requested window and `Check Conflicts` refuses
  if a requested room overlaps. *(Confirm the exact node against a fresh pull — not fully read here.)*
- **Change:** same freeBusy approach, scoped to the **requested room(s)'** resource calendars for the
  window. If any returns a busy interval overlapping the request → `ROOM_OCCUPIED`. This is the guard
  that actually stops the double-booking, so it must be exact.

### 3. Find Booking — `yzirq12O227VTFp8` (lookup, not hot path)

- **Now:** `List Day Events` (HTTP GET) → group calendar events for the day → `Shape Results` lists
  them (already labels a booking with no `Booked by:` as *"not recorded — made outside Jessie"*, so
  tablet bookings are handled gracefully **once they're in the list**).
- **Change:** freeBusy won't work here (needs titles/times). Read **events across the resource
  calendars** for the day. Two options:
  - a **fan-out**: one item per resource calendar → per-calendar GET → merge (27 calls per lookup — OK
    since lookups are rare), or
  - a **Code-node fetch** that loops the calendars via the Google credential (fewer nodes; depends on
    the installed n8n supporting an authenticated request from a Code node — verify).
  - `Shape Results` must then **dedup by `ev.id`** (Jessie's own booking appears on the group and each
    invited resource; a multi-room event appears on several resource calendars). It does not dedup
    today — add it.

## Studio E id fix (prerequisite, appears in every ROOMS map)

Replace the **dead** `c_18807te03d2sqh0lmtal9sbb04gao` with the live
`c_1888r4bbc2lhqgndmprism70nft64` everywhere it appears:

- `Room Availability` → `Compute Availability` `ROOMS` map
- `Find Booking` → `Shape Results` `ROOMS` map (reverse-keyed)
- `Book Session` → `Create Event` attendee map (the actual booking invite — most important)
- likely `Move Booking` and the main workflow — grep and fix all
- do this from a fresh pull, then re-check every occurrence.

## Dependencies to confirm at build time

- **n8n Google credential access.** The read must run under the n8n `googleCalendarOAuth2Api`
  credential (id `6D1r3kaq6KaFdL0a`) — confirm it can read each resource calendar's free/busy and
  events. It already writes events inviting them, so it likely can; a credential without access returns
  empty and would make availability read "free" wrongly.
- **freeBusy behavior** for resource calendars (busy blocks returned as expected).
- **n8n version** support for an authenticated request inside a Code node (only if the Find Booking
  Code-fetch option is chosen).

## Test plan (after build, live)

1. `./scripts/check-fromai` + `./scripts/test-nodes` on the candidate (Code-node coverage).
2. Import to a **test** copy; book a room on the Envoy tablet; then:
   - ask Jessie availability for that room/window → **BUSY** (Room Availability);
   - try to book the same room/window → **ROOM_OCCUPIED** (Check Conflicts);
   - ask "what's booked on <date>?" → the tablet booking appears, `booked_by` = "made outside Jessie"
     (Find Booking).
3. Regression: a normal Jessie booking still books; no room shows double (dedup works).
4. `./scripts/health` after import — nodes green and fast.
5. **Year-shift caveat:** during QA Jessie is on 2027 and the tablet books 2026 — test on a matching
   date or after the launch year-shift flip.

## Caveats / not done

- **Latency:** freeBusy keeps the hot path to ~1–2 calls; Find Booking's per-calendar reads are the
  slower part (lookups only). Don't fan-out Room Availability/Check Conflicts to 27 GETs — freeBusy
  instead.
- **Scope:** this is the read side only. Whether tablet bookings also mirror onto the KDC Bookings
  master calendar is a separate, open decision (see `envoy-calendar.md`).
- Timing: **post-launch** (dev freeze 2026-09-23, launch 2026-10-12). The Studio E id fix is a live bug
  and could ship sooner on its own.
