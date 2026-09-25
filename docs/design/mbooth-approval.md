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
  - **Live since 2026-09-25** (open-consent-request v10, `mboothDeadline` in `Build Request`). Until then
    live had silently used the consent-engine rule (24h / 1h lead) for M-booth too; the draft had never
    been ported. PREEMPT keeps that rule. Covered by `./scripts/test-consent`.
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

## Which booths + how "held" is detected — GENERALIZED 2026-09-23 (Howard, approach A)

**No hard-coded booth list.** Any room named `M<n>` is an M-booth; **any RECURRING event on it is a
standing hold**; the holder is read off the hold's own **`ref:<slack id>` tag** in the event description
(the same convention Jessie stamps on its bookings and preemption reads off the incumbent). New or other
booths need no code change — just a `ref:` on their recurring hold.

Verified on the live calendar 2026-09-23 — the M-booth holds are inconsistent, which is exactly why we
key off `ref:` rather than titles or the map:

| Booth | Hold title | Recurring? | Marked | Holder → Slack ID |
|---|---|---|---|---|
| M1 | `M1 - Rico` | ✅ | Busy | Rico Gonzales → `U026LMLM4` |
| M2 | `M2 - Peemo` | ✅ | Free | Peemo Morato → `UPPEY3F4G` |
| M3 | `M3 - Trish` | ❌ one-off | Busy | (not a hold — one-off) |
| M4 | `M4 - Tel` | ✅ | Busy | Tel → `U098UFLG70B` |
| M6 | `M6 - Marketing` | ✅ | Free | Nicole Miller → `U06CTHTUS1Y` |

Note the split that killed the map idea: holds are Busy *and* Free (so **not** transparency-based);
titles are sometimes a person, sometimes a department (**"M6 - Marketing" is Nicole**); creators are
sometimes the holder, sometimes a shared account. Only a `ref:` on the hold is reliable.

`decideMBooth` (tested, `mbooth/logic.js`) at the `ROOM_OCCUPIED` point returns:
- **`open_mbooth`** — non-holder wants a held booth → consent request to the hold's `ref:` holder.
- **`room_taken`** — a *real* (non-recurring) booking also overlaps → ordinary first-come, normal refuse.
- **`unidentified_holder`** — a recurring hold with **no `ref:` tag** → can't route it → falls through to
  the normal refuse (safe: an untagged booth behaves exactly like today until someone tags its hold).
- **`book_as_holder`** — requester IS the hold owner → (currently falls through; own-booth booking TODO).
- **`none`** — not an M-booth / not a recurring hold → normal path.

### ONE-TIME SETUP (needs calendar write — Howard, or grant Claude write access)

Add `ref: <slack id>` to the **description** of each recurring M-booth hold (a new line is fine; the
`M<n> - <name>` title stays). This is what makes the feature work post-launch:

```
M1 - Rico       → add "ref: U026LMLM4"   (Rico Gonzales)
M2 - Peemo      → add "ref: UPPEY3F4G"   (Peemo Morato)
M4 - Tel        → add "ref: U098UFLG70B" (Tel)
M6 - Marketing  → add "ref: U06CTHTUS1Y" (Nicole Miller)
```

