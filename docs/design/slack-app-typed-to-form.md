# Slack app — slice 1: a typed booking request leads to the form

Decided 14 Oct after the step B test: a typed request ("book studio 7 tomorrow 2-4pm") still went the chat way - free-text
questions and a chat card - and with a taken studio that is the risky part. Now code answers it and the form does the rest.

- **main v263 (typed booking to form):** a typed booking request gets a reply written by code - what it read (room, date,
  time, session type, project, client, engineer, arranger) - and a **Book a room** button. No chat card, no yes/no.
  Typing more after it ("make it 3-5pm", "client is Jem Lim") gets a new reply with that added; a new "book …" starts over.
  Still answered in the chat, unchanged: questions ("is studio 7 free friday?", "what do I have tomorrow?"), cancel and
  move (until step C), a series (until the form has Repeats), a yes or no to a chat card already shown, and anything after
  the reply that adds nothing new.
- **Slack Interactions v9 (form from typed request):** the button opens step 1 with the date, times and session type
  chosen (a time like 2:15 is added to the list). Find rooms → step 2 has the room asked for chosen when it is free; when
  it is taken, the form says *"Studio 7 is taken then. These are free:"* and offers only free rooms. A free room that is
  not a usual one for the session is offered as "not a usual room" (booked as asked). Project, client, project code,
  engineer and arranger are filled in. The menu's Book a room opens an empty form, as before.

## Import (Slack Interactions first, then main)

1. **Slack Interactions v9** - open `PyxSPoAMtSE1gzaH`, download into
   `workflows/imported/slack-interactions-live-before-v9.json` (should MATCH v8), **select all and delete**, Import
   `workflows/slack-interactions-v9.json` → Save → Publish "v9 - form from typed request" → download into
   `workflows/imported/slack-interactions-v9-imported.json`.
2. **main v263** - open `uVVYVB2M7kxpLleI`, download into `workflows/imported/project-jessie-live-before-v263.json`
   (should MATCH v262), **select all and delete**, Import `workflows/project-jessie-v263.json` → Save → Publish "v263 -
   typed booking to form" → download into `workflows/imported/project-jessie-v263-imported.json`.

(Select all and delete before importing - otherwise the import lands beside the old nodes and the old version keeps
running: gotcha 40.)

## Test (2027 dates)

1. `book studio 7 tomorrow 2-4pm VO recording for ORANGE, client Jem Lim` → the reply lists what was read, with the
   button; no card. Press **Book a room** → step 1 filled in → **Find rooms** → Studio 7 chosen, ORANGE and Jem Lim
   filled in → **Book** → Booked.
2. `make it 3-5pm` right after a reply → a new reply with 3:00 PM – 5:00 PM.
3. A taken room: ask for a studio at a time it is booked → in step 2, "… is taken then. These are free:".
4. `book M4 tomorrow 10-12` → M booth chosen; `book likha friday 3-4pm` → Meeting chosen.
5. Still the chat: `is studio 8 free friday?`, `what do I have tomorrow?`, `cancel <a test booking>`.
6. `hi` → the menu; its Book a room → an empty form.
7. Clean up the test bookings in the chat.

Offline: `node scripts/sim-typed-to-form.js` 48 ok; `node scripts/sim-slice1-a.js workflows/project-jessie-v263.json
workflows/slack-interactions-v9.json` 57; `node scripts/sim-slice1-b.js workflows/slack-interactions-v9.json` 33; hello
20; main v263: test-nodes 657, gate 69/69, check-fromai + audit-model-text clean.

## Fixes from the Slack test (15 Oct 01:30-01:40): main v264 + Slack Interactions v10

- **main v264 (offer wording + project):** the reply reads "Project: ORANGE · Client: Jem Lim · Engineer: Howard Luistro";
  "for ORANGE" is read as the project when the client is named separately or the word is in capitals (never a colleague,
  a room, a session type or a date word). The 01:30 message showed no project.
- **Slack Interactions v10 (form polish):** only the top room has a note ("Recommended · usual for VO Recording");
  "Booking Studio 7…" says only "This takes a few seconds."; no "A copy is in your DM" on the Booked screen; a blank line
  after "✅ Booked." (form and DM); Notes behind a small **Add a note** checkbox - ticking it adds the field, entries kept.

### Import (Slack Interactions first, then main) - select all and delete before each import

1. **Slack Interactions v10** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v10.json`
   (should MATCH v9) → clear → Import `workflows/slack-interactions-v10.json` → Save → Publish "v10 - form polish" →
   download into `workflows/imported/slack-interactions-v10-imported.json`.
2. **main v264** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v264.json` (should
   MATCH v263) → clear → Import `workflows/project-jessie-v264.json` → Save → Publish "v264 - offer wording + project" →
   download into `workflows/imported/project-jessie-v264-imported.json`.

### Test

1. `book studio 7 tomorrow 2-4pm VO recording for ORANGE, client Jem Lim` → "Project: ORANGE · Client: Jem Lim · …".
2. Book a room → Find rooms → only the top room has a note; tick **Add a note** → the field appears, entries kept; untick → it goes.
3. Book → "This takes a few seconds." → Booked with a blank line after "✅ Booked." and no DM line; the DM the same.
4. A not-usual room picked from the list (when no usual room is free) books without a "not a usual room" question.

Offline: `node scripts/sim-typed-to-form.js` 68; `sim-slice1-a` 57; `sim-slice1-b` 34; hello 20; main v264 test-nodes
657, gate 69/69, check-fromai + audit clean.
