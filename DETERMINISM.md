# What moved from the prompt into the workflow

Every rule Jessie follows used to be a sentence in a 36,000-character system
prompt. A night of testing showed that every one of them failed at least once —
the conflict check, waiting for confirmation, the room ranking, checking
availability before summarising, even the rule against `**`.

So the build was reorganised around one principle:

> **Anything that must be true is enforced in a sub-workflow.
> Anything the prompt merely asks for is unreliable.**

Rules moved into n8n have held on every run since. This is what moved, what it
used to depend on, and what refuses now.

Two of these have now refused in a live conversation rather than only in a unit
test: `ROOM_OCCUPIED` stopped a booking into an occupied room after the model
had already presented it as free, and `NO_REFERENCE` refused to cancel a booking
made before this build existed. `NOT_YOURS` — refusing to cancel a booking that
belongs to someone else who made it through Jessie — is still unproven live,
because every booking so far was made by the same person.

## The table

| Rule | Decision moved | Before — the prompt asked | After — n8n enforces |
|---|---|---|---|
| **Double-booking** | model → **code** | "check the room is free before you book" | `Check Conflicts` in `Book Session`; check and create are one call that cannot be skipped or reordered → `ROOM_OCCUPIED` |
| **Approval before booking** | model → **code** | "wait for confirmation" | `Gate Context` computes `confirmed` from Slack history; the model supplies no part of it → `NOT_CONFIRMED` |
| **What counts as approval** | model → **code** | the model judged the reply | literal y/n match on the whole message. "no" used to pass |
| **Cancelling someone else's** | model → **code** | compared a `ref:` inside a description the model had retyped | the event is fetched from Google and the marker read off the real record → `NOT_YOURS`, `NO_REFERENCE` |
| **Which booking gets cancelled** | model → **code** | the model supplied an event id | resolved from title + date against that day's calendar → `NOT_ON_CALENDAR`, `AMBIGUOUS_TITLE` |
| **Rescheduling** | model → **code** | the prompt walked it through delete-then-recreate — and the gate could only approve one of those per turn, so a move deleted the booking and then asked for a second yes | `Move Booking` does the whole move in one call and one confirmation. It creates the replacement **first** and removes the original only once that succeeded, so a failure leaves the booking where it was → `ROOM_OCCUPIED`, `NOT_YOURS`, `PARTIAL` |
| **Relative dates and weekdays** | model → **code** | the model worked out "next Thursday" itself | `Gate Context` resolves next/this weekday, bare weekdays, tomorrow and today, states the weekday, and carries the date across follow-up turns that name no date |
| **The client's technical requirements** | model → **code** | read from whatever `Get Client` returned, with no check that a client had been asked for | an empty client returns nothing instead of every client, and a missing client is recovered from the title. This is what the room gets set up from |
| **Room suitability and ranking** | model → **code** | the prompt listed which rooms run which sessions | the Airtable ranking is injected per session type → `ROOM_UNSUITABLE`, `ROOM_NOT_PRIORITY`, `UNKNOWN_ROOM`, `NO_ROOM` |
| **Session duration** | **still model**, deliberately | the prompt called Min/Max an allowed range and the booking was refused outside it | Min/Max is what a session *usually* runs, not a limit. Book Session books the length asked for and returns a note when it is outside typical. Only an end time at or before the start is refused → `DURATION_INVALID` |
| **What is free** | model → **code** | the model reasoned over raw event lists | `Room Availability` computes it — also 2.74s → 0.55s |
| **Dates in the past** | model → **code** | the model was expected to notice | parsed out of the message at intake → `PAST_DATE` |
| **Room and session-type facts** | prompt text → **injected data** | written into the prompt, and several were wrong | read from Airtable on every message → `NO_REFERENCE_DATA` if missing |
| **Booked by** | model → **code** | the model wrote it | composed from the Slack sender. It was empty on every booking made before this |
| **That the event exists** | model → **code** | the model reported success | `Verify` re-reads the created event → `CREATE_FAILED`, `MISMATCH` |
| **Slack bold** | model → **code** | the prompt forbade `**` | `Guard Probe` collapses it on the way out |
| **The calendar title** | **still model** | — | a wrong title becomes a wrong calendar entry, silently |
| **Client, session type, engineer** | **still model** | — | extracted from what was typed; the summary is the only check before it is real |
| **Which rooms she offers** | **still model** | — | asked for alternatives beyond the ranked rooms she once offered a room `Book Session` refuses. A prompt rule now forbids it and `ROOM_UNSUITABLE` is the backstop |
| **Room overrides** | **still model** | — | `room_override` is model-supplied, so the two ranking guards are overridable by design. `duration_override` is gone — duration is no longer a wall to override |
| **Whether it calls the tool at all** | **still model** | — | no guard catches this; a guard only runs once something calls it |

