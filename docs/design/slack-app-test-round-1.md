# Slack app — notes from the first full Slack test (15 Oct afternoon)

Fifteen notes came out of testing slice 1 in Slack. They ship in two builds: **A** (wording, cards, buttons - low risk) and
**B** (behaviour: free stretches, engineer notices, changing details).

## Build A - main v269 + Slack Interactions v17

| # | Note | Where |
|---|---|---|
| 1 | Booking screen: "Your booking is being processed. This takes a few seconds." | Slack Interactions |
| 2 | Change form: the bottom note is gone | Slack Interactions |
| 4 | Typed change / cancel reply: "Here's your proposed change – press *Change* to check the new time." / "Here's the booking – press *Change* to pick the new time." / "Here's the booking – press *Cancel* to cancel it." | main |
| 5 | A cancel, or a change started from a message, shows "⏳ Your cancellation / change is being processed…" under that booking with its buttons hidden until done; a change that fails puts the row back | Slack Interactions |
| 6 | Cancelled and Changed are the card (like Booked); a reply about one booking loses its "Here's…" line once done (a list keeps its heading) | Slack Interactions |
| 7 | The menu's examples in quotes | main |
| 8 | "Or until": 'Only applies if "How many times" is empty.' | Slack Interactions |
| 9 | Series check screen: "Checking availability for each date. This takes a few seconds." | Slack Interactions |
| 10 | Series booking screen: "Processing your series of bookings. This may take a while, so you can close this window for now. You will be notified once finished." | Slack Interactions |
| 11 | The series result DM has Book a room / My bookings | Slack Interactions |
| 12 | My bookings beside Book a room on the booking reply | main |
| 13 | A typed series naming several days ("every tuesday and thursday") starts on the first of them after today, not on the one the date reader resolved | main |

### Import (Slack Interactions first, then main) - Cmd+A then **Delete** (not D) before each import

0. **Slack Interactions v16** first, if not yet re-imported: its 14:33 download had every node deactivated (gotcha 43).
   Download into `workflows/imported/slack-interactions-v16-imported.json` after a clean re-import, or skip straight to v17.
1. **Slack Interactions v17** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v17.json`
   → clear (Cmd+A, Delete) → Import `workflows/slack-interactions-v17.json` → Save → Publish "v17 - build A: wording, cards,
   buttons" → download into `workflows/imported/slack-interactions-v17-imported.json`.
2. **main v269** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v269.json` (should
   MATCH v268) → clear → Import `workflows/project-jessie-v269.json` → Save → Publish "v269 - build A: wording, buttons,
   series first day" → download into `workflows/imported/project-jessie-v269-imported.json`.

### Test (2027 dates)

1. `hi` - the examples in quotes. Book a room → Book → "Your booking is being processed…" → Booked.
2. My bookings → **Cancel** on one → **Cancel booking** → "⏳ Your cancellation is being processed…" under it → the
   ❌ Cancelled card.
3. `make it 3-5pm` after a booking → "Here's your proposed change…" → Change → the row shows "⏳ Your change is being
   processed…" → the message becomes just the ✅ Changed card. Change into a taken time → the row comes back with its
   buttons. No note at the bottom of the Change form.
4. `book studio 7 tomorrow` → Book a room **and My bookings** on the reply.
5. `book likha every tuesday and thursday 10-11am, 4 times` → from **Tuesday**, October 19.
6. A series in the form → "Checking availability for each date…" → Book N dates → "Processing your series of bookings…" →
   the DM with Book a room / My bookings. Or until's hint.

Offline: sim-step-c1 60, sim-series-form 49, sim-typed-series 21, sim-step-c2 59, sim-typed-to-form 70, sim-slice1-a 57,
sim-slice1-b 34, hello 20; main v269 test-nodes 657, gate 69/69, fromai + audit clean; no block repeats an action id.

## Build B - next (Move Booking v31, Cancel Booking v28, Slack Interactions v18)

| # | Note |
|---|---|
| 3 | Change form, room taken: list every free stretch that day ("Free that day: 8:00 – 10:00 AM, 12:00 – 10:00 PM"), not the two nearest slots - Move Booking v31 returns them |
| 14 | Tell the engineer / arranger when someone else books them, and when anyone else on the session changes or cancels it (the booker too) - never the person who did it. During QA the same redirect as Cancel / Move (to Howard unless on ALLOW); a new DEV_REDIRECT for the launch checklist |
| 15 | Change form: "Change other session details" - Project, Client, Engineer (+ Arranger / Project code / Meeting title); checked like a new booking, then the booking updated (Move Booking v31 takes a new title and details) |

## Build B - Move Booking v31 + Cancel Booking v28 + Slack Interactions v18 (built 15 Oct)

- **Change other session details** (note 15): a small checkbox on the Change form shows Project, Client, Engineer and
  Arranger (Project code for Localization, Meeting title for meetings), filled in from the booking. Change only them, or
  them and the time / room; "Nothing changed" counts them. A client not in the list: "Did you mean …?" (press Change again
  to keep the name). The booking is rebuilt with the new title, engineer, arranger and team; the booker, notes, type and
  department stay. A meeting moved to another room gets that room in its title.
- **Free stretches** (note 3): a taken room says every free stretch that day - "Studio 7 is taken then. Free that day:
  8:00 AM – 10:00 AM, 12:00 PM – 10:00 PM."
- **The engineer and arranger are told** (note 14): when someone else books them (single or series), adds them in a change,
  or changes or cancels a session they are on - never about their own change. During QA every notice goes to Howard
  unless the person is on the testing list (a new DEV_REDIRECT, now in the launch checklist).
