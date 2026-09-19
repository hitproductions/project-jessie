# Design — Booking event log (Google Sheet)

Status: **LIVE (BOOKED + CANCELLED verified end to end)** · 2026-09-19
Draft logic + tests: `workflows/drafts/logging/`. Deployed in book-session-v32, cancel-booking-v10,
move-booking-v9.

## Live result (2026-09-19)

Validated the Google Sheets node config on a throwaway first (typeVersion 4.5, `serviceAccount`
auth, `documentId` by id, `sheetName` `gid=0`/`Log`, `autoMapInputData`), then wired it in. A live
booking wrote a `BOOKED` row and a live cancel wrote a `CANCELLED` row — both `Log to Sheet` nodes
`success`, and the return payloads were unchanged (`Return Booked` re-emits `Verify`; Cancel/Move log
before the notify chain). MOVED uses the identical node + the offline-tested `MOVE` row-builder.

**Note on timing:** `Log to Sheet` takes ~2.4–2.8 s (a real Sheets API round-trip), so `./scripts/
health` will flag it as a >1 s node on booking/cancel/move turns — expected, and it's best-effort
(`onError` continue), so it can never block or fail the mutation.

Credential: `Google Sheets - Jessie Log` (`googleApi` id `DU75rLW4KHlVhcK1`), a service account
(`jessie-booking-log@jessie-logging.iam.gserviceaccount.com`) with the Sheet shared to it — no human
Google account involved. Sheet id `1vIQ_cf2jJJ_WKpwFfnZQjQeKg2cxQz4tXGS6RZTEMwo`, tab `Log`.

## Goal

A durable, filterable record of every calendar mutation Jessie makes — **create, cancel, relocate,
update, series** — outside Slack, so it survives outages and serves as the audit trail the
one-account n8n setup can't provide.

## Where the row is written

At the **mutation point inside each sub-workflow**, deterministically (never model-driven), the same
place the notifications fire — a Google Sheets **append** node, **best-effort** (`onError` continue,
and off the return path) so a logging hiccup can never block or fail a booking.

| Sub-workflow | Node it follows | Action |
|---|---|---|
| Book Session | after `Create Event` | `BOOKED` |
| Cancel Booking | after `Delete Event` | `CANCELLED` |
| Move Booking | after `Delete Original` (move complete) | `MOVED` (Note: `old room → new room`) |
| Book Series | per created occurrence (or one summary row) | `SERIES` |

Each fills a context object and calls the shared `buildLogRow(ctx)` (`workflows/drafts/logging/
logrow.js`, 8 offline checks) so columns + formatting are identical everywhere.

## Columns

`Timestamp (Manila) · Action · Title · Room(s) · Date · Time · Department · Booker · Done by ·
Event ID · Note`

- **Timestamp** is Manila, `YYYY-MM-DD HH:MM`, sortable.
- **Done by** is the actor; defaults to the Booker on a self-action, and is the coordinator on an
  authorized change — so the sheet shows *who* moved/cancelled someone else's booking.
- **Note** carries the relocation (`Studio F → Studio 7`) or series size (`×4`).

## Setup needed (manual — I can't create Google credentials)

1. Create a Google Sheet (e.g. "Jessie Booking Log") with a tab (e.g. `Log`) and a header row of the
   columns above, in that order.
2. In n8n → Credentials → add **Google Sheets OAuth2** (sign in once) — this is a different scope
   from the Calendar credential, so it's a new one.
3. Give me the **Sheet URL/id**, the **tab name**, and the **credential name/id**.

Then wiring the four append nodes + deploying + a live check is mechanical.

## Notes

- Read-only for humans; Jessie only appends. Never store anything sensitive beyond what's already on
  the calendar event.
- A one-line Slack mirror can be added later if real-time visibility is wanted; the Sheet stays the
  system of record.
