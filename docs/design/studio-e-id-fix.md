# Draft — Studio E resource-id fix

Status: **fix script built 2026-09-26, dry-run on the 25 Sep backups; not yet applied to n8n** · Owner: Tel · Drafted 2026-09-23

A standalone fix, separate from the Envoy read-side change — it's a live correctness bug on its own.

## Do it (2026-09-26)

`./scripts/fix-studio-e` replaces the id in a pulled file's `nodes` only (never `activeVersion`,
gotcha 8), and `--check` reports what is left. Built without n8n access, so it was dry-run on copies
of the 25 Sep `workflows/live/` backups: 6 replacements in 5 workflows, the id the only change (the
rest of each file byte-identical), `test-nodes` 209 checks + 28 gate scenarios pass before and after,
`check-fromai` clean. With the key in `.env` (Howard's account, gotcha 15):

```
./scripts/n8n pull EUG3sGXkfsJSYIMz workflows/book-session-vNN.json
./scripts/n8n pull e7tBQB458nstrqei workflows/room-availability-vNN.json
./scripts/n8n pull t7lwR2km4tfN8DbM workflows/move-booking-vNN.json
./scripts/n8n pull yzirq12O227VTFp8 workflows/find-booking-vNN.json
./scripts/n8n pull uVVYVB2M7kxpLleI workflows/project-jessie-vNNN.json   # optional, see below
./scripts/fix-studio-e <those files>
./scripts/fix-studio-e --check <those files>        # every line "clean"
./scripts/test-nodes MAIN BOOK CANCEL FIND MOVE     # CANCEL = a fresh cancel-booking pull, unchanged
./scripts/n8n-write put <id> <file>                 # Book Session first; it's the booking invite
./scripts/n8n-write deactivate EUG3sGXkfsJSYIMz && ./scripts/n8n-write activate EUG3sGXkfsJSYIMz
./scripts/health
```

Use the next free version number for each file. Main's hit is `Create Event`, a **disabled** tool node
wired to nothing, so it changes no behaviour. Fix it the next time main is imported for another reason,
rather than importing main (the riskiest workflow) for this alone. `test-nodes` doesn't load Room
Availability; `fix-studio-e --check` is its check here, and the live test below is the real one.

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

**Confirmed live locations (from the `workflows/live/` snapshot, re-checked 2026-09-26):**

| Workflow | id | Where |
|---|---|---|
| Project Jessie v2 (main) | `uVVYVB2M7kxpLleI` | `Create Event`: a disabled, unconnected legacy tool node (no effect) |
| Jessie — Book Session | `EUG3sGXkfsJSYIMz` | `Create Event` attendee map (**the booking invite — most important**) and `Check Conflicts` room map |
| Jessie — Move Booking | `t7lwR2km4tfN8DbM` | `Resolve Booking` room map (a moved Studio E booking also invited the dead resource) |
| Jessie — Room Availability | `e7tBQB458nstrqei` | `Compute Availability` `ROOMS` map |
| Jessie — Find Booking | `yzirq12O227VTFp8` | `Shape Results` `ROOMS` map (reverse-keyed) |



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
