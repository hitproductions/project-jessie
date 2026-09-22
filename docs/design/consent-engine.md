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

> **All consent state lives in one Google Sheet. Nothing is ever held in a running execution
> waiting for a reply. An outage can therefore only *delay* a consent — never lose or corrupt one.**

No `Wait` node, ever: a paused n8n execution is lost on a restart, and this box has had outages.
Instead the work is a set of **short, independent executions** whose only shared state is a **row**.

### Our actual outage, mapped to each step

The known failure is a **Cloudflare 403 at the edge**: inbound webhooks never reach n8n, while n8n
keeps running internally and its *outbound* network (Slack API, Airtable, Calendar) still works.
Scheduled triggers still fire (they are not inbound). Against that reality:

| Step | Needs | During an edge outage |
|---|---|---|
| ① **Request** — write the PENDING row | outbound → Google Sheets | Row write succeeds once the turn runs; **survives** |
| ② **Reply** — incumbent/holder answers in Slack | **inbound** event → n8n | **The only fragile step.** A dropped reply is recovered by the out-of-band path (below) or Slack's own event retries |
| ③ **Sweep** — expire / nudge stale rows | internal schedule | Schedule-triggered, not inbound → **runs anyway** |
| **Finalize** — book/move + notify | outbound | **Works**; re-checks availability and compare-and-sets Status so a duplicate reply cannot double-book |

So there is exactly **one** outage-fragile point — receiving a live reply — and the design gives it
two independent fallbacks. That is the whole answer to "can we build it so an outage doesn't break
it": **yes — an outage delays a consent, it never breaks one.**

## How a request resolves — two Slack paths, first one wins, Sheet edit as backup

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

