# Design — Consent engine (outage-resilient, async, in- or out-of-Jessie)

Status: **pinned down for build · design agreed 2026-09-21 · Owner: Howard**
Supersedes the open 2a/2b fork in [booking-authority-phase2.md](booking-authority-phase2.md) and
generalizes the async skeleton in [mbooth-approval.md](mbooth-approval.md) into one shared engine.
Builds on [booking-authority.md](booking-authority.md) (Phase 1, live). Some inputs still pending
Howard's discussion with Tel (see *Inputs still needed*) — the **shape** is fixed; a few values are not.

## What this is for

One mechanism, two callers that are the same shape — *acting on something that isn't yours, which
needs someone else's consent*:

1. **Cross-department priority preemption.** A higher-priority booking needs a room an existing
   lower-priority booking holds (the canonical case: a last-minute **Celebrity Recording** needs
   **Studio F**, held by a **VO Recording**). The incumbent is relocated **by agreement**, then the
   new booking takes the room.
2. **Recurring / standing M-Booth shared use.** Someone wants a booth (M2/M6/M7) at a time it is
   held for its owner; the holder must OK it.

Both resolve through the same durable record and the same finalize path.

## The one principle that makes it outage-proof

> **All consent state lives in one Airtable table. Nothing is ever held in a running execution
> waiting for a reply. An outage can therefore only *delay* a consent — never lose or corrupt one.**

No `Wait` node, ever: a paused n8n execution is lost on a restart, and this box has had outages.
Instead the work is a set of **short, independent executions** whose only shared state is a **row**.

### Our actual outage, mapped to each step

The known failure is a **Cloudflare 403 at the edge**: inbound webhooks never reach n8n, while n8n
keeps running internally and its *outbound* network (Slack API, Airtable, Calendar) still works.
Scheduled triggers still fire (they are not inbound). Against that reality:

| Step | Needs | During an edge outage |
|---|---|---|
| ① **Request** — write the PENDING row | outbound → Airtable | Row write succeeds once the turn runs; **survives** |
| ② **Reply** — incumbent/holder answers in Slack | **inbound** event → n8n | **The only fragile step.** A dropped reply is recovered by the out-of-band path (below) or Slack's own event retries |
| ③ **Sweep** — expire / nudge stale rows | internal schedule | Schedule-triggered, not inbound → **runs anyway** |
| **Finalize** — book/move + notify | outbound | **Works**; re-checks availability and compare-and-sets Status so a duplicate reply cannot double-book |

So there is exactly **one** outage-fragile point — receiving a live reply — and the design gives it
two independent fallbacks. That is the whole answer to "can we build it so an outage doesn't break
it": **yes — an outage delays a consent, it never breaks one.**

## How a request resolves — two Slack paths, first one wins, Airtable as backup

Decided 2026-09-21 (Howard). Consent resolves through **two primary Slack paths**, and **whichever
lands first pushes the change through** — a race to resolve, with an idempotent finalize so the
loser is a harmless no-op:

1. **The requester attests** — the new (higher-priority) requester tells Jessie *"cleared with
   `<name>`"* / *"`<name>` already said yes."* Jessie records **who attested** and finalizes. This is
   the outage-proof fast path (a normal booking turn, no waiting), and the manual recovery when a
   live reply was dropped.
2. **The incumbent consents** — the incumbent/holder replies `yes` to Jessie's request in the
   approvals channel. The async path; self-heals on Slack retry.

Both write to the **same PENDING row**. `resolveConsent` is deterministic (explicit word, never
model-judged). The finalize is a **compare-and-set**: it acts only if the row is still `PENDING`,
flips it to a terminal state, then books — so the first resolver wins and a second arriving reply or
attestation finds nothing to do. **An explicit `REJECTED` is terminal and sticky:** once the
incumbent says no, a later requester attestation cannot flip it (a real "no" is never steamrolled).

