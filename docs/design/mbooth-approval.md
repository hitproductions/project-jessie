# Design — M-Booth shared-use approval (a caller of the consent engine)

> **Aligned 2026-09-21 with [consent-engine.md](consent-engine.md).** M-Booth shared use is now the
> `MBOOTH` caller of the single shared consent engine — it does **not** have its own table, channel,
> router, or sweep. This doc keeps only what is M-Booth–specific (the standing-hold problem, how
> "held" is detected, the booth/holder set, deadline rules). For the engine itself — the durable
> `Consent Requests` row, DM correspondence, the pending-row router, the sweep, first-resolver-wins,
> the outage analysis — read consent-engine.md; do not re-specify it here.

Status: **scaffolded, aligned to the engine** · updated 2026-09-21 · Owner: Howard
Draft logic + tests: `workflows/drafts/mbooth/` (16/16 offline, still valid — generalize the router
from a channel-id check to a pending-row check when wiring it into the shared engine).

## What's M-Booth–specific

Some M-Booths carry a **standing hold** for an owner/department (historically M2→Peemo, M6→Nicole,
M7→BD). Someone else wanting that booth at a held time needs the holder's OK. The holder's reply can
take minutes to hours while a Jessie turn is ~9s, so it can't complete in one turn — which is exactly
why it runs on the async consent engine (request → PENDING row → resolve → finalize/expire, all
outage-safe; see consent-engine.md).

Two things make it *simpler* than the `PREEMPT` caller:

- **No relocation.** Finalize is just a normal **Book Session** into the booth once the holder
  approves — there is no incumbent booking to move. (`PREEMPT` has to free a room first; `MBOOTH`
  does not.) So M-Booth is the lightest thing the engine does.
- **The approver is the booth's holder**, resolved from the booth→holder map below — not from an
  event `ref:`.

## On the shared engine — how M-Booth maps onto it

- **Store:** the shared `Consent Requests` **Google Sheet** (a tab in the Jessie Log spreadsheet, not
  Airtable) with `Kind = MBOOTH`. Booth requests use `Approver`
  (= the booth holder), `Room`/`Booth`, `Req Start`/`Req End`, `Title`/`Department`/`Engineer`,
  `Deadline`. The incumbent/relocation fields stay empty (there's no booking to move).
- **Correspondence:** the holder is asked and replies **in their Jessie DM**; the requester can also
  attest ("cleared with Peemo"), first resolver wins. `#jessie-approvals` is only the back-end log.
- **Router / consent gate / sweep:** the shared ones. The `workflows/drafts/mbooth/` functions
  (`route`, `resolveConsent`, `computeDeadline`) are the tested basis — `route` changes from "is this
  the approvals channel?" to "does this sender have a PENDING row awaiting them?" when generalized.
- **`computeDeadline(now, start, cfg)` — tiers CONFIRMED by Howard 2026-09-22** (Asia/Manila, not
  "PST"; that was an error in the old draft). How long the holder has to respond, by how far out the
  booking is (Manila calendar days):
  - **booking 2+ days away → now + 24h**
  - **booking is tomorrow → 10:00 AM Manila on the booking day**
  - **booking is same day → now + 3h**
  - Always floored at now and **capped at the session start** (a deadline can't fall after the session
    begins). Built + offline-tested in `workflows/drafts/mbooth/logic.js` (29/29). The sweep that acts
    on `Deadline` is shared with `PREEMPT`.
- **Timeout policy — CONFIRMED by Howard 2026-09-22:** an `MBOOTH` request with **no holder response
  by the deadline BOOKS ANYWAY** (silence = the booth defaults to available; the standing hold is a
  courtesy, not a lock). This is the opposite of `PREEMPT`, where silence must only **EXPIRE** the
  request — you can never move someone's booking without their yes. The split lives in the pure
  `sweepAction(row, now)` (also 29/29): `MBOOTH` past-deadline → `book`, `PREEMPT`/unknown → `expire`.
  (This matches the intent of the superseded Wait-node draft's "no response → book anyway", but via the
  outage-safe scheduled sweep instead of a Wait node that a Cloudflare outage could drop.)

## Build order (folds into the consent-engine build)

M-Booth adds no new infrastructure — it rides Steps 1/3/4 of the engine. Its own pieces:

1. **Shared-use detection** — is the requested booth in the shared-use set, and does its hold cover
   the slot? (See "how held is detected" below. Reuses Room Availability.)
2. **`MBOOTH` request** — write the PENDING row (`Kind = MBOOTH`), DM the holder, log to
   `#jessie-approvals`. No calendar event yet.
3. **`MBOOTH` finalize** — on approval, re-check availability and **Book Session** into the booth,
   flip the row, notify the holder + requester (reuse the Phase-1 sender). No relocation.
4. **Prompt section** + offline tests + canary. Same pre-launch window as the engine (dev freeze
   23 Sep, polish to 5 Oct, launch 12 Oct).

## Inputs needed from the team

1. **Shared-use booth set** and each booth's **holder/approver** (M2→Peemo, M6→Nicole, M7→BD —
   confirm), and whether **M2/M6 are active**.
2. The approver **Slack IDs**.
3. `#jessie-approvals` **DONE** — created 2026-09-21, id `C0C34UMFXGD`, Jessie invited (shared with
   `PREEMPT`; view/audit feed only). Fully set.
4. How **"held"** is detected — a standing calendar event on the booth (+ its title keywords) vs a
   static map.
5. ~~The **window / timeout rules** and the **no-response policy**.~~ **DONE — confirmed by Howard
   2026-09-22** (see the deadline tiers + timeout policy above; built + tested in the draft).
6. **Approval rule** — booth owner approves their own booth (proposed) vs any-of-N.

## Build status (2026-09-22)

Deterministic core BUILT + offline-tested (`workflows/drafts/mbooth/logic.js`, 29/29): the confirmed
deadline tiers, `sweepAction` (MBOOTH-book / PREEMPT-expire on timeout), the shared-booth→holder map
(placeholder ids), hold-overlap detection, and the consent gate. Still to WIRE (a coordinated import
like the PREEMPT deploy, and holding until the working PREEMPT flow's testing settles):
1. **Shared-use detection** in Book Session — booth in {M2,M6,M7} + `holdCoversSlot` → open an `MBOOTH`
   request instead of booking. Needs Tel's confirmed booth set + holder Slack ids + how "held" is
   detected (standing calendar event + title keyword, vs the static map).
2. **`MBOOTH` request** — an Open-Consent-Request variant: `Kind=MBOOTH`, `Approver`=booth holder,
   relocation fields empty, the booth's own Book payload in `Req Payload`. (Reuses the DEV_REDIRECT
   test gate.)
3. **Approve→finalize router path** — the one genuinely new wiring vs PREEMPT: a holder `yes` on an
   `MBOOTH` row calls Finalize (place-only Book) **directly** — there's no move-hook because nothing
   relocates.
4. **The Sweep** — a scheduled workflow (~10 min) running `sweepAction` over PENDING rows: MBOOTH
   past-deadline → Finalize (book); PREEMPT past-deadline → mark EXPIRED + notify. Schedule-triggered,
   so it fires even during a Cloudflare edge outage. Shared by both callers (also closes the "a
   preemption hangs forever if the incumbent never replies" gap).