**Sheet-direct edit — backup only.** A coordinator *can* flip the row's `Status` in the Google Sheet
itself, and the sweep will finalize it — but this is a **fallback used only when both Slack paths
above fail** (e.g. a prolonged outage drops the reply *and* the requester can't reach Jessie either).
Nobody should need to open the Sheet in normal use; it's the break-glass path that keeps a consent
recoverable when Slack is unreachable, because the decision is durable in the Sheet and finalize runs
on the next scheduled sweep (which fires even while the edge is down). (This path is the reason a
Sheet the team can actually edit beats an Airtable table they can't.)

One record → resolver races (requester attest / incumbent reply) → Sheet break-glass behind them
→ one idempotent finalize. No path can double-book (finalize re-checks availability at that instant).

## The durable record — a `Consent Requests` **Google Sheet** (not Airtable)

Decided 2026-09-21: the pending store is a **Google Sheet**, reusing the exact setup the booking log
already uses live — the `jessie-booking-log` service account and its `googleApi` credential
(`DU75rLW4KHlVhcK1`). **A new tab `Consent Requests` in the existing Jessie Log spreadsheet**
(`1vIQ_cf2jJJ_WKpwFfnZQjQeKg2cxQz4tXGS6RZTEMwo`), which is already shared to that service account — so
**no new credential and no new sharing**, just a tab + a header row. Two reasons over Airtable: (1)
the team has no Airtable edit access but *can* edit this Sheet, which also makes the break-glass
manual path (below) actually usable by them; (2) it reuses a proven, outage-tested integration.

One row per request; header row = these columns in order. Serves both callers via `Kind`.

| Column | Purpose |
|---|---|
| `Request ID` | unique id (e.g. `<ts>-<requester>`), the **key the update/finalize matches on** (Sheets updates match a column, not a record id) |
| `Status` | `PENDING` / `APPROVED` / `REJECTED` / `EXPIRED` / `DONE` / `FAILED` |
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
| `Resolved Via` | `reply` / `attestation` / `sheet` (audit — also records the decider) |
| `Attested By` | who attested, when the fast path was used |
| `Decided At` | timestamp of resolution (audit) |
| `Req Payload` | **(added 2026-09-21, 24th column)** JSON of the requester's original Book Session inputs (summary, session_type, client, engineer, description, department, all_day…), written at Open time. Finalize needs it to place the requester after freeing the room; the row can't hold those field-by-field. |

(24 columns. `Decided By` was dropped since `Attested By` + `Resolved Via` capture who/how; `Req
Payload` was added when building Finalize surfaced that the requester's booking details must survive
to finalize-time. **The tab needs `Req Payload` appended as a 24th header**, and `Open Consent
Request` updated to write it.)

**Sheets specifics vs the Airtable plan:**
- **Reads** (router + sweep) use the Google Sheets *read* op and filter in a Code node — the table is
  tiny (usually 0–few `PENDING` rows), so a full read is cheap and folds into the parallel fan-out.
- **Updates** (finalize / resolve) use *update row* matched on `Request ID`.
- **Atomicity caveat:** a Sheets read-then-update isn't transactional, so two resolutions landing in
  the same instant could both see `PENDING`. Rare, and harmless in practice — the finalize re-checks
  the room and the calendar guards (`ROOM_OCCUPIED`, etc.) still prevent any actual double-book
  downstream, and finalize re-reads `Status` immediately before the mutation. (Airtable had no
  row-locking either, so this is not materially weaker.)

## The state machine

```
              requester attests  ─┐   (first resolver wins)
              incumbent replies yes ┼─▶ APPROVED ──▶ finalize ──▶ DONE
              Sheet APPROVED (backup) ─┘                          │
                                                                   └─ availability lost / error ▶ FAILED
  request ──▶ PENDING
              incumbent replies no / Sheet REJECTED ──▶ REJECTED  (terminal, sticky — attestation cannot flip it)
              deadline passed (sweep) ─────────────────▶ EXPIRED
```

- **Finalize is idempotent (compare-and-set).** It re-reads the row, acts only if `Status` is still
  `PENDING`, flips it to a terminal state, re-checks availability at that instant, then books —
  otherwise it does nothing. So the **first** resolver (requester attestation or incumbent reply)
  wins the race, and a second arriving signal is a harmless no-op.
- **`REJECTED` is sticky.** An explicit incumbent "no" (or a `REJECTED` set in the Sheet) is terminal; a
  later requester attestation cannot override it.
- **Anything unclear stays PENDING** (same spirit as the confirmation gate); the sweep or a clearer
  reply resolves it. Never model-judged.

## The preemption flow (PREEMPT), end to end

1. Requester asks for a room that is occupied. `Check New Window` returns `ROOM_OCCUPIED` — and
   **that guard is never touched.** The new branch does not let a booking through an occupied room;
   it just, when the requester's **session-type rank outranks the incumbent's** (data — see below)
   *and* the requester is **authorized**, offers the consent path **instead of a bare refusal**.
   **Authorized requester** = the same set as the Rule-1 move exception, verified live in
   `Resolve Booking`: Bookers `Authority` of **`Dept Head`** or **`Client Booking`**, or **`HAIST
   Dev`** (a Standard user only ever gets the plain `ROOM_OCCUPIED` refusal). **Department scope for
   preemption (DECIDED YES, 2026-09-21):** unlike a plain authorized move (own-department only), a
   coordinator **may** preempt a booking in **another** department — because the incumbent booker's
   **consent is what authorizes the cross-department action**. No consent → nothing moves; the
   boundary is bridged only by the affected owner's own yes. HAIST Dev keeps its existing cross-dept
   reach.
2. Jessie DMs the approver (the incumbent's booker, resolved from the event `ref:`):
   *"`<Requester>` needs `<Room>` on `<slot>` for a higher-priority `<session type>`. You hold it
   for `<incumbent title>`. Are you OK to move? If yes, what time works for your session?"* Writes
   the PENDING row. **No calendar change yet** (no tentative hold — that would falsely occupy the
   slot and fight Rule 1).

   > **Cross-department scope: DECIDED YES (2026-09-21).** A coordinator may preempt across
   > departments gated on the incumbent's consent — so the celeb-over-VO case (requested by Ms. Letty
   > / S&A, who are coordinators not HAIST Dev) works, with the VO owner's yes as the safeguard.
   > **Parked idea (not for now):** letting a *non-coordinator* preempt purely on higher priority, to
   > save the dept head work — moot today since the real high-priority requesters are coordinators.
3. Approver consents — by their DM reply, by the requester's attestation, or (break-glass) by an
   Sheet edit — and the relocation slot is agreed **through that DM conversation** (Jessie does
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
attests the holder cleared it; Sheet break-glass behind both) → on approval, re-check and create
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
people/departments at a glance without opening the Sheet. Jessie *posts* each request and its outcome
there; **nobody replies there** (correspondence is DM) and it is **not** used for routing (the router
keys on the pending row). The durable record is the `Consent Requests` Google Sheet; this
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
- **Latency — the pending-row read MUST join the existing parallel read fan-out** at the top of the
  turn (alongside the Airtable `Get Booker` / `All Rooms` / `All Session Types`, which already run
  concurrently ~1s). It's a Google Sheets *read* of the `Consent Requests` tab (the sheet is tiny —
  usually 0–few `PENDING` rows), filtered in a Code node to rows where the sender is the `Approver`
  or `Requester` and `Status = PENDING`. It runs on every message, but overlapping the reads that
  already happen makes its wall-clock cost ~0 — the only cost is one API call, not turn time. Do
  **not** wire it as a serial step before the agent. Fail-open: a slow/errored read → treat as no
  pending row → normal message, so it can never block or break a booking.
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
- **Step 1 — `Consent Requests` Google Sheet tab** (config): a new `Consent Requests` tab + header
  row in the existing Jessie Log spreadsheet (already shared to the `jessie-booking-log` service
  account — reuse credential `DU75rLW4KHlVhcK1`, no new setup).
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
- **Step 6 — Sheet-direct break-glass:** sweep reads a human-set `Status` in the Sheet and finalizes.
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
(`ROOM_OCCUPIED`).** So two equal-rank bookings can never bump each other, which is the safe default.

**As actually set by Tel, 2026-09-21 (LIVE in Airtable, field `fldoLFpIKDG1JCrFt`; provisional —
Howard to polish ~22 Sep):**

| Rank | Session types |
|---|---|
| 100 | Celebrity Recording |
| 90 | Band Recording |
| 50 | everything else (QC, Post Mixing, Localization Editing/Mixing/Atmos Mixing, Event, Music Vocal Recording, Meeting, Localization Dubbing, Music Mixing, VO Recording) |

Consequence today: **only Celebrity and Band Recording can preempt anything**; all others are equal
(no mutual preemption). Accepted as the starting policy so we can build. **Howard's intent for the
polish pass:** Celebrity is the objective top priority, *especially for Studios F and C*; Music Vocal
Recording to be raised above the 50 floor later. Nothing in the engine changes when these numbers
move — it reads them live.

## Inputs still needed (Howard ⇄ Tel — Tel = she/her)

- **Session-type ranking values** — Tel fills `Preemption Rank` in Airtable per the spec above.
  (Howard has no Airtable edit access, so this is Tel's to do; it's the one remaining Airtable item.)
- **`Consent Requests` Sheet tab — DECIDED 2026-09-21 (Google Sheets, not Airtable).** New tab
  `Consent Requests` + header row in the existing Jessie Log spreadsheet
  (`1vIQ_cf2jJJ_WKpwFfnZQjQeKg2cxQz4tXGS6RZTEMwo`, already shared to the `jessie-booking-log` service
  account — reuse credential `DU75rLW4KHlVhcK1`). Chosen because the team can edit a Sheet but not
  Airtable, and it reuses the live booking-log integration. **DONE 2026-09-21** — tab created with the
  23-column header verified via the Drive connector (`Decided By` dropped; `Attested By` +
  `Resolved Via` cover who/how).
- **Consent model — DECIDED 2026-09-21:** requester-attestation OR incumbent-consent, first resolver
  wins; Sheet-direct edit is backup-only when both Slack paths fail; two-way notify on the incumbent's
  yes. Howard may refine exact wording after the Tel discussion, but the shape is fixed and built to.
- **Approver identity for PREEMPT — DECIDED 2026-09-21: the incumbent's booker** (resolved from the
  event `ref:`). **TODO (definitely, later):** add the "either" escalation — ask the booker first,
  fall back to that department's coordinator if the booker doesn't respond by the deadline. Start
  with booker-only; build the escalation after.