- **Arrangers**: anyone whose Bookers Info says "Arranger" (Mike Villegas was missing).

### Import (Cancel, Move, then Slack Interactions) - Cmd+A then **Delete** before each import

1. **Cancel Booking v28** into `bAyDw7udhmY0NL38`: download into `workflows/imported/cancel-booking-live-before-v28.json`
   (should MATCH v27) → clear → Import `workflows/cancel-booking-v28.json` → Publish "v28 - everyone on it told" → download
   into `workflows/imported/cancel-booking-v28-imported.json`.
2. **Move Booking v31** into `t7lwR2km4tfN8DbM`: download into `workflows/imported/move-booking-live-before-v31.json`
   (should MATCH v30) → clear → Import `workflows/move-booking-v31.json` → Publish "v31 - free stretches, details, everyone
   told" → download into `workflows/imported/move-booking-v31-imported.json`.
3. **Slack Interactions v18** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v18.json`
   (should MATCH v17) → clear → Import `workflows/slack-interactions-v18.json` → Publish "v18 - build B: details, notices,
   free stretches" → download into `workflows/imported/slack-interactions-v18-imported.json`.

### Test (2027 dates)

1. Change on a booking → tick **Change other session details** → change only the engineer → Change → Changed, with the
   new initials in the title; the calendar event shows the new engineer. The new engineer's notice comes to you ("[DEV]
   would notify …").
2. Change the client to a near miss ("sasa abela") → "Did you mean Sasa Abella?" → fix it, or press Change again.
3. Change into a taken time → "Free that day: …" lists every free stretch.
4. Book with Tara (or another tester) as engineer → she gets "Howard Luistro booked you as the engineer".
5. Cancel a booking that has an engineer → the engineer's notice comes to you.
6. A music session → Mike Villegas is in the Arranger list.

Offline: sim-build-b 30 (Move v31's own code on the form's inputs: free stretches, the new title and details on the
replacement, who is told); sim-step-c1 60, sim-series-form 49, sim-step-c2 59, sim-typed-to-form 70, sim-typed-series 21,
sim-slice1-a 57, sim-slice1-b 34, hello 20; test-nodes 660 with Cancel v28 + Move v31; no repeated action ids.

## Round 2 - the notes from testing builds A and B (15 Oct): Slack Interactions v19 + main v270

| # | Note | Where |
|---|---|---|
| 1 | "You may close this window. You'll be notified when it's done." on Booking… and Changing… (the series screen reworded); a finished change also DMs the ✅ Changed card with its buttons | Slack Interactions |
| 2 | My bookings' example in quotes | Slack Interactions |
| 3 | The Changing… screen shows the proposed booking as the card | Slack Interactions |
| 4 | Clients: a capital first letter on every word ("john smithy" -> John Smithy; ACME stays) | both |
| 5 | A typed room that is free but on neither of the session type's lists is offered as "not a usual room" (Studio 2 for Music Mixing said "taken"); a "Use another room" box lists the other free rooms of the same kind | Slack Interactions |
| 6 | Closing the series "Booking N dates…" view closes the whole form | Slack Interactions |
| 7 | The message a booking started from shows "⏳ Your booking / series is being processed…" with its buttons hidden; then "✅ Booked." (a booking reply) or its buttons back (the menu, or a question on the form) | Slack Interactions |
| 8 | Room names from the calendar matched to the room list ("Likha (Big Room)" -> Likha); the Change form lists only rooms of the same kind (it listed studios for a meeting) | both |
| 9 | The engineer / arranger notice has the booking's Change / Cancel | Slack Interactions |

Parked: PENDING 118 - a series shown as a series in My bookings, with Cancel series.

### Import (Slack Interactions first, then main) - Cmd+A then **Delete** before each import

1. **Slack Interactions v19** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v19.json`
   (should MATCH v18) → clear → Import `workflows/slack-interactions-v19.json` → Publish "v19 - round 2" → download into
   `workflows/imported/slack-interactions-v19-imported.json`.
2. **main v270** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v270.json` (should
   MATCH v269) → clear → Import `workflows/project-jessie-v270.json` → Publish "v270 - round 2: client capitals, room names"
   → download into `workflows/imported/project-jessie-v270-imported.json`.

### Test (2027 dates)

1. `book studio 2 sat 10-2 music mixing, client john smithy` → the reply says "Client: John Smithy" → Book a room → step 2
   offers Studio 2 "not a usual room for Music Mixing", chosen → Book → the reply shows "⏳ Your booking is being
   processed…" with its buttons hidden, then "✅ Booked."; the Booking… screen has the close line.
2. In step 2, tick **Use another room** → the other free studios.
3. Change a booking → the Changing… screen shows the new card and the close line → a DM with the ✅ Changed card arrives.
4. Change a meeting (Likha) → the room list has only conference rooms.
5. A series through the menu → the menu shows "⏳ Your series is being processed…", then its buttons back; close the
   "Booking N dates…" view → the whole form closes.
6. Book with an engineer → their notice (to you) has **Change** / **Cancel** for that booking.
7. My bookings → the example in quotes.

Offline: `node scripts/sim-round-2.js` 38; sim-build-b 30, sim-step-c1 60, sim-series-form 49, sim-step-c2 59,
sim-typed-to-form 70, sim-typed-series 21, sim-slice1-a 57, sim-slice1-b 34, hello 20; main v270 test-nodes 660, gate
69/69, fromai + audit clean; no repeated action ids.

## Every message leads to the buttons - main v271 (15 Oct, from the 16:27 test)

"what can you do for me" got "What would you like to do? What's the project?", and "project orange" then "Who's the
arranger? (or "none")" - the AI was still the chat booking assistant. Decided: every message leads to the Book a room /
My bookings buttons; the chat answers questions only.

1. **Every reply carries Book a room / My bookings.** An AI reply that still asks for booking details or for a yes is
   replaced by "Tap *Book a room* below - the form asks for everything it needs. To change or cancel, open *My bookings*."
2. **"What can you do?"** ("how does this work", "what are your features", "who are you", "help me") -> one line on what
   Jessie does, with the menu.
3. **Booking details without "book"** ("project orange", "studio 7 tomorrow 2-4pm", "I need studio 7 every monday") -> the
   booking reply and the form (PENDING 116).
4. **The AI answers questions only** (PENDING 117): its seven booking tools are removed, and its prompt is rewritten - what
   is free, what is booked, rooms, people, session types, clients; never booking details, cards or yes/no. (33,450
   characters -> about 7,100, keeping Showing bookings, the availability rules and Who is who.) An old chat card already on screen can still be answered yes.

### Import (main only) - Cmd+A then **Delete** before importing

**main v271** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v271.json` (should MATCH
v270) → clear → Import `workflows/project-jessie-v271.json` → Save → **Publish** "v271 - every message leads to the
buttons" (Publish reloads the agent's tools) → download into `workflows/imported/project-jessie-v271-imported.json`.

