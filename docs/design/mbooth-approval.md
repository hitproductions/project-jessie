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

## Booth set + holders — CONFIRMED 2026-09-22 (Howard)

Only two booths carry a standing recurring hold right now (**M7 dropped**). Holder Slack ids from the
Bookers table:

| Booth | Holder | Slack ID | Standing-hold event title |
|---|---|---|---|
| **M2** | Peemo Morato (Head of Video Post) | `UPPEY3F4G` | `M2 - Peemo` |
| **M6** | Nicole Miller (Head of Marketing) | `U06CTHTUS1Y` | `M6 - Marketing` |

## How "held" is detected — CONFIRMED

The standing holds are real recurring calendar events, and both share two robust signals (verified on
the live calendar 2026-09-22):

- **`recurringEventId` present** — the hold is a daily recurring event (M2 as an all-day `date` event;
  M6 as a 24h `dateTime` event — different shapes, both recurring).
- **`transparency: "transparent"` / `availability: FREE`** — a *soft* hold that shows on the calendar
  but is marked Free, not Busy. A real booking is opaque (Busy) and non-recurring.
- Title pattern **`M<n> - <holder>`** as a corroborating fallback.

So the detection (in Book Session, at the `ROOM_OCCUPIED` point): among the overlapping events on the
booth, a conflict is the **standing hold** iff `transparent && recurring` (or the title matches). Then
`decideMBooth` (tested) returns:
- **`open_mbooth`** — non-holder wants a held booth → open a consent request to the holder.
- **`book_as_holder`** — the requester IS the holder → just book (skip the courtesy hold; the holder
  owns the booth). *(Fixes a current gap: today the transparent hold registers as a plain
  `ROOM_OCCUPIED`, so even the holder can't book their own booth through Jessie — Check Conflicts does
  not filter by transparency.)*
- **`room_taken`** — a *real* (opaque) booking also overlaps → ordinary first-come clash, normal refuse.
- **`none`** — not a shared booth / not a hold → falls through to the normal path.

`#jessie-approvals` is `C0C34UMFXGD` (shared with `PREEMPT`; view/audit feed only). Fully set.

## Still open for the team

Only one design question remains (everything else — booth set, holders, Slack ids, held-detection,
deadline tiers, timeout policy — is confirmed above):

- **Approval rule** — the booth owner approves their own booth (proposed default), vs any-of-N. Wiring
  assumes owner-approves-own-booth unless told otherwise.

## Build status (2026-09-23)

Deterministic core offline-tested (`workflows/drafts/mbooth/logic.js`, 39/39). **Three of the four
wiring stages are LIVE + component-verified:**

1. ✅ **Shared-use detection — LIVE (Book Session v37/v38).** Check Conflicts now enriches each conflict
   with `transparent` + `recurring`; Decide Preempt runs `decideMBooth` before the preempt eligibility.
   At a `ROOM_OCCUPIED` on M2/M6, a standing hold (`transparent && recurring`, title fallback) →
   `open_mbooth` for a non-holder, `room_taken` if a real booking also overlaps, else falls through.
   Verified against the live node: a held-M2 request by a non-holder returns `offer:MBOOTH, approver=Peemo`.
2. ✅ **`MBOOTH` request — LIVE (Open v6).** Open takes a `kind` input (default PREEMPT); Build Request
   writes `Kind`; Build Messages has booth wording ("… your standing booth, OK to let them use it?").
   Book Session's Decide Preempt builds the MBOOTH `open` object (approver=holder, relocation fields
   empty, the booth's Book payload in `Req Payload`). Reuses the DEV_REDIRECT gate (still Howard-only).
3. ✅ **Approve→finalize router path — LIVE (main v149).** Consent Router is Kind-aware: an MBOOTH row +
   holder `yes` → branch `mbooth-book`; a new `MBooth Book?` IF routes it to `Call Finalize MBOOTH`
   (place-only Book). Book Session v38 lets that placement **bypass the permanent hold** — Check
   Conflicts skips a `transparent && recurring` hold when `room_override` is set, so the consented
   booking isn't blocked by the very hold the holder just approved. Normal path verified unbroken.
4. ⏳ **The Sweep — NOT built yet.** Scheduled workflow (~10 min) running `sweepAction` over PENDING
   rows: MBOOTH past-deadline → Finalize (book, per timeout=book); PREEMPT past-deadline → EXPIRED +
   notify. Schedule-triggered → fires even during a Cloudflare edge outage. Shared by both callers
   (also closes the "a preemption hangs forever if the incumbent never replies" gap). Without it, the
   holder-**replies** path works; only the **no-response → book** timeout is missing.

**Live end-to-end test is blocked on a data gap:** the real M2/M6 standing holds are 2026 near-term
recurring events whose recurrence does NOT reach the year-shifted QA dates (2027), so M-booth stays
dormant in QA (M2/M6 just book normally there). To test the flow live, seed a `transparent && recurring`
"M2 - Peemo" event on a 2027 QA date (needs calendar write access — the connector is read-only here),
or test post-launch with `YEAR_SHIFT=0` on a real near-term date where the hold exists.

**Cosmetic follow-up:** Finalize's requester/holder notices are PREEMPT-worded ("… moved their session
to make way") — for an MBOOTH placement nothing moved, so make those notices Kind-aware.