## Reading the table

The **model → code** rows are settled. They are enforced in
`Jessie — Book Session`, `Jessie — Cancel Booking` and `Jessie — Room
Availability`, and a refusal comes back as a `reason` code with a plain-English
`human` line that Jessie relays. A rule in this group cannot be talked out of by
a cleverly worded request, because the model is not the one deciding.

The **still model** rows are the honest edge of the build. Some are judgement
calls that arguably belong with the model. Two are not.

**Whether it calls the tool at all.** A guard catches a wrong action, never a
missing one. On 2026-08-30 she presented a booking summary for a room that was
already taken, having called no availability tool at all that turn — the prompt
rule "check the room is free before you summarise" simply did not fire.
`ROOM_OCCUPIED` refused the create, so the requester got a correct answer and
nothing was double-booked, but the wasted turn came from a rule the prompt could
not enforce. The durable fix is to take the model out of the path entirely for
actions the gate has already approved, which is a restructure of the main chain
and has not been done.

**Free text that nothing binds to a source.** Three inventions were caught in one
evening's testing, and they share a mechanism worth naming, because it predicts
where the next one will appear:

- *A required value it does not hold.* Asked for an event id it never had, it
  produced one shaped exactly like the ids it had just seen. Fixed structurally —
  cancel and move resolve bookings by title, so there is no id to invent.
- *A value it retypes instead of copies.* It wrote "Jem H. Lim" where Airtable
  says "Jem Lim". The calendar title was correct, because that is assembled in
  code; only the sentence around it drifted.
- *A contradiction with no stated precedence.* It offered a booking as a choice
  in the same turn a search had shown it cancelled — memory and a live tool
  result disagreed and nothing said which wins.

The first kind is fixable by deleting the field. The other two are only
addressable by prompt rules, which is to say: mostly, not always. Anywhere the
model writes prose containing a name, a date or a state, treat it as the least
reliable thing on the screen — and check the calendar entry, which is assembled
in code, rather than the message describing it.

## Where to look

| Workflow | id | Holds |
|---|---|---|
| `Project Jessie` | `uVVYVB2M7kxpLleI` | `Gate Context` — approval, past dates, memory epoch |
| `Jessie — Book Session` | `EUG3sGXkfsJSYIMz` | every booking guard, and the only path that creates an event |
| `Jessie — Cancel Booking` | `bAyDw7udhmY0NL38` | ownership, booking resolution, and the only path that deletes one |
| `Jessie — Room Availability` | `e7tBQB458nstrqei` | availability, computed rather than reasoned |
| `Jessie — Move Booking` | `t7lwR2km4tfN8DbM` | the only path that reschedules; creates before it deletes |

Guard names are greppable: `grep -o "reason:'[A-Z_]*'" workflows/*.json`.

`Gate Context` is the one node every message passes through, so a mistake there
takes Jessie down completely rather than degrading one feature — it has happened
twice. Run it offline against the scenarios before shipping any change to it:

```bash
./scripts/test-gate workflows/project-jessie-v91.json
```

**Before launch:** `YEAR_SHIFT` at the top of `Gate Context` and the
`plus({ years: 1 })` in the system prompt are the QA year shift. They must go to
zero together, or the model and the guards will disagree about what day it is.
