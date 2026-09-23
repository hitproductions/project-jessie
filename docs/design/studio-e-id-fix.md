# Draft — Studio E resource-id fix

Status: **draft, not implemented** · Owner: Tel · Drafted 2026-09-23

A standalone fix, separate from the Envoy read-side change — it's a live correctness bug on its own.
**Nothing here is built or imported.**

## The bug

Jessie's workflows map **Studio E → `c_18807te03d2sqh0lmtal9sbb04gao`**, which **does not resolve**
(the calendar returns "not found / deleted"). The real, live Studio E resource is
**`c_1888r4bbc2lhqgndmprism70nft64`** — it shows as "Studio E (5)" in the Admin resource list, carries
real bookings, and is organized by KDC Bookings. Found 2026-09-23.

## Impact

- **Bookings:** when Jessie books Studio E, `Create Event` invites the **dead** resource, so the event
  never reaches the real Studio E resource calendar. Envoy won't see it, and the real room's calendar
  stays wrong.
- **Availability / conflicts / lookups:** the Code nodes match events to Studio E by that dead id, so a
  real Studio E booking is never matched — availability can report Studio E free when it isn't, and
  Find Booking can't attribute a Studio E event to the room.

## The fix

Replace `c_18807te03d2sqh0lmtal9sbb04gao` with `c_1888r4bbc2lhqgndmprism70nft64` everywhere it appears.

**Confirmed live locations (from the `workflows/live/` snapshot):**

| Workflow | id | Where |
|---|---|---|
| Project Jessie v2 (main) | `uVVYVB2M7kxpLleI` | `Book Session` tool node's invite/room map |
| Jessie — Book Session | `EUG3sGXkfsJSYIMz` | `Create Event` attendee map (**the booking invite — most important**) |
| Jessie — Room Availability | `e7tBQB458nstrqei` | `Compute Availability` `ROOMS` map |
| Jessie — Find Booking | `yzirq12O227VTFp8` | `Shape Results` `ROOMS` map (reverse-keyed) |

Also **check Move Booking** on a fresh pull — the hand-versioned `move-booking-v*.json` files carry the
id, so the live Move Booking may too.

## Before building

- **Pull each workflow fresh** (`./scripts/n8n pull <id> <file>`) — this draft is from the
  `workflows/live/` backup (no `.env`/live pull here). Re-check every occurrence on the fresh copy;
  don't trust this list blindly.
- **Confirm the canonical id with IT** — that `c_1888r4bbc2lhqgndmprism70nft64` is the managed Studio E
  resource and `c_18807te03d2sqh0lmtal9sbb04gao` is genuinely retired (not just inaccessible to one
  account).

## Method

1. Fresh pull of the 4 (or 5) workflows.
2. Replace the id string in each (check every occurrence — a pulled file also carries an
   `activeVersion` snapshot; fix the live nodes, per gotcha 8).
3. `./scripts/check-fromai` + `./scripts/test-nodes` on each candidate.
4. Import via `./scripts/n8n-write put` (or the browser UI); toggle Active off/on for Book Session
   since a tool's inputs are involved.
5. Verify with a pull + `./scripts/health`.

## Verification test (live)

- Book **Studio E** through Jessie → confirm the event lands on `c_1888r4bbc2lhqgndmprism70nft64`
  (the real Studio E resource) with the room **accepted**, and shows in Envoy.
- With a real Studio E booking in place, a Studio E availability check reports it **busy**, and Find
  Booking attributes it to Studio E.

## Caveats

- Smaller and lower-risk than the read-side change, and shippable independently — but it still touches
  the booking invite and availability matching, so it needs the same `test-nodes` + `health` pass.
- Timing: can go **before** the Envoy read-side change; it's also a prerequisite for it.
