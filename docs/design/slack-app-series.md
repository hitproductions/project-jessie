# Slack app — slice 1: series (Repeats) in the form

Series moved into slice 1 on 14 Oct (Localization books dubbing in batches; mixing, post, M booths and meetings recur too),
and to be built right after step C (15 Oct). **Slack Interactions v13** adds it to the booking form; the back end is the
live **Book Series v8** unchanged (prepare every date, then book exactly the prepared series). Typed series requests
("book studio 7 every monday") still go to the chat's series card until the next main build leads them here.

## What it does

- **Step 1** has a small **Repeats** box on every booking. Ticking it adds:
  - *How often* - every week / every weekday (Mon–Fri) / every day;
  - *On* - the days, for every week (the first date's day is ticked);
  - *How many times* (2–16), or *Or until* an end date.
  Unticking removes them; entries are kept either way. Up to 16 dates; a pattern that gives one date or more than 16
  says so next to the field.
- **Find rooms** checks every date. Step 2 shows "🗓️ 6 dates · 2:00 PM–4:00 PM · Localization Dubbing", the dates, and
  each room with how many dates it is free ("free on all 6 dates", "free on 5 of 6 dates"), those free on more dates
  first. The button says **Check 6 dates**.
- **Check** runs every date through the same checks as a single booking (client, department, the arranger…), nothing
  booked yet. A date whose room is taken gets another usual room or time that day when one is free, or is left out. A
  question comes back on the form, as for a single booking.
- The **check screen** lists the dates, any date moved and why, and any left out, with **Book N dates**.
- **Book N dates** books exactly that series (read back and checked - a changed or someone else's series books
  nothing). About half a minute a date; the form says so and can be closed. The result - "✅ Booked 5 of 6 dates" with the
  dates, time and room, and what was not booked - comes to the form and the DM. Each date can be changed or cancelled
  from **My bookings**.

Not yet: changing or cancelling a whole series at once (after release); per-date tweaks before booking beyond what the
check does itself.

## Import - Slack Interactions only (select all and delete before importing)

**Slack Interactions v13** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v13.json`
(should MATCH v12) → clear → Import `workflows/slack-interactions-v13.json` → Save → Publish "v13 - series" → download
into `workflows/imported/slack-interactions-v13-imported.json`.

## Test (2027 dates)

1. `hi` → **Book a room** → a date, 2–4 PM, a session type → tick **Repeats** → every week, 3 times → **Find rooms**.
   Step 2: 3 dates, rooms with "free on …" → pick one, fill the details → **Check 3 dates** → the check screen.
2. **Book 3 dates** → "Booking 3 dates…" → Booked (form and DM). Check the calendar: three events.
3. Repeats with a date or time where the room is taken on one week → the check screen says that week moved or is left out.
4. Repeats, every day, until a date three weeks away → "more than 16 dates".
5. Clean up: cancel the dates from **My bookings**.

Offline: `node scripts/sim-series-form.js` 41 (the Repeats box, the dates and every refusal, Room Availability per date,
"free on k of N", Book Series' own Expand Dates on the form's inputs - prepare and book, the stored series checked, the
result); sim-step-c1 45, sim-step-c2 59, sim-typed-to-form 70, sim-slice1-a 57, sim-slice1-b 34, hello 20 on v13.

## Typed series → the form (main v268 + Slack Interactions v14)

A typed repeating booking no longer goes to the chat's series card and its typed yes - the last typed confirmation.
- **main v268:** the booking reply reads the pattern too: "book studio 7 every monday 2-4pm for 4 weeks" →
  "🗓️ Studio 7 · from Monday, October 18 · 2:00 PM – 4:00 PM / 🔁 Every Monday · 4 times". It reads every week (the days -
  "every tuesday and thursday", "mondays"), every weekday ("weekdays", "mon-fri"), every day ("daily"), how many times
  ("for 4 weeks", "6 times", "3 sessions", up to 16) or an end ("until nov 30"), and the first date (the next of those
  days when none is named; a day after "until" is the end).
- **Slack Interactions v14:** **Book a room** opens step 1 with Repeats ticked and filled in; the rest is the series form above.

### Import (Slack Interactions first, then main) - select all and delete before each import

1. **Slack Interactions v14** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v14.json`
   (should MATCH v13) → clear → Import `workflows/slack-interactions-v14.json` → Save → Publish "v14 - typed series" →
   download into `workflows/imported/slack-interactions-v14-imported.json`.
2. **main v268** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v268.json` (should
   MATCH v267) → clear → Import `workflows/project-jessie-v268.json` → Save → Publish "v268 - typed series to form" →
   download into `workflows/imported/project-jessie-v268-imported.json`.

### Test

1. `book studio 7 every monday 2-4pm for 3 weeks` → the reply with 🔁 Every Monday · 3 times → **Book a room** → step 1
   with Repeats filled in → Find rooms → Check 3 dates → Book 3 dates.
2. `book likha every tuesday and thursday 10-11am, 4 times` → Every Tuesday and Thursday · 4 times (Meeting).
3. `book a dubbing session every weekday until <a date two weeks out>` → Every weekday · until …
4. Clean up from **My bookings**.

Offline: `node scripts/sim-typed-series.js` 17; sim-series-form 41, sim-typed-to-form 70, sim-step-c2 59, sim-step-c1 45,
sim-slice1-a 57, sim-slice1-b 34, hello 20; main v268 test-nodes 657, gate 69/69, check-fromai + audit clean.