- **Authorized-to-preempt — DECIDED 2026-09-21:** Dept Head / Client Booking / HAIST Dev only
  (verified against live `Resolve Booking`); Standard users cannot preempt. **Cross-department:
  DECIDED YES (2026-09-21)** — coordinators may reach across departments gated on the incumbent's
  consent. **Parked:** widening to non-coordinators on priority alone (moot today).
- **Relocation choreography confirm** — all-or-nothing move-then-place, incumbent's new slot agreed
  in the DM (per Howard 2026-09-21).
- **Approvals channel — DONE.** `#jessie-approvals` created 2026-09-21, id **`C0C34UMFXGD`**,
  **Jessie invited** — view/audit feed only (Jessie posts here, nobody replies here, not used for
  routing). Fully set.
- **M-Booth specifics** — shared-use booth set + each holder's Slack id; how "held" is detected
  (standing calendar event vs static map); window/timeout rules; no-response policy.
- **Timeout / no-response policy** — expire silently vs notify the requester.

## Build progress

- **2026-09-21 — `Open Consent Request` built** (workflow id `nEHnCMMXS0am59Zy`, **inactive, not
  wired** — touches nothing live). Writes the PENDING row + DMs the incumbent + posts the audit line.
  Logic offline-tested (`workflows/drafts/consent/open-request.js`, 15/15); repo file
  `workflows/open-consent-request-v1.json`; created in n8n and verified by pull (Sheets tab
  `gid=431550013`, log credential, Slack v2.2 best-effort). Not activated yet — it's only callable
  once Book/Move are wired to invoke it (then activate per gotcha 0). Engine core logic:
  `workflows/drafts/consent/logic.js` (21/21).