**Airtable-direct edit — backup only.** A coordinator *can* flip the row's `Status` in the Airtable
UI, and the sweep will finalize it — but this is a **fallback used only when both Slack paths above
fail** (e.g. a prolonged outage drops the reply *and* the requester can't reach Jessie either).
Coordinators shouldn't need to open Airtable in normal use; it's the break-glass path that keeps a
consent recoverable when Slack is unreachable, because the decision is durable in Airtable and
finalize runs on the next scheduled sweep (which fires even while the edge is down).

One record → resolver races (requester attest / incumbent reply) → Airtable break-glass behind them
→ one idempotent finalize. No path can double-book (finalize re-checks availability at that instant).

## The durable record — Airtable `Consent Requests`

One row per request. Serves both callers via a `Kind` field.

| Field | Purpose |
|---|---|
| `Status` | `PENDING` / `APPROVED` / `REJECTED` / `EXPIRED` / `DONE` / `FAILED` (single select) |
| `Kind` | `PREEMPT` (cross-dept room) / `MBOOTH` (shared booth) |
| `Requester` · `Requester Name` | Slack id + name of who asked |
| `Approver` · `Approver Name` | Slack id + name of who must consent (incumbent booker, or booth holder) |
| `Room` / `Booth` | the contested room or booth |
| `Req Start` · `Req End` | the requesting booking's slot (ISO, +08:00) |
| `Incumbent Event Id` · `Incumbent Title` | the booking being displaced (PREEMPT only) |
| `Incumbent New Start` · `Incumbent New End` | the agreed relocation slot for the incumbent (PREEMPT; filled when agreed) |
| `Req Priority` · `Inc Priority` | the two session-type ranks at request time (audit; why preemption was allowed) |
| `Deadline` | computed at request time (earlier of now+window and start−lead) |
| `Channel` · `Thread TS` | where the request was posted, to correlate a reply |
| `Resolved Via` | `reply` / `attestation` / `airtable` (audit) |
| `Attested By` | who attested, when the fast path was used |
| `Decided By` · `Decided At` | audit |

## The state machine

```
              requester attests  ─┐   (first resolver wins)
              incumbent replies yes ┼─▶ APPROVED ──▶ finalize ──▶ DONE
              Airtable APPROVED (backup) ─┘                        │
                                                                   └─ availability lost / error ▶ FAILED
  request ──▶ PENDING
              incumbent replies no / Airtable REJECTED ──▶ REJECTED  (terminal, sticky — attestation cannot flip it)
              deadline passed (sweep) ─────────────────▶ EXPIRED
```

- **Finalize is idempotent (compare-and-set).** It re-reads the row, acts only if `Status` is still
  `PENDING`, flips it to a terminal state, re-checks availability at that instant, then books —
  otherwise it does nothing. So the **first** resolver (requester attestation or incumbent reply)
  wins the race, and a second arriving signal is a harmless no-op.
- **`REJECTED` is sticky.** An explicit incumbent "no" (or an Airtable `REJECTED`) is terminal; a
  later requester attestation cannot override it.
- **Anything unclear stays PENDING** (same spirit as the confirmation gate); the sweep or a clearer
  reply resolves it. Never model-judged.

## The preemption flow (PREEMPT), end to end

1. Requester asks for a room that is occupied. `Check New Window` today returns `ROOM_OCCUPIED`.
   **New branch:** if the requester's **session-type rank outranks the incumbent's** (data — see
   below) *and* the requester is authorized, Jessie does **not** hard-refuse. Instead she opens a
   consent request.
2. Jessie DMs / posts to the approver (the incumbent's booker, resolved from the event `ref:`):
   *"`<Requester>` needs `<Room>` on `<slot>` for a higher-priority `<session type>`. You hold it
   for `<incumbent title>`. Are you OK to move? If yes, what time works for your session?"* Writes
   the PENDING row. **No calendar change yet** (no tentative hold — that would falsely occupy the
   slot and fight Rule 1).
3. Approver consents — by reply, by attestation, or by Airtable edit — and the relocation slot is
   agreed **through that DM conversation** (Jessie does not pick it unilaterally; Howard's rule).
4. Finalize, **all-or-nothing**: re-check the incumbent's new slot is free → **move the incumbent
   there** → re-check the contested room is now free → **place the requester**. If any step fails,
   nothing changes and the row goes `FAILED` (the incumbent is never left homeless).
5. Notify: the incumbent (moved), the requester (**confirmed consent given + booked** — Howard's
   two-way notification), and the affected dept's coordinator. Reuses the Phase-1 sender.

**Priority is data, not judgment.** `Req Priority`/`Inc Priority` come from a **session-type
ranking** (decided 2026-09-21) — e.g. Celebrity Recording > VO Recording. Read from Airtable and
injected/compared deterministically in the sub-workflow, exactly like the room ranking. Tel defines
the order. No booking may preempt an equal-or-higher rank; only a strict outrank opens the path.

## The M-Booth flow (MBOOTH)

Same engine, `Kind=MBOOTH`. Detect the requested booth is shared-use and its hold covers the slot →
open a request to the booth's holder → resolve the same way (holder replies `yes`, or the requester
attests the holder cleared it; Airtable break-glass behind both) → on approval, re-check and create
the event, notify the holder. The router / consent-gate / deadline logic is already
scaffolded and unit-tested in [`workflows/drafts/mbooth/`](../../workflows/drafts/mbooth/) (16/16
green as of 2026-09-21). Generalize the pending table from `M-Booth Approvals` to `Consent Requests`
with the `Kind` field so both callers share one router and one sweep.

## Every-message-path safety (the router)

The only new code on the path every message hits is the reply-router — kept deterministic and
**fail-open** (already written and tested for M-Booth; generalize it):

- A message is a consent reply **only if** it is in the dedicated approvals channel **and** matches a
  PENDING row **and** is from that row's approver — else it is a `normal` message and flows down
  today's pipeline **byte-for-byte unchanged**. Own-bot messages ignored.
- A dedicated channel (e.g. `#approvals`, threaded) is what keeps the router a channel-id equality
  check rather than fuzzy matching — normal bookings (DM) and consent replies (channel) are
  physically different message populations. Proven by running the full `test-nodes` suite against the
  ELSE branch (zero regression) before any canary.

## Build order — target: live **before launch (25 Sep)**

Howard's call 2026-09-21: build ASAP, pre-launch. Sequenced so the highest-value, lowest-risk pieces
land first and each step is independently shippable — if the calendar tightens, we stop at whatever
step is done and it's still coherent. Every step: build on a **candidate/canary** copy, run the full
`test-nodes` suite against the unchanged ELSE branch (zero regression) + offline tests, snapshot with
`backup-live` before import, `n8n-write put` then pull to confirm stored, `health` to confirm ran.

- **Step 0 — foundations, zero live-path risk (in progress now):** Tel enters the **session-type
  ranking** in Airtable (inert until read — see spec below); priority-classification pure function
  scaffolded + unit-tested offline (`workflows/drafts/preempt/`, not wired).
- **Step 1 — Airtable `Consent Requests` table** (config).
- **Step 2 — attestation fast path (outage-proof, biggest value/risk ratio).** The requester's
  *"cleared with `<name>`"* resolution + two-way notification. Delivers most of the value with **no
  async and no every-message-path change** — it's a branch inside Move/Book, gated on authority +
  the priority outrank. **This is the realistic pre-launch core.**
- **Step 3 — reply-router + consent gate** (the incumbent's async `yes`/`no`; generalize the tested
  M-Booth router — the one new component on the every-message path, fail-open).
- **Step 4 — sweep** (scheduled ~10 min): expire past deadline; **nudge** aging PENDING rows by
  re-posting the ask (extra hardening for a dropped reply).
- **Step 5 — PREEMPT finalize:** the all-or-nothing move-incumbent-then-place-requester
  choreography + the `ROOM_OCCUPIED` priority branch.
- **Step 6 — Airtable-direct break-glass:** sweep reads a human-set `Status` and finalizes.
- **Step 7 — prompt sections, offline tests, canary pass, careful live merge.**

**Honest risk note:** Steps 2 is genuinely pre-launch-feasible and low-risk. Steps 3–5 (the async
router + sweep + the two-booking relocation choreography) are the materially bigger, higher-risk part,
landing on the every-message path and the `ROOM_OCCUPIED` guard during launch week. If all of it
can't be made solid by the 25th, ship Step 2 (+ M-Booth attestation) and finish 3–5 right after —
the design is the same either way, so nothing is thrown away.

## Airtable spec — session-type priority ranking (for Tel)

**Where:** `Session Types` table (`tblxEvRNPneUhQxUv`), base `app8GQxEInqJi1NRP`.

**Add one field:**

```
Field name:  Preemption Rank
Field type:  Number (integer, precision 0)
Meaning:     Higher number outranks lower. A booking may preempt an occupied room
             ONLY IF its type's rank is STRICTLY GREATER than the incumbent's.
             Equal ranks never preempt. Blank = 0 = lowest (never preempts, always preemptible).
```

Why a single number (not the existing `Priority`/`Last Resort` links): those rank *rooms within a
session type*. This is a different axis — ranking *session types against each other* so Jessie can
tell, deterministically, that a Celebrity Recording outranks a VO Recording. Kept as data so the
model never judges priority (the CLAUDE.md principle).

**Suggested starting ranks — Tel to set/adjust** (round numbers leave room to insert later; the
gaps are deliberate):

| Session Type | Suggested Rank |
|---|---|
| Celebrity Recording | 100 |
| Localization Dubbing | 80 |
| Band Recording | 70 |
| Music Vocal Recording | 60 |
| VO Recording | 60 |
| Localization Editing | 50 |
| Localization Mixing | 50 |
| Localization Atmos Mixing | 50 |
| Music Mixing | 50 |
| Post Mixing | 50 |
| QC | 30 |
| Event | 20 |
| Meeting | 10 |

These are a *starting point only* — the operational judgment is Tel's. The one rule the code relies
on: **only a strict outrank opens preemption; equal or lower is refused as it is today
(`ROOM_OCCUPIED`).** So two rank-60 bookings can never bump each other, which is the safe default.

I have **not** created this field — it's a spec for Tel to add (or say the word and I'll create it,
with your approval, since it's inert until the preemption branch reads it).

## Inputs still needed (Howard ⇄ Tel — Tel = she/her)

- **Session-type ranking values** — Tel fills `Preemption Rank` per the spec above.
- **Consent model — DECIDED 2026-09-21:** requester-attestation OR incumbent-consent, first resolver
  wins; Airtable-direct is backup-only when both Slack paths fail; two-way notify on the incumbent's
  yes. Howard may refine exact wording after the Tel discussion, but the shape is fixed and built to.
- **Approver identity** for PREEMPT — incumbent's booker (`ref:`) and/or that dept's coordinator?
- **Relocation choreography confirm** — all-or-nothing move-then-place, incumbent's new slot agreed
  in the DM (per Howard 2026-09-21).
- **Approvals channel** — create `#approvals`, invite Jessie, give the channel id.
- **M-Booth specifics** — shared-use booth set + each holder's Slack id; how "held" is detected
  (standing calendar event vs static map); window/timeout rules; no-response policy.
- **Timeout / no-response policy** — expire silently vs notify the requester.
