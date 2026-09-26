# Draft — Envoy → KDC Bookings mirror (alternative to the read-side change)

Status: **v2 built 2026-09-26, offline-tested, not yet imported** · Owner: Tel · Drafted 2026-09-23

An alternative (or complement) to the [read-side change](./envoy-jessie-readside-build.md). Instead of
teaching Jessie to read the resource calendars, this **mirrors Envoy bookings onto KDC Bookings**, so
they show on the master calendar **and** Jessie sees them there (she already reads KDC Bookings today).
**Not imported or tested.**

## Build: v2 (built 2026-09-26, not yet imported)

[`workflows/envoy-mirror-v2.json`](../../workflows/envoy-mirror-v2.json) replaces the v1 scaffold. It is
**offline-tested only** (`./scripts/test-mirror`, 11 scenarios), never imported or run against Google.

```
Every 2 min → Room Calendars (Code, 27 items) → Read Room Calendar (HTTP, per room) ┐
                           └──────────────────────────────────────────────────────┴→ Merge Reads (by position)
→ Read KDC Mirrors (HTTP, once) → Plan Changes (Code) → Route Op → Create / Update / Delete Copy (HTTP)
```

What changed from v1, and why:

- **Google calls are HTTP Request nodes** with the existing `Google Calendar account` credential (the
  pattern Find Booking / Book Session use). v1 called Google from inside a Code node, which has no
  credential slot and would almost certainly have failed on the first run.
- **A failed room read no longer deletes that room's copies.** v1 read "that calendar errored" as "every
  booking there was cancelled", deleted the copies, and recreated them next run, leaving a double-book
  window in between. v2 skips deletes for any room whose read errored or came back with a `nextPageToken`.
  If the reads don't pair one-to-one with the rooms, it makes no deletes at all.
- **A failed or partial KDC read writes nothing.** v1 read it as "no copies yet" and duplicated every
  tablet booking. v2 stops (errored read) or throws (partial read) before writing anything.
- **Delete cap:** more than 25 deletes in one run are held rather than applied (`deletesHeld` in the run
  record), a backstop against an unexpected empty response.
- **Duplicate copies of one source are removed**, and times are compared as instants, so a different
  `+08:00` vs `Z` rendering doesn't cause an update every run.
- `maxResults` 2500 (Google's max) per read; the run record lists any room that still came back partial.

**Run record:** the first item out of `Plan Changes` (`op: summary`): `unreadable`, `incomplete`, `desired`,
`existing`, `creates`, `updates`, `deletes`, `deletesHeld`, `skippedDeletes`. `unreadable` is also the
first-run check that the credential can read every room calendar.

### Import and go-live steps

1. Item 43 first (the Studio E id in the five live workflows). The mirror already uses the live Studio E id.
2. `./scripts/test-mirror` → `./scripts/n8n-write create workflows/envoy-mirror-v2.json` (prints the id),
   or use Import from File in the browser. The key must be Howard's (gotcha 15).
3. Open it in n8n and confirm the five HTTP nodes show **Google Calendar account**. The file carries its
   id, but re-select it if the UI flags it.
4. **Execute workflow** once by hand. Check `Plan Changes` → summary: `unreadable` should be `[]`.
   Look at KDC Bookings for the new `<Room> - …` copies.
5. `./scripts/n8n-write activate <id>`: workflows created through the API start inactive (gotcha 0).
6. Run the live test plan below on **real, near-term dates**. The window is now → +90 days, so the 2027
   QA bookings are outside it.
7. Add the new id to `verify-ids` and the workflow table in `CLAUDE.md`, then pull it back into the repo
   and commit.

At every 2 minutes this adds ~720 executions a day; the 04:00 pruner covers it. Setting
`saveDataSuccessExecution: none` would stop successful runs being stored at all, but would also hide them
from `health`; decide after the first week.

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