### Test

0. **Factual questions first** (the prompt is new - this is the real check; the eval cannot run without n8n access):
   "what's free friday afternoon?", "is studio 7 free tomorrow 2-4?", "what do I have this week?", "who's the engineer for
   ORANGE?", "which rooms can do 5.1?", "who's Drey?" - each answered from the tools, with the buttons under it.
1. `what can you do for me` -> what Jessie does + the buttons.
2. `project orange` -> the booking reply with Project: ORANGE.
3. `is studio 7 free friday?` -> the answer, with Book a room / My bookings under it.
4. `who engineers music sessions?` -> an answer from Bookers, with the buttons.
5. `I need studio 7 every monday 2-4pm` -> the booking reply with the repeat.
6. Try to get it to book in chat ("can you just book it for me here?") -> it points to the buttons.

Offline: `node scripts/sim-every-message.js` 35; sim-step-c2 59, sim-typed-to-form 70, sim-typed-series 21, sim-slice1-a 57,
sim-round-2 38; test-nodes 570 (the booking tools' input checks no longer apply - 660 before), gate 69/69, fromai ok,
audit-model-text clean (331 texts).

## Round 3 - questions answered cleanly: main v272 (15 Oct, from the v271 test) - LIVE ~16:55 (before MATCH v271, after MATCH)

Three replies from testing v271, all on the question side:

- "what's free friday afternoon?" checked 2-4 PM - the times came from an earlier message.
- "is studio 8 free tomorrow 3-5?" -> the answer, but Book a room under it opened an empty form.
- "what do I have this week?" -> a list the AI wrote itself: Engineer / Arranger on every row, "Filtering for Howard…"
  first, loose formatting (PENDING 100: booking lists were the last facts the model still wrote).

1. **Each question uses its own times.** Room Availability's window comes from the AI's reading of *this* message; times
   from earlier messages correct it only when they were typed in this one. List Events no longer offers cancel / move.
2. **Book a room under an answer is filled in from that message** - its date, its times, a single room named - and
   nothing from earlier messages. Nothing named -> the empty form, as before.
3. **"What do I have …" is answered in code, like My bookings** (PENDING 100): "what do I have this week / tomorrow / in
   November / next week", "my bookings", "what's on my schedule", "am I engineering anything friday". The reply is
   *Your bookings* · the range, then title / date · time · room per booking (the ones you booked or are on), each with
   Change / Cancel, Previous / Next 7 days for a week, and Book a room. No engineer, arranger or preamble. Up to 20 rows.
4. **The question rules from the old prompt are back** (8,127 characters; v271 7,149): each question stands alone; relay
   what the tools said, never invent a reason or say how you searched; a booking shown is title, date with weekday, time,
   room only, unless more is asked for; the old *Style* section (timezone, Slack formatting, tone, with a good and a bad
   example). The bad example is the old 10 PM one, not the "Filtering for…" reply - a prompt that shows a habit teaches it
   (gotcha 6). Nothing about booking came back.

### Import (main only) - Cmd+A then **Delete** before importing

**main v272** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v272.json` (should MATCH
v271) → clear → Import `workflows/project-jessie-v272.json` → Save → **Publish** "v272 - questions answered cleanly" →
download into `workflows/imported/project-jessie-v272-imported.json`.

### Test (2027 dates)

1. `is studio 7 free tomorrow 2-4pm?`, then `what's free friday afternoon?` -> the whole afternoon, not 2-4.
2. `is studio 8 free tomorrow 3-5?` -> answer; **Book a room** under it opens with tomorrow, 3-5 PM, Studio 8.
3. `what do I have this week?` -> *Your bookings* with title / date · time · room, Change / Cancel per row, Previous / Next
   7 days. Then `what do I have tomorrow?` and `what do I have in November?`.
4. `what's in studio 4 on thursday?` -> the AI's answer: title, date, time, room only, no "Filtering for…".
5. The v271 questions again: `which rooms can do 5.1?`, `who's Drey?`, `who engineers music sessions?`.
6. `cancel my booking tomorrow` -> not the bookings list (the change / cancel route as before).

Offline: `node scripts/sim-round-3.js` 25; sim-every-message 36, sim-step-c2 59, sim-typed-to-form 70, sim-typed-series 21,
sim-slice1-a 57, sim-round-2 38 (with SI v19); test-nodes 570, gate 69/69, fromai ok, audit-model-text clean.

## main v273 (v272 fixed) - 15 Oct, from testing v272 - LIVE ~17:45 (before MATCH v272, after MATCH)

- "what do I have this week?" right after "is studio 8 free tomorrow 3-5?" -> "Here's what I have so far: Studio 8 · 3-5 PM",
  then "what's in studio 4 on thursday?" -> an offer for Studio 4 on Thursday. v272 put the answer's date / time / room on
  its Book a room button, and Form Offer read any such button as its own offer and the next message as more details for it.
  Nothing was booked - an offer only fills the form. Fixed: only Form Offer's own message ("Here's what I have so far:")
  counts as an offer, and a question after an offer is never more details (Menu Check likewise).
- "cancel a booking i have next friday" -> 'couldn't find a booking of yours called "have"' ("cancel a booking for next
  friday" worked). Change Offer now drops more everyday words (have, booked, scheduled, upcoming, naman, yung, pa-cancel …).

### Import (main only) - Cmd+A then **Delete** before importing

**main v273** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v273.json` (should MATCH
v272) → clear → Import `workflows/project-jessie-v273.json` → Save → **Publish** "v273 - v272 fixed" → download into
`workflows/imported/project-jessie-v273-imported.json`.

### Test

1. `is studio 8 free tomorrow 3-5?` → `what do I have this week?` → *Your bookings* (the list, not "Here's what I have so far").
2. `what's in studio 4 on thursday?` → an answer about Studio 4, not an offer.
3. `cancel a booking i have next friday` → "Which one?" with the bookings that day.
4. Still working: `studio 7 tomorrow 2-4pm` → the offer, then `project orange` → the offer with Project: ORANGE added; and
   **Book a room** under the Studio 8 answer still opens filled in.
5. The rest of round 3: `what's free friday afternoon?`, `what do I have tomorrow?`, `which rooms can do 5.1?`.

Offline: `node scripts/sim-v273.js` 16 (5 fail on v272); sim-round-3 25, sim-every-message 36, sim-step-c2 59,
sim-typed-to-form 70 (its offer fixture now has the real first line), sim-typed-series 21, sim-slice1-a 57, sim-round-2 38;
test-nodes 570, gate 69/69, fromai ok, audit clean.

## Slack Interactions v20 (v19 fixed) - hotfix, 15 Oct - LIVE ~17:45 (before MATCH v19, after MATCH)

Every single booking from the form failed since v19 (~16:26): "This couldn't be booked. Check the details and press Book
again". Book Session execution 44331 (17:09, M2) shows why - MISSING_DETAILS, "a title, a start time, an end time, a room":
it received Slack's answer to the "⏳ Your booking is being processed…" update instead of the booking (v19 put those steps in
front of the call, gotcha 45). Nothing was booked. Series were not affected. v20 hands the call the booking again.

