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

**Every one of these has now refused something in a live conversation**, not only
in a unit test. `ROOM_OCCUPIED` stopped a booking into an occupied room after the
model had already presented it as free. `NO_REFERENCE` refused to cancel a
booking made before this build existed. `NOT_ON_CALENDAR` and `AMBIGUOUS_TITLE`
both fired during the 2026-08-30 QA run.

`NOT_YOURS` was the last one outstanding and was proved on 2026-08-30, using a
seeded calendar event carrying a foreign `ref:` rather than by aiming the bot at
a real third-party booking — so nothing anyone owned was ever at risk. It held
through two escalations: a claim of authority over the other person's bookings,
then a claim that the session was really the requester's. It refused both times
and the event was untouched afterwards.

The gap that used to remain — a reply describing a booking no guard was ever asked
about — is closed too, by the first row of the table. What is left is narrower: the
model still composes titles, clients and engineers from what was typed, and the
summary is the only check before those become real.

## The table

| Rule | Decision moved | Before — the prompt asked | After — n8n enforces |
|---|---|---|---|
| **Double-booking** | model → **code** | "check the room is free before you book" | `Check Conflicts` in `Book Session`; check and create are one call that cannot be skipped or reordered → `ROOM_OCCUPIED` |
| **Approval before booking** | model → **code** | "wait for confirmation" | `Gate Context` computes `confirmed` from Slack history; the model supplies no part of it → `NOT_CONFIRMED` |
| **What counts as approval** | model → **code** | the model judged the reply | a literal match on the whole message against a fixed yes/no set. "no" used to pass |
| **Cancelling someone else's** | model → **code** | compared a `ref:` inside a description the model had retyped | the event is fetched from Google and the marker read off the real record → `NOT_YOURS`, `NO_REFERENCE` |
| **Which booking gets cancelled** | model → **code** | the model supplied an event id | resolved from title + date against that day's calendar → `NOT_ON_CALENDAR`, `AMBIGUOUS_TITLE` |
| **Who booked a session** | model → **code** | the raw Google event went to the model, and it read `creator` — always the n8n service account | `Find Booking` shapes the day's events to id, title, time, room, booked-by and engineer. `creator` never reaches her. She told a requester their own booking "was made by someone else, not you" |
| **The confirmation marker** | model → **code** | the model wrote the marker line and the gate matched it exactly | `Guard Probe` normalises it on the way out. "Confirm to cancel both." broke the gate and refused a cancellation |
| **The weekday beside a date** | model → **code** | written by the model from the date | recomputed from the date in `Guard Probe`. It printed the wrong day three times, twice in a booking summary |
| **Internal vocabulary** | model → **code** | a prompt rule forbade "priority room" and "last resort" | rewritten on the way out. The prompt rule was ignored in five replies |
| **Conference rooms** | prompt text → **injected data** | a rule paragraphs away from the room list said never to choose one | the list itself now marks them: "conference rooms, ask which before booking" |
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
| **Invisible characters in a timestamp** | model → **code** | nothing — the ISO string was parsed as sent | every string the model hands a sub-workflow is scrubbed of format and control characters first. A variation selector (U+FE0F) glued to an ISO time made `Room Availability` answer `BAD_WINDOW`, and the model summarised anyway as if the room were free |
| **A title the model mistyped** | model → **code** | an exact or substring match, or nothing | one slipped character now still resolves, but only when a single booking that day is strictly closest — and the ownership check still runs on whatever it finds. `REASON1` came back `REazon1` and a move died as `NOT_ON_CALENDAR` |
| **The booker's name in a summary** | model → **code** | the model retyped it | rewritten from `Get Booker` in `Guard Probe`. It rendered "Tara Lim" as "Tara Inf" in the line a requester reads before saying yes. The calendar entry was never at risk — its `Booked by` comes from a workflow input |
| **"deviation" and "BLOCKED"** | model → **code** | — | stripped and reworded on the way out. `deviation:` is the room ranking's internal vocabulary and `BLOCKED - ` is a prefix meant for the model, not a person |
| **A start time with no end** | model → **notice** | the model chose a length silently | `Gate Context` spots a lone time in the message and tells the model to ask, or to state the length it is assuming. "at 2pm" became a 2–5 PM summary with nothing said |
| **The reason a tool refused** | **still model**, now constrained | the model explained refusals in its own words | the prompt forbids inventing a cause. It told a requester two titles differed by "exact casing" when one letter had been substituted — the tool had only said nothing matched |
| **An offer the check contradicts** | model → **code** | the prompt asked her to check availability before summarising | a booking summary is refused when this turn's own availability call errored or named that room busy. She offered Studio C while another booking held it, after a check that had come back `BAD_WINDOW` |
| **A claim that a booking happened** | model → **code** | nothing checked it | the reply may only say "Booked", "Cancelled" or "Moved" if that tool appears in the agent's `intermediateSteps` this turn with a success status. She said "Booked" without calling `Book Session` once in 120 runs and nothing was on the calendar. The direct question — did the node run — hangs the task runner, so this reads the agent's own report of what it called |
| **A stated assumption about length** | notice → **code** | `Gate Context` asked her to say what she assumed | she did once and ignored it the next time. `Guard Probe` writes the line when the summary lacks it |
| **A note that contradicts the ranking** | model → **code** | — | dropped on the way out. "Studio 7 is outside the usual rooms for Post Mixing" went out about the room that is first in that ranking |
| **A weekday with no year beside it** | model → **code** | the two corrections both needed a four-digit year | the year is taken from the date `Gate Context` resolved. "next Wednesday, September 9" went out uncorrected for a Thursday |
| **A carried date on a catalogue question** | model → **code** | the date carried to every follow-up | dropped for a question about which rooms exist. "list all the rooms" inherited a 2–5pm window and answered with the free ones, presented as the whole list |
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
| `Jessie — Find Booking` | `yzirq12O227VTFp8` | shapes a day's events; the model never sees the raw payload |

Guard names are greppable: `grep -o "reason:'[A-Z_]*'" workflows/*.json`.

There is now a third place where rules live. **`Guard Probe`** rewrites the reply
on the way out, and is where anything that must be true of the *text* belongs —
the weekday, the vocabulary, the marker, the `**` collapse. Every one of those was
a prompt rule first, and every one failed as a prompt rule. Two of them were caught
correcting a real reply during testing rather than in a staged case.

`Gate Context` is the one node every message passes through, so a mistake there
takes Jessie down completely rather than degrading one feature — it has happened
twice. Run it offline against the scenarios before shipping any change to it:

```bash
./scripts/test-gate workflows/project-jessie-v91.json
```

**Before launch:** `YEAR_SHIFT` at the top of `Gate Context` and the
`plus({ years: 1 })` in the system prompt are the QA year shift. They must go to
zero together, or the model and the guards will disagree about what day it is.
