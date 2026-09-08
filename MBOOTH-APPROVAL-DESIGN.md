# M-Booth Shared-Use Approval — Design

Status: **design, not built.** Architecture chosen (Howard, 8 Sept): event-driven with an
Airtable pending store — no n8n Wait nodes, nothing parked in memory, restart-safe.

This is the deterministic (node) layer. The system-prompt section Tel drafted is its
conversational companion; the guarantees live here in the nodes, not in the prompt.
Both must agree on one rule set — authored from the rules below, not from each other.

## The problem this solves

Some M-Booths carry a standing hold for an owner/department. Someone else wanting that
booth needs the owner's OK first. Tel's windows make approval **asynchronous** (1–24 h),
but Jessie's turns are synchronous (~9 s) — so a shared-use booking cannot complete in
one turn. It must be: *request → pending → approver responds (or window expires) →
finalize or reject*, across separate executions.

## Rules (from Tel's handoff + Slack message)

**Shared-use booths and their owner/approver** — *NEEDS CONFIRMING*:

| Booth | Hold keyword (handoff) | Proposed approver | Note |
|---|---|---|---|
| M2 | "peemo" | Peemo Morato | Currently **inactive** in Airtable — in scope? |
| M6 | "nicole" | Nicole Miller | Currently **inactive** in Airtable — in scope? |
| M7 | "bd" / "business development" | Ana Cadelina (Ana/Kristine) | Active |

**Approval windows** — deadline computed from request-to-booking lead time:
- booking date is **today** → deadline = now + **1 h**
- booking date is **tomorrow** (day before) → deadline = **10:00 on the booking day**
- booking date is **2+ days out** → deadline = now + **24 h**

**Approval rule** — *NEEDS CONFIRMING.* Proposed default: the **booth's owner is the sole
approver** for their booth (matches the keyword→owner mapping). "3 approvers" = the union
across the 3 booths, not all-three-must-approve. Alternatives: any-of-three, or
all-three.

## Architecture — two workflows + a sweep

Reuses existing infrastructure: Airtable, Slack send + Slack Trigger, `Book Session`,
`Room Availability`, and the proven yes/no confirmation-gate pattern (PENDING #9 — the
gate already strips the connector suffix and reads yes/no). Genuinely new: the pending
table, the deadline math, the approval-side routing, and the scheduled sweep.

### Airtable table — `M-Booth Approvals`

| Field | Purpose |
|---|---|
| Request ID | correlation key |
| Booth | M2 / M6 / M7 |
| Requester | name + Slack ID |
| Booking date | the requested date |
| Start / End / All-Day | the requested window |
| Approver | name + Slack ID (from booth→owner map) |
| Status | PENDING / APPROVED / REJECTED / EXPIRED |
| Created at / Deadline | window math |
| Approval channel + message ts | correlate the approver's reply |
| Calendar event id | filled once booked |

### Workflow A — request side (new `Request M-Booth` tool the agent calls)

1. Detect the requested booth is in the shared-use set (M2/M6/M7). If not, fall through
   to the normal M-Booth flow — no approval.
2. Check availability now (`Room Availability`) so an already-taken slot is refused up
   front, before pinging anyone.
3. Compute the deadline from the window rules above.
4. Write a **PENDING** row to `M-Booth Approvals`. **Do not create the calendar event
   yet** — booking only on approval keeps Rule 1 clean and avoids falsely blocking the
   slot; availability is re-checked at finalize.
5. Post to the approval channel, addressed to the booth's approver, with the request
   detail and a clear "reply *yes* or *no*." Store the message ts on the row.
6. Return to Jessie: *"Sent to [approver] for approval — you'll hear back by
   [deadline]."* The turn ends here. No waiting.

### Workflow B — approval side (Slack Trigger on the approval channel)

1. Fires on a reply in the approval thread. Match it to its PENDING row by message ts.
2. Parse yes/no (reuse the gate's suffix-strip + yes/no logic).
3. **YES**, still PENDING and within deadline:
   - Re-check availability (the slot may have gone since).
   - Call `Book Session` to create the event. Write the event id back to the row.
   - Status → APPROVED. Notify requester ("approved and booked") and confirm to approver.
4. **NO** → status REJECTED, notify requester.
5. Already resolved or past deadline → reply "this request has already closed/expired,"
   take no booking action.

### Sweep — Schedule Trigger (every ~10 min)

1. Find PENDING rows where deadline < now.
2. Status → EXPIRED, notify requester ("no response by [deadline] — not booked; rebook or
   follow up"). Optionally nudge the approver once before expiry.

## Recommended defaults (override on review)

- Book only on approval, re-checking availability at finalize — no tentative calendar hold.
- Booth owner is the sole approver for their booth.
- Approver pings go to a **dedicated Slack channel** (e.g. `#m-booth-approvals`) as
  threads — far more reliable to correlate a reply than a DM.
- Sweep every 10 minutes.

## Inputs still needed before build

1. **3 approver Slack member IDs** — Peemo Morato, Nicole Miller, Ana Cadelina (confirm
   Ana vs "Kristine" — same person?).
2. **Approval rule** — owner-approves (proposed) / any-of-three / all-three.
3. **Shared-use booth set + hold keywords confirmed against the actual calendar hold
   titles** (M2→peemo, M6→nicole, M7→bd/business development).
4. **M2 / M6 inactive** — in scope now, or hold until reactivated?
5. **Approval channel** — create `#m-booth-approvals`, or use DMs / an existing channel?
6. Whether Tel wants to author the companion prompt section, or we draft it from these
   rules and she reviews.

## Build / rollout

- Build on **canary**, never straight into the recovered production workflow.
- Verify end-to-end on canary (approve, reject, expire, slot-taken-since-request).
- Merge to live only with explicit sign-off, then `./scripts/webhook-canary` +
  `./scripts/baseline --diff` to confirm no drift.