(M3/M5/M7/M8 when/if they carry a recurring hold — same pattern, holder's Slack ID from the Bookers
table's `Slack User ID` field.) Until a hold is tagged, requests for that booth just refuse normally.

`#jessie-approvals` is `C0C34UMFXGD` (shared with `PREEMPT`; view/audit feed only). Fully set.



### Resource transfer (cancel-then-book) — added 2026-09-23
A booth is a Google **resource with capacity 1**. The holder's standing hold reserves that resource, so
just *adding* the requester's booking left its room resource **auto-declined** (Rico kept the room). Fix
(Howard-confirmed, **M-booths only, never studios**): on consent, Finalize **cancels the holder's hold
INSTANCE for that date** (deletes just that recurring occurrence, freeing the resource) and **then** books
the requester, who now holds the room cleanly. Book Session (v40) captures the hold's event-instance id
onto the row (`Incumbent Event Id`); Finalize (v8) has a `Cancel Hold?` IF (Kind=MBOOTH && id present) →
`Cancel Hold` (Calendar DELETE the instance, onError-continue) → `Book Requester`. The PREEMPT path is
untouched (it move-then-books; nothing is deleted). Caveat: holds are all-day, so a *timed* share still
cancels the holder's whole-day instance for that date (accepted, booths only).

## Still open for the team

Only one design question remains (everything else — booth set, holders, Slack ids, held-detection,
deadline tiers, timeout policy — is confirmed above):

- **Approval rule** — the booth owner approves their own booth (proposed default), vs any-of-N. Wiring
  assumes owner-approves-own-booth unless told otherwise.

## Build status (2026-09-23)

Deterministic core offline-tested (`workflows/drafts/mbooth/logic.js`, 36/36). **Three of the four
wiring stages are LIVE + component-verified:**

1. ✅ **Detection — LIVE (Book Session v39), GENERALIZED.** Check Conflicts enriches each conflict with
   `recurring` (+ `transparent`); Decide Preempt runs `decideMBooth` before preempt eligibility. At a
   `ROOM_OCCUPIED` on **any `M<n>` booth**, a **recurring** conflict is a hold and the holder is read off
   its `ref:` tag → `open_mbooth` for a non-holder, `room_taken` if a one-off booking also overlaps,
   `unidentified_holder`/`none` fall through. No hard-coded booth list. Book Session v39's Check Conflicts
   also skips a `recurring` hold when `room_override` is set, so the consented placement books despite it.
   Verified on the live node: M4 held by Tel (ref-tagged) → open MBOOTH to Tel; untagged hold → falls
   through; non-M-booth → normal.
   Verified against the live node: a held-M2 request by a non-holder returns `offer:MBOOTH, approver=Peemo`.
2. ✅ **`MBOOTH` request — LIVE (Open v6).** Open takes a `kind` input (default PREEMPT); Build Request
   writes `Kind`; Build Messages has booth wording ("… your standing booth, OK to let them use it?").
   Book Session's Decide Preempt builds the MBOOTH `open` object (approver=holder, relocation fields
   empty, the booth's Book payload in `Req Payload`). Reuses the DEV_REDIRECT gate (still Howard-only).
3. ✅ **Approve→finalize router path + CANCEL-THEN-BOOK — LIVE (main v149/v150, Book v40, Finalize v8).** Consent Router is Kind-aware: an MBOOTH row +
   holder `yes` → branch `mbooth-book`; a new `MBooth Book?` IF routes it to `Call Finalize MBOOTH`
   (place-only Book). Book Session v38 lets that placement **bypass the permanent hold** — Check
   Conflicts skips a `transparent && recurring` hold when `room_override` is set, so the consented
   booking isn't blocked by the very hold the holder just approved. Normal path verified unbroken.
4. ✅ **The Sweep — BUILT (inactive), `Jessie — Consent Sweep` QHHDevaWhMk8gSBX.** Schedule (10 min) →
   Read Pending Rows → Sweep Decide (`sweepAction`) → Route: MBOOTH past-deadline → Call Finalize
   (book, timeout=book); PREEMPT/other past-deadline → Mark EXPIRED. Schedule-triggered → fires even
   during a Cloudflare edge outage. Left **inactive** until the stale test rows are cleared — activating
   it now would BOOK the 2 stale M1 MBOOTH rows (timeout=book) and EXPIRE the stale Studio 7 PREEMPT row.
   Activate with `./scripts/n8n-write activate QHHDevaWhMk8gSBX`. (Follow-up: a per-row requester notice
   on expire; Finalize already notifies on the book path.)

**Live end-to-end test is blocked on a data gap:** the real M2/M6 standing holds are 2026 near-term
recurring events whose recurrence does NOT reach the year-shifted QA dates (2027), so M-booth stays
dormant in QA (M2/M6 just book normally there). To test the flow live, seed a `transparent && recurring`
"M2 - Peemo" event on a 2027 QA date (needs calendar write access — the connector is read-only here),
or test post-launch with `YEAR_SHIFT=0` on a real near-term date where the hold exists.

**Cosmetic follow-ups:** (1) Finalize's requester/holder notices are PREEMPT-worded ("… moved their
session to make way") — for an MBOOTH placement nothing moved, so make those notices Kind-aware. (2) An
all-day booth booking (no time given) is correct, but the DM whenPhrase rendered it "8:00 AM–8:00 AM";
fixed in Open v7 → renders "<date> (all day)".