- **2026-09-21 — `Finalize Consent` core built + tested (logic only; n8n assembly deferred to
  wiring).** `workflows/drafts/consent/finalize.js`, 28/28 offline. Reuses the LIVE sub-workflows:
  - **Relocate the incumbent via `Move Booking`, invoked AS the incumbent** (`requester` = incumbent
    booker id) → `owner===true`, so `NOT_YOURS` never triggers and **no guard is modified**;
    `confirmed:true` (consent). Move keeps the contested room, new agreed time — freeing the req slot.
  - **Place the requester via `Book Session`** (`confirmed:true`, `room_override:true`) into the
    now-free room — a normal booking; the double-book guard is untouched because the room really is
    free by then.
  - **All-or-nothing, move-first:** `classifyMove` (`MOVED`/`PARTIAL`/`REJECTED`) gates whether the
    requester is placed; a `PARTIAL` (Move's replacement-made-but-original-not-deleted) or `REJECTED`
    stops before booking, marks the row `FAILED`, and tells the requester nothing changed. If Move
    succeeds but Book then fails, the incumbent is only ever at the slot they agreed to — never
    homeless, never a double-book.
  - Row goes `DONE` (Sheets update matched on `Request ID`) with `Resolved Via`/`Decided At`;
    notifies incumbent (moved) + requester (booked), or requester (failed) with the honest reason.
  - **Deferred to increment #3 (wiring):** the n8n workflow assembly + create. Two reasons — it needs
    the new `Req Payload` column to exist, and its `executeWorkflow` input-passing can only be
    validated by a real approved request, not a pull. Building it blind/inactive now would be false
    assurance.

### Follow-ups this surfaced
- **Add `Req Payload` (24th column)** to the Consent Requests tab (Howard — he can edit the Sheet).
- **Update `Open Consent Request`** to accept the requester's Book payload and write it into
  `Req Payload` (mine — small change to the isolated, inactive workflow).

- **2026-09-21 — #3 trigger logic built + tested (logic only, no live changes yet).**
  `workflows/drafts/preempt/branch.js`, 15/15. At a `ROOM_OCCUPIED` conflict, `preemptAtConflict`
  parses the incumbent's `SType`/`ref` off its event description, runs `decidePreempt`, and — when the
  authorized requester strictly outranks a *readable* incumbent and the incumbent's booker is known —
  returns the Open Consent Request context (approver = incumbent booker). Otherwise it falls through
  to the normal refusal. **New live-data decision:** Book Session will stamp `SType: <session type>`
  on the event description (additive, like `Dept:`/`Type:`), so future incumbents are rankable;
  pre-stamp events carry no `SType` and are never preemptible (safe — `INCUMBENT_RANK_UNKNOWN`).

### #3 remaining — the FIRST live-touching work (checkpoint + candidate + test-nodes + backup each)
1. **Book Session (candidate):** add the `SType:` stamp on Create Event; at `ROOM_OCCUPIED`, run
   `preemptAtConflict` (needs requester authority + `Preemption Rank` read + reqPayload passed from
   main) → on offer, call `Open Consent Request` (executeWorkflow) and return its message; else the
   normal refusal. Activate `Open Consent Request` once it's actually called (gotcha 0).
2. **Move Booking (candidate):** the same preempt branch at its `ROOM_OCCUPIED` (`Check New Window`).
3. **Main (candidate):** add the pending-row Sheets read into the parallel fan-out + the
   `classifyInbound` router; consent-reply branch → consent gate (`resolveConsent`) → `Finalize
   Consent`; normal branch unchanged (prove zero regression against the full `test-nodes` suite).
4. **Build + create `Finalize Consent`** in n8n and wire it; validate end to end with a real approved
   request on year-shifted dates. Then `MBOOTH` rides the same engine.

- **2026-09-22 — #3 PROVEN END-TO-END LIVE (with fixes).** Drove the full book-preempt path via
  Slack QA (Howard-authorized). Calendar ground truth on the year-shifted date confirmed the whole
  mechanism: a Celebrity Recording request into an occupied Studio F → preempt detected → `Open
  Consent Request` wrote a PENDING row + DMed the incumbent + informed the requester → the incumbent
  consented and moved their own booking via the normal Move flow → Move Booking's tail hook matched
  the PENDING row by `Incumbent Event Id` → `Finalize Consent` placed the requester into the freed
  slot. End state: **INCUMBENT relocated + the higher-priority booking placed, no double-book.**

  **Five bugs found and fixed live to get there (all imported + verified stored + health green):**
  1. **Consent Sheets nodes must reference the tab by its numeric gid, not by name.** The Google
     Sheets *append/update* operation resolves the sheet by gid; `mode:list value:"Consent Requests"`
     fails `Sheet with ID Consent Requests not found` (only *read* tolerates the name). Set all six
     consent nodes to `value:"431550013"` (Open `Write Pending Row`; Finalize `Mark Done`/`Mark Failed
     Place`; main `Read Pending Consent`/`Mark Rejected`; move `Read Consent Rows`).
  2. **`Read Pending Consent` / `Read Consent Rows` must set `alwaysOutputData: true`.** With the
     correct (usually empty) consent tab, a 0-row read makes n8n skip every downstream node —
     silently killing the entire main workflow after `Read Pending Consent` (success, no reply) and
     truncating Move Booking before `Return Moved`. The old by-name read accidentally hit a non-empty
     sheet and masked this. **This is the dangerous one: an empty consent tab took Jessie fully dark.**
  3. **Decide Preempt (Book Session) must carry `reference_data` into `reqPayload`.** Finalize replays
     the requester's Book server-side; without the Room Table injection it rejects `NO_REFERENCE_DATA`.
  4. **Finalize `Book Requester` (executeWorkflow) must map `reference_data`.** The node passed 13
     fields but not `reference_data`, so it was dropped at the node boundary even though `placePayload`
     carried it. executeWorkflow only forwards mapped keys.
  5. **Finalize `Placed Book?` must match `CREATED`, not `BOOKED`.** Book Session returns
     `status:'CREATED'` on success (from `Verify`). The IF checked `=== 'BOOKED'`, so a real placement
     was mis-classified as a failure — row wrongly marked FAILED, requester told "couldn't place" when
     the calendar event had in fact been created. `classifyBook` in `finalize.js` fixed to match too.

  **Two agent-level findings opened (PENDING 26, 27):** the agent can *fabricate* a preemption offer
  without calling Book Session (no row written), and can double-call Book Session (duplicate consent
  requests / double incumbent DM). Neither risks a double-book (the guards hold); both are follow-ups.

  **Live workflow versions after this session:** main `v146`, Book Session `v35`, Move Booking `v16`,
  Finalize `v5`, Open `v2`. Test-event cleanup pending Howard's approval (INCUMBENT + CELEBTEST6 on
  Studio F 2027-11-08; three FAILED test rows in the Consent Requests tab).