### Import (Slack Interactions only) - Cmd+A then **Delete** before importing

**Slack Interactions v20** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v20.json`
(should MATCH v19) → clear → Import `workflows/slack-interactions-v20.json` → Save → **Publish** "v20 - v19 fixed" → download
into `workflows/imported/slack-interactions-v20-imported.json`. Independent of main v273 (either order).

### Test

1. Book a room → M booth → M2, Tue Oct 19 2027 1-3 PM → **Book** → ✅ Booked "M2 - Howard". Cancel it from My bookings.
2. Book a room → VO Recording → a studio → Book → ✅ Booked (the same call - every single booking went through it).
3. From a typed request ("studio 7 tomorrow 2-4pm" → Book a room): the reply shows "⏳ Your booking is being processed…",
   then "✅ Booked.".

Offline: `node scripts/sim-si-wiring.js` 10 (fails on v19); sim-round-2 38, sim-slice1-a 57, sim-slice1-b 34, sim-hello-form
20, sim-step-c1 60, sim-series-form 49, sim-build-b 30; fromai ok, audit clean.

## Round 4 - Slack Interactions v21 (15 Oct): rooms on top, studio + booth pairs, QC, Post Processing, all-day M booth - LIVE ~18:45 (before MATCH v20, after MATCH)

From testing v19 / v20 (the prototype screens 36 / 36b, 71-76 are the design):

1. **"Use another room"** now opens its list. It was never routed, and Slack refused its dropdown (option descriptions);
   now one note under it: "Not a usual room for <type> - booked as asked."
2. **Holding rooms and vocal booths go on top of the studio.** The Room list holds studios only - Likha, Katha and Salin
   (Celebrity Recording's ranking) and Studio A, B, D (Localization Dubbing's) are no longer room choices.
   - *Celebrity Recording*: **+ Holding room** -> "Holding rooms", the conference rooms free then (one or more).
   - *Recording sessions* (VO, Music Vocal, Celebrity, Band): **+ Vocal booth** -> the free vocal booths. A studio that
     records vocals in the room (7, 8, C, F) says "Studio F records vocals in the room - add a booth only if the session
     needs one."
3. **Localization Dubbing: Studio and Booth.** The booth starts at the studio's usual one ("Set to Studio 1's usual booth.
   Any free booth works - the engineer patches it."); the others say "the engineer patches it (Dante)"; picking another
   studio resets it (Studio 6 -> Studio D, Studio 2 -> Studio B); a taken usual booth is said. From Airtable's *Paired with*.
   Every room goes on the one booking; the card says "Room: Studio F + Studio A" and "Holding room: Likha"; Change keeps them.
4. **QC** asks for the Localization details: Project code + Engineer, no client ("NET-KUBA / JT").
5. **Post Processing**: *Booker* Dylan Diaz (set), *Project title*, no client - "BRAND REEL / DD". Anyone can pick it. No
   engineer notice. (The calendar event still says "Engineer: Dylan Diaz" - Book Session writes that line.)
6. **M booth: All day booking** appears under "What's it for?" once M booth is picked; ticked, Start and End go. One date
   only (with Repeats it asks to untick one).

Not in this build: adding or removing a booth / holding room from the Change form (it keeps what the booking has).

### Import (Slack Interactions only) - Cmd+A then **Delete** before importing

**Slack Interactions v21** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v21.json`
(should MATCH v20) → clear → Import `workflows/slack-interactions-v21.json` → Save → **Publish** "v21 - round 4: rooms, QC,
post, all day" → download into `workflows/imported/slack-interactions-v21-imported.json`. No main or Book Session change.

