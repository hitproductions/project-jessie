# Slack app — slice 1, step C: My bookings, Change, Cancel

Step C comes in two builds. **C1 (this one)** adds the buttons and forms: every booking a message shows - the Booked DM
and My bookings - gets **Change** and **Cancel**. **C2 (next)**: typed "cancel …" / "make it 3pm" lead to those buttons,
and the chat's yes/no cards for cancel and move come out (no confirmation is ever typed - decided 15 Oct). Series
(Repeats in the form) follows step C.

- **Cancel Booking v27 / Move Booking v30 (team may cancel / change):** the booker, and the session's engineer and
  arranger (their Slack ids are on form bookings as "team:"), may cancel or change it. When the engineer or arranger does
  it, the booker is told; nobody is told about their own change.
- **Slack Interactions v11 (my bookings, change, cancel):**
  - **Cancel** asks first with Slack's own pop-up - *Cancel this booking?* with the booking, **Cancel booking** (red) /
    **Keep it**. Then the message updates in place: "❌ Cancelled: …" and the buttons go; if it can't be cancelled, why
    shows under the booking.
  - **Change** opens a form at the booking's current date, start, end and room (rooms of the same kind - studios, M booths
    or conference rooms - the current one first). Change with nothing changed: "Nothing changed - pick a new date, time or
    room." on the form, nothing moved. Otherwise "Changing…", then **Changed** (the card) - or the problem on the form,
    entries kept (a taken room says its free times that day). The message's row updates to the new time.
  - **My bookings** (from the menu): the next 7 days - bookings you made, and ones you engineer or arrange ("You're
    engineering") - each with Change / Cancel; **← Previous 7 days / Next 7 days →** update the same message.

Not yet: typed cancel / change (C2), moving or cancelling a whole series, a booking's room kind outside its own group.

## Import (Cancel and Move first, then Slack Interactions) - select all and delete before each import

1. **Cancel Booking v27** into `bAyDw7udhmY0NL38`: download into `workflows/imported/cancel-booking-live-before-v27.json`
   (should MATCH v26) → clear → Import `workflows/cancel-booking-v27.json` → Save → Publish "v27 - team may cancel" →
   download into `workflows/imported/cancel-booking-v27-imported.json`.
2. **Move Booking v30** into `t7lwR2km4tfN8DbM`: download into `workflows/imported/move-booking-live-before-v30.json`
   (should MATCH v29) → clear → Import `workflows/move-booking-v30.json` → Save → Publish "v30 - team may change" →
   download into `workflows/imported/move-booking-v30-imported.json`.
3. **Slack Interactions v11** into `PyxSPoAMtSE1gzaH`: download into
   `workflows/imported/slack-interactions-live-before-v11.json` (should MATCH v10) → clear → Import
   `workflows/slack-interactions-v11.json` → Save → Publish "v11 - my bookings, change, cancel" → download into
   `workflows/imported/slack-interactions-v11-imported.json`.

## Test (2027 dates)

1. Book something through the form → the Booked DM has **Change** and **Cancel**.
2. **Change** → the form at its current values → press Change without changing anything → "Nothing changed". Change the
   end time → Change → "Changing…" → Changed; the DM's booking now shows the new time (and its buttons still work).
3. Change it into a time when that room is taken → the problem with the room's free times, entries kept.
4. `hi` → **My bookings** → the week, with Change / Cancel on each; **Next 7 days →** / **← Previous 7 days** update it.
5. **Cancel** → the pop-up → **Keep it** (nothing happens) → Cancel again → **Cancel booking** → "❌ Cancelled: …"; check
   the calendar.
6. Optional: book one with someone else as engineer and have them press Cancel / Change on it from their My bookings.

Offline: `node scripts/sim-step-c1.js` 45 (routes, the DM buttons, My bookings, Cancel, the Change form, Move's inputs,
the row update, the team rule in Cancel / Move); sim-slice1-a 57, sim-slice1-b 34, sim-typed-to-form 68, hello 20;
test-nodes 657 with Cancel v27 + Move v30.

## C2: typed cancel / change → the buttons; anything else → the menu (main v265 + Slack Interactions v12)

- **main v265 (typed cancel / change, menu otherwise):**
  - A typed cancel or change - "cancel ORANGE saturday", "cancel my 2pm on saturday", "make it 3-5pm", "move it to friday
    3pm", "move my studio 7 booking to studio 8", "change my booking" - is answered by code: the requester's bookings
    (made, or engineered / arranged), from today for 60 days, found by the words typed, the date, the time or the room -
    or, with nothing to go on, the booking in Jessie's newest message (so "make it 3-5pm" right after Booked is that
    booking). One: "Here it is - press Cancel / Change …" with *Now:* and *New:* for a change; several: "Which one?";
    none: "I couldn't find a booking of yours …" with **My bookings**. Each has Change / Cancel (Cancel asks first).
    No chat card, no typed yes.
  - **Anything that is not a booking, a question or an answer gets the menu** ("what's up", "test"; thanks → "Anytime!
    Anything else?"), unless Jessie is waiting for an answer (her newest message asks something, is a chat card, or is a
    booking-form reply). The agent answers questions and answers.
  - Still the agent's: questions, a yes / no to a chat card already shown, a series.
- **Slack Interactions v12 (change at the typed time):** the Change button from that reply opens the form at the new time
  (a start alone keeps the booking's length; a new date or room too). "Now:" and "Nothing changed" still use the booking
  as it is.

### Import (Slack Interactions first, then main) - select all and delete before each import

1. **Slack Interactions v12** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v12.json`
   (should MATCH v11) → clear → Import `workflows/slack-interactions-v12.json` → Save → Publish "v12 - change at the typed
   time" → download into `workflows/imported/slack-interactions-v12-imported.json`.
2. **main v265** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v265.json` (should
   MATCH v264) → clear → Import `workflows/project-jessie-v265.json` → Save → Publish "v265 - typed cancel / change, menu
   otherwise" → download into `workflows/imported/project-jessie-v265-imported.json`.

### Test (2027 dates)

1. Book something through the form, then type `make it 3-5pm` → the booking with Now / New and **Change** → Change opens
   at 3-5 PM → Change → Changed.
2. `cancel <its title> <its day>` → "Here it is" with **Cancel** → the pop-up → Cancelled.
3. `cancel nothinglikethis` → "I couldn't find a booking of yours called …" with **My bookings**.
4. `what's up`, `test`, `thanks` → the menu. `is studio 8 free friday?` → answered in the chat as before.

Offline: `node scripts/sim-step-c2.js` 49; sim-step-c1 45, sim-typed-to-form 68, sim-slice1-a 57, sim-slice1-b 34, hello
20; main v265 test-nodes 657, gate 69/69, check-fromai + audit clean.
