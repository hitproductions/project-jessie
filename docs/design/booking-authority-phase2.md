# Design — Booking authority Phase 2 (cross-department) + M-Booth shared use

Status: **draft for discussion** · 2026-09-19 · Owner: Howard · Builds on
[booking-authority.md](booking-authority.md) (Phase 1, done)

## Problem

Phase 1 lets an authorized coordinator move/cancel a booking **in their own department**, and
notifies the booker + engineer. Two things it deliberately left out:

1. **Cross-department.** A coordinator sometimes needs to move/cancel a booking in *another*
   department (a last-minute celeb session needs Studio F, held by a VO booking owned by another
   dept). Also the S&A/BD "Client Booking" people, whose home department is never a booking's
   producing department, so today they can't act on anything (see the Phase 1 finding).
2. **M-Booth shared use.** Some M-Booths carry a **standing hold** for an owner/department
   (historically M2→Peemo, M6→Nicole, M7→BD). Someone else wanting that booth needs the holder's OK.

Both are the same shape: *acting on something that isn't yours, which needs someone else's consent.*

## Two models for consent

### 2a — Attested consent (synchronous, lightweight) — recommended first

Coordinators already sort these out with the concerned parties out-of-band. So Jessie doesn't run
the approval itself — it **requires the coordinator to attest** that they have, then proceeds and
**informs the affected people afterward** (reusing the Phase 1 notification sender).

- Single conversation, one turn, no waiting, no pending store, no extra Slack IDs or channel —
  so **none of the async/outage risk**. This is the whole reason it's feasible quickly.
- The affected parties are still told (post-hoc DM), so nothing happens silently.
- Trade-off: Jessie trusts the coordinator's attestation rather than collecting the other party's
  actual reply. For a small, accountable internal team that is a reasonable **policy choice** — and
  it is logged (who they said they cleared it with).

**Gate (in the Move / Cancel sub-workflow, extending the Phase 1 check):**

```
owner                      → allow                          (Phase 1)
coordinator, same dept     → allow                          (Phase 1)
coordinator, OTHER dept    → allow ONLY IF attestedConsent  (Phase 2a)
                             else → NEEDS_CONSENT (ask, don't refuse)
not a coordinator          → NOT_YOURS                      (unchanged)
```

`attestedConsent` is read from the Slack history like the confirmation gate — an explicit,
deterministic phrase, not model-judged. Flow: on a cross-dept attempt the tool returns
`NEEDS_CONSENT`; Jessie says *"That booking is in {dept}, not yours. Have you cleared this with
{the booking's owner / that dept's coordinator}? Reply `confirmed with <name>` to proceed."* On the
attested reply, the change goes through and the booker + engineer **and the other department's
coordinator** are notified. Only someone who is a coordinator *somewhere* can attest; a Standard
user still gets `NOT_YOURS`.

### 2b — Live consent (asynchronous, full) — later

Jessie actually asks the other party and waits for their real yes/no. This is the system the
earlier M-Booth design landed on (event-driven + **pending store**, no tentative hold):

- **Airtable `Consent Requests` table** (durable, survives an n8n restart — the reason not to use a
  Wait node): who asked, which booking, who must approve, deadline, status, the approval message ts.
- The action does **not** happen up front — only a PENDING row is written.
- Jessie posts the request to the approver (a dedicated channel such as `#approvals`, threaded —
  more reliable to correlate than a DM).
- The **main workflow** must, on every inbound message, check whether it is a reply to a pending
  request and route it to a **consent gate** (deterministic yes/no from the *right* person).
- A **scheduled sweep** (~10 min) expires stale requests past their deadline.
- On approve → perform the change (re-checking availability) + notify. On reject/expire → tell the
  requester.

This is materially bigger and carries the async/outage risk; it belongs **after launch**.

## M-Booth shared use — the same pattern

A booking on a shared-use booth (M2/M6/M7) at a time the booth is held is "acting on something that
isn't yours." Two ways to ship it, matching the two models:

- **2a (attested):** detect the requested booth is shared-use and its hold covers the slot; Jessie
  says *"M2 is held by Peemo — have you cleared this with them? Reply `confirmed with Peemo`."* On
  the attestation, book it and notify the holder. **No tentative hold, no async, no sweep.**
  Feasible pre-launch (see below).
- **2b (live approval):** the full async approval with the pending table + `#m-booth-approvals`
  channel + sweep + the three approver Slack IDs + the timeout policy. This is the earlier
  `MBOOTH-APPROVAL-DESIGN.md` design (in the old *JESSIE for Claude* repo). Post-launch.

Either way, **book only on approval/attestation — never a tentative calendar hold** (that was the
"doesn't have to hold it" point: a blocking event would falsely occupy the slot and fight Rule 1).

## Enforcement & security

- All decisions stay in the sub-workflows, not the prompt (the Phase 1 principle).
- The attestation / consent must be an explicit deterministic match (like `Gate Context`), never
  model-judged. The requester must already be an authorized coordinator to even be offered the
  cross-dept / shared-use path.
- Whatever path, the affected people are **notified** — the Phase 1 sender already does this.

## Build order

1. **2a attested cross-department** — extend the Move/Cancel ownership check with the `NEEDS_CONSENT`
   branch + an attestation read; prompt wording for the ask; notify the other dept's coordinator.
2. **2a M-Booth shared use** — shared-use booth detection + hold check + the same attestation gate;
   book on attestation.
3. **2b live consent** (post-launch) — the `Consent Requests` table, the main-workflow consent
   router, the consent gate, the sweep. M-Booth async approval reuses it.

## Inputs / decisions needed

- **Policy:** is an *attestation* acceptable (2a), or must Jessie collect the other party's actual
  reply (2b)? This is the fork.
- For M-Booth: the **shared-use booth set** (M2/M6/M7?) and each booth's **holder/approver**
  (M2→Peemo, M6→Nicole, M7→BD — confirm, and whether M2/M6 are active), and whether "held" is read
  from a standing calendar event or a static map.
- For 2b only: approver Slack IDs, the approval **channel**, and the **timeout policy** (what happens
  on no response).