### Test (2027 dates)

1. Book a room → *Celebrity Recording* → step 2: the Room list is studios only (F, C); tick **+ Holding room** → pick Likha;
   tick **+ Vocal booth** → Studio A (note: Studio F records vocals in the room) → Book → "Room: Studio F + Studio A",
   "Holding room: Likha". Check the calendar event has all three rooms. Cancel it from My bookings.
2. *Localization Dubbing* → Studio 1 + Booth Studio A (usual); pick Studio 6 → the booth becomes Studio D; pick Studio B
   instead → "the engineer patches it (Dante)" → Book.
3. *QC* → Project code + Engineer only → Book ("CODE / initials").
4. *Post Processing* → Studio E, Booker Dylan Diaz, Project title → Book ("TITLE / DD").
5. *M booth* → **All day booking** appears → tick it (Start / End go) → M2 → Book → an all-day event. Untick / change the
   purpose → the times come back.
6. *Music Mixing* → **Use another room** → a list of other free studios → pick one → Book.
7. Change a booking from test 1 to another time → it keeps Studio A and Likha.

Offline: `node scripts/sim-round-4.js` 48 (fails on v20); sim-si-wiring 11, sim-round-2 38, sim-slice1-a 57, sim-slice1-b 34,
sim-hello-form 20, sim-step-c1 60, sim-series-form 49, sim-build-b 30, sim-typed-to-form 70, sim-typed-series 21, sim-step-c2
59; fromai ok, audit clean.

## Round 5 - Slack Interactions v22 + Move Booking v32 (15 Oct) - LIVE ~19:55 (before MATCH v21 / v31, after MATCH)

From testing v21:

1. **Booths**: only the usual one has a line ("Studio 1’s usual booth"); no "the engineer patches it (Dante)".
2. **"_Another room…_"** is the last choice in the Room / Studio list; picking it opens the dropdown right under the list. The
   "Use another room" row is gone.
3. **Working lines**: "Your booking is being processed. You may close this window – we’ll notify you once it’s done." (and the
   same close line when changing or booking a series); the series date check just says "Checking availability for each date."
4. **Changing an all-day booking** (an M booth all day is 12:00 AM to 12:00 AM the next day): the Change form opens with **All
   day booking** ticked and no Start / End - a room or date change keeps it all day; untick for times. Rows and cards say
   "All day".
