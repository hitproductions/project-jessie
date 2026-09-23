# Draft — Envoy → KDC Bookings mirror (alternative to the read-side change)

Status: **draft, not implemented** · Owner: Tel · Drafted 2026-09-23

An alternative (or complement) to the [read-side change](./envoy-jessie-readside-build.md). Instead of
teaching Jessie to read the resource calendars, this **mirrors Envoy bookings onto KDC Bookings**, so
they show on the master calendar **and** Jessie sees them there (she already reads KDC Bookings today).
**Not imported or tested.**

## Scaffold workflow (untested)

A starting-point workflow is at [`workflows/envoy-mirror-v1.json`](../../workflows/envoy-mirror-v1.json)
— a Schedule Trigger (every 2 min) → one Code node ("Mirror Envoy to KDC") carrying the full
create / update / delete / reconcile logic, with Studio E already on the **live** id. Import it and adapt.

**Before it can run, verify/adjust:**

- **Google auth from a Code node.** The node calls `this.helpers.httpRequestWithAuthentication` with the
  `googleCalendarOAuth2Api` credential. If that isn't usable from a Code node in the installed n8n, the
  node throws a clear error on the first run — split the Google calls into HTTP Request nodes (same
  logic, the pattern the other workflows already use). Attach the Google credential either way.
- **Activate it** — a workflow imported/created via the API can default to inactive (gotcha 0).
- **Untested** — built with no live pull/test. Run it against a **test** setup first, watch the run
  summary (`created / updated / deleted / failed`), and confirm no duplicates and correct reconcile
  (cancel a tablet booking → its KDC copy is removed on the next run) before trusting it.

## Why this covers both goals at once

- **Master view:** the mirrored copy lands on KDC Bookings, so people scanning that calendar see Envoy
  bookings.
- **Jessie recognition:** Jessie's `Check Conflicts` / `Room Availability` / `Find Booking` already
  read KDC Bookings — so a mirrored copy is where she already looks. **No change to those 3 workflows
  is required for basic recognition.**

## The one tradeoff (decide with eyes open)

- **Sync lag.** A mirror runs on a poll (or a calendar-change trigger), so there's a window (seconds to
  a few minutes) between a tablet booking and its copy appearing on KDC Bookings. In that window Jessie
  could still double-book over it. The read-side change has **no** such gap because it reads the
  resource calendars live.
- → If back-to-back / busy-room double-booking in that window is unacceptable, keep the read-side
  change too (belt and suspenders). Otherwise the mirror alone is the simpler path.

## What it does

A scheduled workflow (poll — like the consent sweep; outage-tolerant) that, each run:

1. Lists events on each **room resource calendar** for a forward window (e.g. now → +N weeks).
2. Keeps only **Envoy-origin** events — identify by their signature: organizer = the room resource
   itself, description contains `Created by Envoy`, and/or event id starts with `rooms`. (Scope choice
   below.)
3. **Upserts** a copy onto **KDC Bookings**, deduped by the source id:
   - store the source `<resourceCalId>:<eventId>` in the mirror copy (e.g. in `extendedProperties` or a
     `source:` line in the description) so re-runs don't duplicate.
   - the copy must be **matchable to its room** by Jessie's existing matchers: put the room in the
     **title first segment** (`Studio 7 - …`) or **location** (`Studio 7`). Do **NOT** re-invite the
     room resource on the copy (that would double-hold the resource / conflict).
   - **no** Jessie `Booked by: | ref:` marker — so Cancel/Move correctly refuse it and Find Booking
     labels it *"made outside Jessie."*
4. **Reconciles**: if a mirror copy's source event no longer exists (Envoy booking cancelled/released)
   or changed time, **delete/update** the copy. This makes each run idempotent and self-healing.

## Scope choice

- **Narrow (recommended start): Envoy-origin only** — clear signature, low risk.
- **Broad: any resource-only event not already on KDC Bookings** — also captures the personal-calendar
  bookings the scan found (Via on Studio 5, Anne on Studio 6). Closes more of the gap, but riskier
  (harder to identify cleanly, more edge cases). Can broaden later.

## Dependencies

- **Studio E id** — the mirror reads resource calendars, so use the **live** Studio E id
  (`c_1888r4bbc2lhqgndmprism70nft64`), not the dead one. Note the Studio E fix is still needed
  separately so Jessie's own Studio E bookings reach the real resource calendar.
- **n8n Google credential** must read each resource calendar and write to KDC Bookings (it already
  writes KDC Bookings and invites resources, so likely fine — confirm).
- **Poll interval** — tighter shrinks the double-book window but adds executions; ~2–5 min is a
  reasonable start.

## Test plan (live)

1. Book a room on the Envoy tablet.
2. Within one poll cycle, a copy appears on **KDC Bookings** with the room in the title/location.
3. Ask Jessie availability for that room/window → **BUSY** (no read-side change needed).
4. Try to book the same slot via Jessie → refused at conflict.
5. Ask Jessie to cancel it → refused (no owner marker) → "change it in Envoy."
6. Cancel/release on the tablet → next poll removes the KDC copy.
7. Regression: Jessie's own bookings are **not** duplicated (they're organized by KDC Bookings, not the
   resource, so they're excluded by the Envoy-origin filter).

## Mirror vs. read-side change — pick per goal

| | Mirror (this doc) | Read-side change |
|---|---|---|
| Envoy bookings on **KDC Bookings** master view | ✅ | ❌ (needs overlay/mirror) |
| **Jessie** recognizes Envoy bookings | ✅ (via existing KDC read) | ✅ (live) |
| Double-book guarantee | small sync-lag window | airtight |
| Build | 1 new workflow | 3 workflows changed |
| Cancel/move of Envoy bookings via Jessie | refused (correct) | refused (correct) |

Recommendation: for "keep KDC Bookings as the master view **and** have Jessie see Envoy bookings," the
**mirror is the most direct fit.** Add the read-side change on top only if the sync-lag double-book risk
matters. Timing: **post-launch** (dev freeze 2026-09-23, launch 2026-10-12). Drafted from the repo with
no live pull — build from a fresh pull.
