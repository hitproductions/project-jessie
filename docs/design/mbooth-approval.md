# Design — M-Booth shared-use approval (live async consent)

> **Superseded in part (2026-09-21) by [consent-engine.md](consent-engine.md).** M-Booth is now one
> caller of a single shared consent engine. The **interaction model changed**: correspondence is via
> **Jessie DM**, not the `#m-booth-approvals`/`#jessie-approvals` channel (which is a back-end audit log
> only), and the router keys on a pending `Consent Requests` row rather than channel-id. The **async
> skeleton below still holds** — Airtable pending row, request/reply/sweep as short independent
> executions, deadline math, fail-open router — and the drafts in `workflows/drafts/mbooth/` remain
> valid (16/16). Schedule is the amended sprint (dev freeze 23 Sep, launch 12 Oct), not "post-launch."

Status: **in build — basics scaffolded** · 2026-09-19 · Owner: Howard
Relates to [booking-authority-phase2.md](booking-authority-phase2.md) (this is the 2b / live-consent
instance of that pattern). Draft logic + tests: `workflows/drafts/mbooth/`.

## Problem

Some M-Booths carry a **standing hold** for an owner/department (historically M2→Peemo, M6→Nicole,
M7→BD). Someone else wanting that booth at a held time needs the holder's OK. The holder's reply can
take minutes to hours, but a Jessie turn is ~9s — so the booking cannot complete in one turn. It must
be *request → pending → approver replies (or the window expires) → finalize or reject*, across
**separate executions**.

## Why it is outage-safe: no waiting process, state in Airtable

We do **not** use a Wait node (a paused execution is lost on an n8n restart — unacceptable on a box
that has had outages). Instead the work is three short, independent executions, and the only thing
that persists between them is a **row in Airtable**. Nothing runs between steps.

- **① Request** (a normal ~9s turn): detect the booth is shared-use and its hold covers the slot →
  check availability now → write a **PENDING** row → post the request to the approvals channel →
  tell the requester "asked, will confirm." **No calendar event is created** (the slot is not
  falsely held; the booking is made only on approval). Execution ends.
- **② Reply** (fires when the approver answers, whenever that is): their yes/no is an ordinary Slack
  message → a fresh execution → the router recognizes it → the consent gate reads yes/no → on
  approve, re-check availability and **create the event now**, flip the row to APPROVED, notify both;
  on reject, mark REJECTED and tell the requester.
- **③ Sweep** (a scheduled workflow, ~10 min, like the 04:00 pruner): PENDING rows past their
  deadline → EXPIRED, tell the requester. Handles "approver never replied" with nothing in memory.

The **temporary status is the PENDING row**; it is *activated into a real booking* by execution ②,
which is triggered by the reply, not by anything waiting. An outage at any moment loses nothing: the
row survives, the reply still triggers ② when it lands, and ③ still expires stale rows.

## Airtable table — `M-Booth Approvals`

One row per request. Suggested fields:

| Field | Purpose |
|---|---|
| `Status` | PENDING / APPROVED / REJECTED / EXPIRED (single select) |
| `Requester` · `Requester Name` | Slack id + name of who asked |
| `Approver` | Slack id of the booth's holder (who may decide) |
| `Booth` | M2 / M6 / M7 |
| `Start` · `End` | requested slot (ISO, +08:00) |
| `Title` · `Department` · `Engineer` | the booking details needed to finalize |
| `Deadline` | computed at request time |
| `Channel` · `Thread TS` | where the request was posted, to correlate the reply |
| `Decided By` · `Decided At` | audit |

## The logic that carries the risk (scaffolded + tested)

In `workflows/drafts/mbooth/logic.js`, unit-tested in `test.js` (16 checks passing):

- **`route(msg, pending)`** — the only piece on the every-message path. A message is an approval
  reply **only if** it is in the dedicated approvals channel **and** matches a PENDING row **and**
  is from that row's approver; otherwise it's `normal` and flows down today's pipeline unchanged.
  Own-bot messages are ignored. **Fail-open:** anything unrecognized is treated as a normal message,
  so a bug here can't take Jessie down — worst case an approval doesn't finalize and the sweep
  expires it.
- **`resolveConsent(text)`** — deterministic yes/no (same spirit as the confirmation gate); anything
  unclear stays PENDING.
- **`computeDeadline(now, start, cfg)`** — earlier of (now + window) and (start − lead), floored at
  now. **The window numbers are placeholders pending Tel's real rules.**

Channel separation is what makes the router clean: normal bookings (DM) and approval replies
(`#m-booth-approvals`) are physically different message populations, so the router is a channel-id
equality check, not fuzzy matching, and the existing path is left byte-for-byte intact.

## Build order

1. **Airtable `M-Booth Approvals` table** (config).
2. **Request sub-workflow** — shared-use + hold detection, `computeDeadline`, write PENDING, post to
   channel, save thread ts. (Reuses Room Availability.)
3. **Reply-router** in the main workflow — `route()` as a Code node at the top; the ELSE branch is
   the current pipeline unchanged. Proven by running the full `test-nodes` suite against ELSE (zero
   regression) before canary.
4. **Consent gate + finalize sub-workflow** — `resolveConsent`, re-check availability, create event,
   update row, notify (reuse the Phase-1 sender).
5. **Sweep** — scheduled workflow to expire stale rows.
6. **Prompt section** + offline tests + **canary pass** + careful live merge (post-launch).

## Inputs needed from the team (before it can go live)

1. **Shared-use booth set** and each booth's **holder/approver** (M2→Peemo, M6→Nicole, M7→BD —
   confirm), and whether **M2/M6 are active**.
2. The approver **Slack IDs**.
3. Create **`#m-booth-approvals`** and invite Jessie; give the channel id (replaces the
   `APPROVALS_CHANNEL` placeholder).
4. How **"held"** is detected — a standing calendar event on the booth (+ its title keywords) vs a
   static map.
5. The **window / timeout rules** (replaces the placeholders in `computeDeadline`) and the
   **no-response policy** (expire silently vs notify).
6. **Approval rule** — booth owner approves their own booth (proposed) vs any-of-N.

## Status

Scaffolded and tested offline (router, consent gate, deadline math). Not wired to any workflow, not
deployed. The remaining build is inputs-first and lands on **canary**, merging to live **after
launch** so it adds no risk to the production path during launch week.