5. **No engineer** for Music Mixing and Music Vocal Recording: an engineer, an arranger, or both - never neither ("Pick an
   engineer or an arranger."). "MUSICMIXTEST / JS". The Change form's details offer No engineer too.
6. **Rooms in order.** Google lists a booking's rooms in its own order, so the CELEBTEST Change form said "Room: Studio D".
   New bookings keep a "Rooms: Studio F, Studio D, Likha, Katha" line (Move Booking v32 keeps it up to date); older ones are
   sorted by Airtable (Vocal Booth = booth, Conference Room = holding). "Likha (Big Room)" reads "Likha". The Change form of a
   booking with a booth or holding rooms shows **Studio**, **Booth** (or No booth) and **Holding rooms**, like Book.

Still left for main: the chat's own lists ("what do I have", a typed cancel / change) show rooms in Google's order and an
all-day booking as "12:00 AM – 12:00 AM" (main's row helpers) - the same fix in main when next built.

### Import - Cmd+A then **Delete** before each import

1. **Move Booking v32** into `t7lwR2km4tfN8DbM`: download into `workflows/imported/move-booking-live-before-v32.json` (should
   MATCH v31) → clear → Import `workflows/move-booking-v32.json` → Save → **Publish** "v32 - rooms line" → download into
   `workflows/imported/move-booking-v32-imported.json`.
2. **Slack Interactions v22** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v22.json`
   (should MATCH v21) → clear → Import `workflows/slack-interactions-v22.json` → Save → **Publish** "v22 - round 5" → download
   into `workflows/imported/slack-interactions-v22-imported.json`.

### Test (2027 dates)

1. Localization Dubbing → the booths: only the usual one has a line.
2. Music Mixing → "_Another room…_" at the bottom of the list → the dropdown opens under it → pick a studio → Book.
3. Book anything → "Your booking is being processed. You may close this window – we’ll notify you once it’s done."
4. M booth → All day → Book → Change it → All day ticked, no times → pick another M booth → Change → still all day.
5. Music Mixing → Engineer "No engineer" + Arranger Joaquin → Book ("… / JS"); both empty -> "Pick an engineer or an arranger."
6. Celebrity Recording with a booth and two holding rooms → Book → My bookings shows "Studio F + Studio D + Likha, Katha" →
   Change → Studio F, Booth Studio D, Holding rooms ticked → set No booth, untick one → Change → the calendar event has
   Studio F and the one holding room; Change again → the form matches.
7. Change the CELEBTEST booking from earlier (no Rooms line) → Studio F, Booth D, Likha + Katha.

Offline: `node scripts/sim-round-5.js` 40 (fails on v21); sim-round-4 48, sim-si-wiring 11, sim-round-2 38, sim-slice1-a 57,
sim-slice1-b 34, sim-hello-form 20, sim-step-c1 60, sim-series-form 49, sim-build-b 30 (with Move v32), sim-typed-to-form 70,
sim-typed-series 21, sim-step-c2 59; test-nodes 570 (Move v32), gate 69/69, fromai ok, audit clean.

## Round 6 - Slack Interactions v23 + Book Session v111 (15 Oct) - LIVE 16 Oct ~17:15 (before MATCH v22 / v110, after MATCH; Book Session needed a second import on a cleared canvas, gotcha 40)

From testing v22: the note on a booking longer or shorter than usual ran on at the end of the Booked card, full size, in
minutes ("(240-600 minutes is typical)").

1. The note is a **small line under the card** (like My bookings' "Further ahead? …"), on the form's result and in the DM,
   above Change / Cancel. A change or cancel that goes through removes it.
2. It says **hours**: "That is a bit shorter than Localization Dubbing sessions usually run (4–10 hours is typical)."

### Import - Cmd+A then **Delete** before each import

1. **Book Session v111** into `EUG3sGXkfsJSYIMz`: download into `workflows/imported/book-session-live-before-v111.json` (should
   MATCH v110) → clear → Import `workflows/book-session-v111.json` → Save → **Publish** "v111 - lengths in hours" → download into
   `workflows/imported/book-session-v111-imported.json`.
2. **Slack Interactions v23** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v23.json`
   (should MATCH v22) → clear → Import `workflows/slack-interactions-v23.json` → Save → **Publish** "v23 - round 6" → download
   into `workflows/imported/slack-interactions-v23-imported.json`.

### Test (2027 dates)

1. Book a Localization Dubbing for 2 hours → the Booked card ends at Room; under it, small: "That is a bit shorter than
   Localization Dubbing sessions usually run (4–10 hours is typical)." - on the form and in the DM.
2. A VO Recording for 5 hours → "(1–3 hours is typical)".
3. Change the first one to another time → ✅ Changed, the old note gone. Cancel the second → ❌ Cancelled, no note.
4. A booking inside the usual length → no note.

Offline: `node scripts/sim-round-6.js` 12 (fails on v22 / v110); sim-round-5 40, sim-round-4 48, sim-si-wiring 11, sim-slice1-b
34 (version-aware), every other SI sim green; test-nodes 570 with Book Session v111; fromai ok, audit clean.

## Round 7 - Slack Interactions v24 + Move Booking v33 + main v274 (16 Oct) - LIVE ~18:15, Slack test owed

From testing rounds 5 and 6 (decided with Howard 16 Oct):

1. **"What's it for?" first** in step 1 - it decides every other field.
2. **The Change form follows the booking's session type**, read from the calendar event (a VO Recording shows no Arranger).
3. **The session type can be changed** - "What's it for?" at the top of the Change form; the details below follow it.
4. **Fields shown up front** - no "Change other session details" box; the details are on the Change form at once, filled in.
5. **Fields per session type from Airtable** (Session Types: Engineer Role Required) - an engineer, an arranger, or both.
6. **"Engineer and arranger: pick one or both."** where both roles apply (Music Mixing / Vocal / Band / Celebrity per
   Airtable) - both optional; "No engineer" / "No arranger" stay only to clear a pick (Slack cannot empty a dropdown).
7. **"Booking this for someone else?"** on meetings, events and M booths - anyone in Bookers; "Booked by: X (for Y)"; they
   can see / change it and are told; an M booth is titled with their name.
8. **Department on meetings**, set to the booker's (not on events).
9. **The Note shown** (no box), on Book and Change. 10. Repeats stays behind its box.
11. **Localization project code: type or pick** - a search list of Localization Projects (Slack's Options Load URL, set 16
    Oct) that also takes a new code ("Use … as a new code"); picking one shows the title, client and Recordist / Editor /
    Mixer, and sets the Engineer from the project (Dubbing: Recordist, Editing: Editor, Mixing: Mixer; QC: anyone).

Also: Jessie's chat lists (main v274) show rooms in order and "all day", like the form, and carry the session type.

### Import - Cmd+A then **Delete** before each import (three workflows)

1. **Move Booking v33** into `t7lwR2km4tfN8DbM`: before download `workflows/imported/move-booking-live-before-v33.json` (MATCH v32)
   → Import `workflows/move-booking-v33.json` → Publish "v33 - note + session type" → after download `…/move-booking-v33-imported.json`.
2. **Slack Interactions v24** into `PyxSPoAMtSE1gzaH`: before `…/slack-interactions-live-before-v24.json` (MATCH v23) → Import
   `workflows/slack-interactions-v24.json` → Publish "v24 - round 7" → after `…/slack-interactions-v24-imported.json`.
3. **main v274** into `uVVYVB2M7kxpLleI`: before `…/project-jessie-live-before-v274.json` (MATCH v273) → Import
   `workflows/project-jessie-v274.json` → Publish "v274 - rows: rooms, all day, session type" → after `…/project-jessie-v274-imported.json`.

### Test (2027 dates)

1. Book a room → step 1 starts with "What's it for?".
2. VO Recording → step 2: Engineer (set to you), no Arranger, a Note field. Music Mixing → "pick one or both", both optional.
3. Localization Dubbing → Project code: type "net" → the projects + "Use “NET” as a new code" → pick NET-MALAS → "BAD DAY ·
   NETFLIX", Recordist / Editor / Mixer, Engineer set to the Recordist → Book. QC → nobody preset.
4. Meeting → Department set to yours; tick "Booking this for someone else?" → pick someone → Book → "Booked by: you (for them)";
   they get a DM. M booth for someone → "M2 - Name".
5. Change a VO Recording booking → "What's it for?" VO Recording at the top, the details shown, no Arranger → switch to Music
   Mixing → Arranger appears → pick one → Change → the title gets "x initials", the event's session type changes.
6. Change with only a Note typed → Change → the event's note updated.
7. In chat, "what do I have this week?" → rooms in order, all-day bookings say "all day"; Change from there → the form knows the type.

Offline: `node scripts/sim-round-7.js` 52 (fails on v23); every earlier SI and main sim green (version-aware for the intended
changes); test-nodes 570 with Move v33 + Book Session v111; gate 69/69; fromai ok, audit clean.

## Round 8 - Log Booking v1 + Book Session v112 + Slack Interactions v25 + main v275 (19 Oct) - LIVE ~14:30, Slack test owed

What and why: `docs/design/round-8-plan.md` (Tara's three speed fixes, the forms, the wording table, Atmos / Van Recording).

### Import - four workflows, in this order (Cmd+A then **Delete** before each import into an existing workflow)

1. **Jessie — Log Booking v1 - a NEW workflow.** In n8n: create a new workflow → ⋯ → Import from File →
   `workflows/log-booking-v1.json` → Save → Publish "v1 - log after the reply". Copy its id from the URL (`/workflow/<id>`) and
   send it to Claude: `scripts/set-log-booking-id.py <id>` puts it into Book Session v112 (and is committed) - **Book Session
   cannot be imported before this.** Download → `workflows/imported/log-booking-v1-imported.json`.
2. **Book Session v112** into `EUG3sGXkfsJSYIMz`: before `…/book-session-live-before-v112.json` (MATCH v111) → Import
   `workflows/book-session-v112.json` (with the id set) → Publish "v112 - faster booking + single rooms" → after `…/book-session-v112-imported.json`.
3. **Slack Interactions v25** into `PyxSPoAMtSE1gzaH`: before `…/slack-interactions-live-before-v25.json` (MATCH v24) → Import
   `workflows/slack-interactions-v25.json` → Publish "v25 - round 8" → after `…/slack-interactions-v25-imported.json`.
4. **main v275** into `uVVYVB2M7kxpLleI`: before `…/project-jessie-live-before-v275.json` (MATCH v274) → Import
   `workflows/project-jessie-v275.json` → Publish "v275 - greeting + fewer words" → after `…/project-jessie-v275-imported.json`.

### Test (2027 dates)

First: **does the form open at all?** The blank text boxes use an invisible placeholder (U+2800). If Book a room shows "The
form did not open" in the DM, that is Slack refusing it - say so, and the placeholders come out.

1. "hi", then "reset" → "Hi, I'm Jessie!" and the two buttons only. "thanks" → "Anytime!".
2. Book a room → "Step 1 of 2", "Select a booking type", "You'll get a recommendation based on the booking details.".
3. VO Recording → Step 2: the rooms ticked list, **Another room** under it at once. Pick Another room → the tick clears; tick a
   room → Another room clears. Vocal booth dropdown (No booth, nothing picked). Text boxes empty-looking; no hints.
4. Celebrity Recording → Holding rooms: pick two → both on the Booked card.
5. Localization Dubbing → Vocal booth set to the usual one "(usual)"; Project code: type "net-malas" + Enter → BAD DAY · NETFLIX
   and the Recordist set; type a code not in Airtable → nothing shown, books as typed.
6. Meeting → no "for someone else", Department without a hint; type "post weekly meeting" → "LIKHA - Post weekly meeting".
   Event → Lobby recommended; pick Studio F under Another room → "STUDIO F - …".
7. M booth → "Who is it for?" says your first name; change to "joaquin" → "M2 - Joaquin" (he is told).
8. Atmos Mixing (or Localization Atmos Mixing until the rename) → only Studio C; when taken, "Studio C is taken then - pick
   another date or time.". Van Recording → only Studio M; Studio M nowhere else.
9. While booking: the message you opened the form from says "Your booking details:" + the form's room · date · time, "⏳
   Booking…", then "✅ Booked." (from the menu: the greeting comes back). The Booking… window: date, then time on two lines.
10. **Speed:** Book → "Booked." should take ~12-13 s (was 21.7 s). Book Session's run ~7-8 s; a screenshot of Slack
    Interactions' and Book Session's execution lists after a booking shows it.
11. The Jessie Log sheet still gets the row (now written a second or two after "Booked."); a new client still lands in New Clients.
12. Change: "Select a booking type", no hint, the Note box blank; an M booth shows "Who is it for?"; a meeting can move to a studio.
13. Cancel / Change from My bookings → "⏳ Cancelling…" / "⏳ Changing…" (the row shows what it becomes).

Offline: `./scripts/test-forms` (20 sims: sim-round-8 86, sim-round-8-book 47, every earlier sim green on both the candidates
and the live builds); test-nodes 570 + gate 69/69 with Book Session v112; fromai ok, audit clean, test-dates 17.

## Round 9 - Slack Interactions v26 + Book Session v113 + main v276 (19 Oct) - LIVE ~15:44, Slack test owed

From testing round 8 (Howard, 19 Oct afternoon):
1. The year on long dates - the Booking… window, "Your booking details:", step 2's header, the chat's "Your booking details so far:".
2. No "Not a usual room …" anywhere in the forms.
3. No usual room free -> "Available rooms:" and "The usual rooms for this type of booking are not available in your chosen schedule" under it.
4. Studio E only for Post Processing (like Studio M for Van Recording) - forms and Book Session.
5. Vocal booth / Engineer (where an arranger also counts) / Arranger: optional, no "No …" options; empty reads "No booth" / "No
   engineer" / "No arranger" - Slack's own clearing line then says the same. Book and Change.
6. No "Engineer and arranger: pick one or both." (neither picked still says "Pick an engineer or an arranger.").
7. "Recommended rooms:" (Localization Dubbing: "Recommended studios:"), no "Recommended" line, the top one ticked; "Choose a different room".
8. At most 6 rooms in the list; the rest under Choose a different room. (Airtable: Event's usual rooms trimmed - PENDING 120.)

Not changeable (Slack's own): the "Are you sure you want to leave?" box and its Keep Editing / Continue buttons.

### Import (Cmd+A then **Delete** before each)

1. **Book Session v113** into `EUG3sGXkfsJSYIMz`: before `…/book-session-live-before-v113.json` (MATCH v112) → Import
   `workflows/book-session-v113.json` → Publish "v113 - Studio E for Post Processing" → after `…/book-session-v113-imported.json`.
2. **Slack Interactions v26** into `PyxSPoAMtSE1gzaH`: before `…/slack-interactions-live-before-v26.json` (MATCH v25) → Import
   `workflows/slack-interactions-v26.json` → Publish "v26 - round 9" → after `…/slack-interactions-v26-imported.json`.
3. **main v276** into `uVVYVB2M7kxpLleI`: before `…/project-jessie-live-before-v276.json` (MATCH v275) → Import
   `workflows/project-jessie-v276.json` → Publish "v276 - the year on the offer" → after `…/project-jessie-v276-imported.json`.

### Test (2027 dates)

1. Book an M booth all day → the Booking… window says "Tuesday, October 19, 2027" then "All day"; the message the same.
2. VO Recording → "Recommended rooms:", no "Recommended" under Studio 7 (it is ticked); "Choose a different room", no line under
   it, no Studio E / Studio M in it. Vocal booth reads "No booth"; open it - the clearing line should read "--No booth--" (or
   "Clear selection"), and there is no separate "No booth".
3. Music Vocal Recording → Engineer "No engineer" / Arranger "No arranger" when empty, no "pick one or both"; book with only
   an arranger; then with neither → "Pick an engineer or an arranger.".
4. A time when the usual rooms are all taken → "Available rooms:" and the line under it; book one - it goes through.
5. Event → at most 6 rooms in the list (after the Airtable trim: Lobby, Katha, Likha, Salin, Studio F, Studio C).
6. Meeting → no Studio E under Choose a different room. Post Processing → Studio E.
7. Change a booking with a booth → Vocal booth can be emptied ("No booth"); an arranger can be added or cleared.
8. Type "book studio 7 tomorrow 2-4pm" → "Your booking details so far:" with the year.

Offline: `./scripts/test-forms` (21 sims; sim-round-9 40); test-nodes 570 + gate 69/69 with Book Session v113; fromai ok, audit clean.

## Round 10 - Slack Interactions v27 (19 Oct): questions after Book reach the DM - LIVE ~16:24, Slack test owed

Tara's Celebrity Recording (16:07): Book -> "You can close this window" -> closed -> Book Session asked "Is this a Music or an
Audio Post session?" -> the window was gone (views.update `not_found`) -> nothing reached her.

1. Step 2 asks **Department** for types whose roles span departments (Celebrity Recording, Van Recording), set to the booker's.
2. A question / problem that comes back after the window closed goes to the **DM** ("Not booked yet: …" + Book a room, filled in);
   a series checked but never confirmed, and a refused change, too.
3. The working lines: "You can close this window – we’ll let you know in your DM once it’s done."

Import: **Slack Interactions v27** into `PyxSPoAMtSE1gzaH`: before `…/slack-interactions-live-before-v27.json` (MATCH v26) → Cmd+A,
Delete → Import `workflows/slack-interactions-v27.json` → Publish "v27 - questions reach the DM" → after `…/slack-interactions-v27-imported.json`.

Test: Celebrity Recording → step 2 shows Department (Audio Post for you) → Book → booked, no question. Then something that asks
after Book (e.g. a client spelled close to a real one, "jem lin") → press Book and **close the window at once** → the DM says
"Not booked yet: Did you mean *Jem Lim*? …" with Book a room → it opens the form filled in. Tara: Band Recording again.

### Round 10b - Slack Interactions v28 (19 Oct): the details stay when not booked

When a booking comes back unbooked and the window is gone, the message it started from keeps "Your booking details:" and the
room · date · time, with "⚠️ Not booked yet – see below" (the question is in the DM). Import into `PyxSPoAMtSE1gzaH`: before
`…/slack-interactions-live-before-v28.json` (MATCH v27) → Cmd+A, Delete → `workflows/slack-interactions-v28.json` → Publish
"v28 - details kept when not booked" → after `…/slack-interactions-v28-imported.json`.
Test: Book from the menu something that asks after Book ("jem lin"), close the window at once → the menu message shows your
details with "⚠️ Not booked yet – see below", and the DM below it asks the question.
