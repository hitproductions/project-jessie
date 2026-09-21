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
2. **The incumbent consents** — the incumbent/holder replies `yes` to Jessie's request **in their
   own DM with Jessie**. The async path; self-heals on Slack retry.

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
| `Requester DM` · `Approver DM` | the DM channel ids where each side is corresponded (replies arrive here) |
| `Log Thread TS` | the `#jessie-approvals` back-end mirror post, for audit/coordination (not where people reply) |
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

1. Requester asks for a room that is occupied. `Check New Window` returns `ROOM_OCCUPIED` — and
   **that guard is never touched.** The new branch does not let a booking through an occupied room;
   it just, when the requester's **session-type rank outranks the incumbent's** (data — see below)
   *and* the requester is authorized, offers the consent path **instead of a bare refusal**.
2. Jessie DMs the approver (the incumbent's booker, resolved from the event `ref:`):
   *"`<Requester>` needs `<Room>` on `<slot>` for a higher-priority `<session type>`. You hold it
   for `<incumbent title>`. Are you OK to move? If yes, what time works for your session?"* Writes
   the PENDING row. **No calendar change yet** (no tentative hold — that would falsely occupy the
   slot and fight Rule 1).
3. Approver consents — by their DM reply, by the requester's attestation, or (break-glass) by an
   Airtable edit — and the relocation slot is agreed **through that DM conversation** (Jessie does
   not pick it unilaterally; Howard's rule).
4. Finalize — **exactly a normal edit, clearing the room first, and it never double-books**
   (Howard's rule 2026-09-21). It reuses the existing, live authorized **Move Booking** to relocate
   the incumbent to the agreed slot (which frees the contested room the normal way), then a normal
   **Book Session** places the requester into the now-genuinely-empty room. The double-book guard
   stays exactly as-is because by the time the requester is booked the room really is free. Ordered
   and all-or-nothing: if the incumbent's move fails, nothing else happens; if the requester's
   booking then fails, the row goes `FAILED` and the incumbent has still only been moved to the slot
   they agreed to — never left homeless, never a double-book at any instant.
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

## Where people are corresponded — Jessie DM (decided 2026-09-21)

**All human correspondence happens in the person's own Jessie DM** — the requester attests in their
DM, and the incumbent/holder is asked and replies in *their* DM. Nobody has to watch a separate
place. Howard's call: users deal only with Jessie.

The `#jessie-approvals` channel (**`C0C34UMFXGD`**, created 2026-09-21) is a **view/audit feed only**
— a restricted mirror where relevant coordinators can see requests/approvals that span
people/departments at a glance without opening Airtable. Jessie *posts* each request and its outcome
there; **nobody replies there** (correspondence is DM) and it is **not** used for routing (the router
keys on the pending row). The durable record is still the Airtable `Consent Requests` table; this
channel is the human-readable convenience view on top of it. People who aren't involved never see it.

### The router, now that replies arrive in DMs

The only new code on the every-message path is the reply-router — deterministic and **fail-open**.
Because replies now come by DM (not a dedicated channel), it can't route by channel-id; instead it
routes by **pending-row state**, which is just as deterministic:

- A DM is a consent reply **only if** the sender has a **PENDING `Consent Requests` row awaiting
  them** (they are its `Approver`, or its `Requester` on the attestation path). Otherwise it's a
  `normal` message and flows down today's pipeline **byte-for-byte unchanged**. Own-bot messages
  ignored.
- **The one edge case** the old channel design avoided for free: a person who has a pending consent
  *and* is mid-booking in the same DM. Handled by (a) the consent DM asking for an explicit, clearly
  worded reply, and (b) if a reply is ambiguous, Jessie asks to clarify rather than guessing — never
  model-judged silently. Rare, and it degrades to a clarifying question, never a wrong action.
- **Latency — the pending-row read MUST go in the existing parallel Airtable fan-out** at the top of
  the turn (alongside `Get Booker` / `All Rooms` / `All Session Types`, which already run
  concurrently ~1s). It runs on every message, but overlapping the reads that already happen makes
  its wall-clock cost ~0 — the only cost is one API call, not turn time. Do **not** wire it as a
  serial step before the agent. Query is server-side filtered (`status = PENDING AND
  (approver = sender OR requester = sender)`), almost always zero rows. Fail-open: a slow/errored
  read → treat as no pending row → normal message, so it can never block or break a booking.
- Proven by running the full `test-nodes` suite against the ELSE branch (zero regression) before any
  canary. Generalize the tested M-Booth router from a channel-id check to a pending-row check.

## Build order — target: **major dev done by 23 Sep**, polish headroom to 5 Oct, **launch 12 Oct**

Howard's call 2026-09-21: build ASAP. Per the amended sprint the dev freeze is **23 September**
(24 Sep = QA round 2, 25 Sep = address QA), with back-end polish headroom until **5 October** and
launch on **12 October**. So the full feature — including the relocation finalize — is comfortably in
scope, because the finalize no longer touches the double-book guard (see below). Sequenced so the
highest-value, lowest-risk pieces land first and each step is independently shippable. Every step:
build on a **candidate/canary** copy, run the full `test-nodes` suite against the unchanged ELSE
branch (zero regression) + offline tests, snapshot with `backup-live` before import, `n8n-write put`
then pull to confirm stored, `health` to confirm ran.

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
- **Step 5 — PREEMPT finalize:** relocate the incumbent with the existing authorized **Move Booking**
  (frees the room), then a normal **Book Session** — ordered, all-or-nothing, **never touches the
  double-book guard** (the room is genuinely free before the requester is booked).
- **Step 6 — Airtable-direct break-glass:** sweep reads a human-set `Status` and finalizes.
- **Step 7 — prompt sections, offline tests, canary pass, careful live merge.**

**Risk note (lower than before, now that the guard is untouched):** Step 2 is low-risk. The bigger
part is Step 3 (the router now lives on the every-message path) and Step 5 — but Step 5 reuses the
live, tested Move + Book rather than modifying `ROOM_OCCUPIED`, so its risk is orchestration (order,
all-or-nothing, failure handling), not a new exception to the one guard that prevents double-booking.
The 23 Sep → 5 Oct window is enough for all of it. If anything slips, the fallback order still holds:
ship Step 2 (+ M-Booth attestation) first and finish 3–5 in the polish window — same design, nothing
wasted.

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
- **Approvals channel — DONE.** `#jessie-approvals` created 2026-09-21, id **`C0C34UMFXGD`**,
  **Jessie invited** — view/audit feed only (Jessie posts here, nobody replies here, not used for
  routing). Fully set.
- **M-Booth specifics** — shared-use booth set + each holder's Slack id; how "held" is detected
  (standing calendar event vs static map); window/timeout rules; no-response policy.
- **Timeout / no-response policy** — expire silently vs notify the requester.
