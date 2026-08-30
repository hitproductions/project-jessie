# What moved from the prompt into the workflow

Every rule Jessie follows used to be a sentence in a 35,000-character system
prompt. A night of testing showed that every one of them failed at least once —
the conflict check, waiting for confirmation, the room ranking, checking
availability before summarising, even the rule against `**`.

So the build was reorganised around one principle:

> **Anything that must be true is enforced in a sub-workflow.
> Anything the prompt merely asks for is unreliable.**

Rules moved into n8n have held on every run since. This is what moved, what it
used to depend on, and what refuses now.

## The table

| Rule | Decision moved | Before — the prompt asked | After — n8n enforces |
|---|---|---|---|
| **Double-booking** | model → **code** | "check the room is free before you book" | `Check Conflicts` in `Book Session`; check and create are one call that cannot be skipped or reordered → `ROOM_OCCUPIED` |
| **Approval before booking** | model → **code** | "wait for confirmation" | `Gate Context` computes `confirmed` from Slack history; the model supplies no part of it → `NOT_CONFIRMED` |
| **What counts as approval** | model → **code** | the model judged the reply | literal y/n match on the whole message. "no" used to pass |
| **Cancelling someone else's** | model → **code** | compared a `ref:` inside a description the model had retyped | the event is fetched from Google and the marker read off the real record → `NOT_YOURS`, `NO_REFERENCE` |
| **Which booking gets cancelled** | model → **code** | the model supplied an event id | resolved from title + date against that day's calendar → `NOT_ON_CALENDAR`, `AMBIGUOUS_TITLE` |
| **Room suitability and ranking** | model → **code** | the prompt listed which rooms run which sessions | the Airtable ranking is injected per session type → `ROOM_UNSUITABLE`, `ROOM_NOT_PRIORITY`, `UNKNOWN_ROOM`, `NO_ROOM` |
| **Session duration** | model → **code** | the prompt stated min/max | read from Session Types → `DURATION_OUT_OF_RANGE` |
| **What is free** | model → **code** | the model reasoned over raw event lists | `Room Availability` computes it — also 2.74s → 0.55s |
| **Dates in the past** | model → **code** | the model was expected to notice | parsed out of the message at intake → `PAST_DATE` |
| **Room and session-type facts** | prompt text → **injected data** | written into the prompt, and several were wrong | read from Airtable on every message → `NO_REFERENCE_DATA` if missing |
| **Booked by** | model → **code** | the model wrote it | composed from the Slack sender. It was empty on every booking made before this |
| **That the event exists** | model → **code** | the model reported success | `Verify` re-reads the created event → `CREATE_FAILED`, `MISMATCH` |
| **Slack bold** | model → **code** | the prompt forbade `**` | `Guard Probe` collapses it on the way out |
| **The calendar title** | **still model** | — | a wrong title becomes a wrong calendar entry, silently |
| **Client, session type, engineer** | **still model** | — | extracted from what was typed; the summary is the only check before it is real |
| **Duration and room overrides** | **still model** | — | `duration_override` and `room_override` are model-supplied, so those three guards are overridable by design |
| **Whether it calls the tool at all** | **still model** | — | no guard catches this; a guard only runs once something calls it |

## Reading the table

The **model → code** rows are settled. They are enforced in
`Jessie — Book Session`, `Jessie — Cancel Booking` and `Jessie — Room
Availability`, and a refusal comes back as a `reason` code with a plain-English
`human` line that Jessie relays. A rule in this group cannot be talked out of by
a cleverly worded request, because the model is not the one deciding.

The **still model** rows are the honest edge of the build. Three of them are
judgement calls that arguably belong with the model. The fourth is not:

**Whether it calls the tool at all.** On 2026-08-30 two cancellations failed
this way. The gate had computed that the requester approved, a notice saying so
reached the model at the top of its prompt, and it answered by re-presenting the
same summary instead of acting. Once it was an invented event id, once it
searched and then stopped. Both were fixed at the level they occurred, but the
class remains: guards catch a wrong action, not a missing one.

The durable fix is to take the model out of the approved path entirely —
`Gate Context` already knows a cancellation was approved and holds the summary
text, so the workflow can resolve and cancel on its own without asking. That is
a restructure of the main chain and has not been done.

## Where to look

| Workflow | id | Holds |
|---|---|---|
| `Project Jessie` | `uVVYVB2M7kxpLleI` | `Gate Context` — approval, past dates, memory epoch |
| `Jessie — Book Session` | `EUG3sGXkfsJSYIMz` | every booking guard, and the only path that creates an event |
| `Jessie — Cancel Booking` | `bAyDw7udhmY0NL38` | ownership, booking resolution, and the only path that deletes one |
| `Jessie — Room Availability` | `e7tBQB458nstrqei` | availability, computed rather than reasoned |

Guard names are greppable: `grep -o "reason:'[A-Z_]*'" workflows/*.json`.