- **2026-09-22 (later) — clean confirmation run PASSED + polish.** After the CREATED fix, re-ran the
  full book-preempt via Slack: agent showed a proper summary **with the "current holder" note**,
  confirm → Open (single incumbent DM, **no duplicate** this run) → incumbent moved to a free slot →
  Finalize **Return Done** → requester got **"Done - Studio F is yours"** and the incumbent a
  "moved to make way" notice. Calendar verified: INCUMBENT 9-12, CELEBTEST7 2-5, no double-book.
  **Removed the "Automated with this n8n workflow" footer** (`includeLinkToWorkflow:false`) on the five
  consent message nodes: Open `DM Incumbent`; Finalize `Notify Incumbent`/`Notify Requester OK`/`Notify
  Place Fail`; main `Notify Requester`. Live: Open **v3**, Finalize **v6**, main **v147**.
  **Small cosmetic bug still open:** the requester/incumbent notices interpolate `Approver Name`, which
  Open stores empty (Decide Preempt sets `approverName:''`), so they read "…  moved their session" with a
  blank name. Fix later: resolve the approver's display name at Open time (or in Finalize from the id).
  **Two-party QA note (Howard):** in testing Howard is both requester and incumbent (same `ref:`), so both
  DMs land in his DM. To exercise the real two-person experience, a second tester must OWN the incumbent
  booking (book it themselves, or seed a calendar event carrying their `ref:`); then Howard's preemption
  DMs the incumbent tester while requester updates stay with Howard. Consent DMs are NOT behind the
  Cancel/Move `DEV_REDIRECT`, so QA will really ping the incumbent tester (intended) — just don't seed a
  non-participant's id.

- **2026-09-22 (later) — TEST GATE so testing never DMs a real non-dev (Howard).** `Open Consent
  Request` → `Build Request` (v4) wraps the row's `Approver` and `Requester` in
  `route(id) = ALLOW.includes(id) ? id : DEV_REDIRECT` with `DEV_REDIRECT='U08V3CKDGJF'` and
  `ALLOW=[Howard, Tel, Genzo]` (HAIST devs only — deliberately narrower than Cancel/Move's list). Every
  consent DM downstream reads the row's Approver/Requester (Open `DM Incumbent` repointed at the routed
  row Approver; Finalize `Notify *`; main `Notify Requester`/`Reply Incumbent`), so routing those two
  fields once gates all of them. The tail hook matches on `Incumbent Event Id`, not `Approver`, so the
  real booking is still moved/placed; Finalize moves it as the routed Approver (Howard) via HAIST-dev
  god-mode. **Launch flip: set this `DEV_REDIRECT=''`** (now in CLAUDE.md Before-launch #2). Caveat: an
  incumbent owned by a dev (Tel/Genzo) still gets a real DM — narrow ALLOW to just Howard for pure-solo.
