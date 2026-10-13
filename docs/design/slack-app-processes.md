# Slack app pivot — process map (working notes)

Working notes, not for presenting. Every feature of the current chat build (main v261 / Book Session v108 / Cancel v26 /
Move v29 / Room Availability v22, Claude Haiku 5.5) mapped to how the Slack-app version does it, so nothing is lost on the
way. The before / after presentation is made from this file once the processes are settled.

Status: brainstorm. Nothing is built. Block Kit samples live outside the repo until a design is settled.

Legend for the last column: **Keep** (same behavior, same backend) · **Gain** (new) · **Lose** (goes away, and why that
is fine) · **Change** (same goal, different way).

## Decided so far

- **Front door: a DM menu**, no Home tab. Three buttons: **Book a room** · **My bookings** · **Studios** (the day board).
  The menu shows on a greeting or anything not understood, at the end of each result (as a ⋯ menu), and on "menu".
  No "next booking" line for now.
- **AI keeps two jobs:** reading the first natural-language message (to pre-fill a form or find a booking) and answering
  questions. Everything that books or changes goes through a form or a button.
- **Typed changes stay:** "cancel my friday booking" / "make it 3pm" — the AI finds the booking, then shows it with
  buttons. No typed "yes".
- **Follow-up questions:** a short window (the previous question only, a few minutes, nothing carried from bookings).

## 1. Starting a request

| Feature now | After the pivot | |
|---|---|---|
| Type anything; the AI works out what you want | Same, plus the menu buttons | Keep |
| "reset" clears the thread's context | Not needed for bookings (each form stands alone); questions use the short window | Lose |
| Transcript of the last 20 lines given to the AI | Only for the first message and questions | Change |

## 2. Booking a room

**Form order:** step 1 = date, start, end, **What's it for?** (session types + Meeting / Event / Booth time), Repeats.
Step 2 = the 🗓️ line, **Room** (radio list: free rooms that fit, ranked, top one marked Recommended; a note names usual
rooms that are not free then), then the details. **Book** = the confirmation.

| Feature now | After the pivot | |
|---|---|---|
| Details collected one question at a time (code-written questions, v258) | One form, pre-filled from the first message | Change |
| Date and time read from words ("next thursday", "2-5"); gaps: "bukas", "for 2 hours" | Date and time pickers; the first message only pre-fills them | Change |
| "Next Thursday" rule (from Friday on, the one after) | Kept for reading the first message | Keep |
| Room suggested from the Airtable ranking (Session Types Priority / Last Resort) | Same ranking drives the room list | Keep |
| Room taken → nearest free times, other studios, another day (v249+) | Mostly prevented (only free rooms listed); otherwise the same suggestions as one-tap choices | Keep + Gain |
| Last Resort room refused once, booked if the requester insists (`ROOM_NOT_PRIORITY` / override) | Last Resort rooms listed when no usual room is free; **Show all suitable rooms** (in the ⋯ menu on the 🗓️ line) adds every free room that can do it (Priority + Last Resort), marked "not a usual room", booked without a second refusal | Change |
| Room checked as soon as named (early heads-up) | Built into step 2 | Change |
| "Which kind of mixing?" from Airtable | "What's it for?" list in step 1 | Change |
| Unusual length / past date heads-up | Shown on step 2 before Book | Keep |
| Confirmation card + check code + typed "yes" (Prepare Booking) | Book button | Lose |
| The room's answer read back after booking (44) | Same | Keep |
| No double booking, room suitability, ownership, consent / priority | Same Book Session guards | Keep |
| Free times offered within a fixed window | Free times offered 8 AM – 11 PM; bookings at any hour shown | Change |

**Any free room** is no longer a separate path: the room list in step 2 is always "free rooms that fit". A room named in
the first message is pre-selected if free; if not, the note says when it is free and the recommendation is selected.

## 2a. Paired rooms (booths and holding rooms)

(Proposed 13 Oct, not yet agreed.) Today: a booking can hold several rooms (`rooms` = "Studio 1, Studio A") on one event;
a booth is allowed when it is paired with a ranked studio and refused on its own; Celebrity Recording gets "Want a holding
room? (Likha, Katha or Salin)" from its Room Requirements; Airtable has each control room's **Paired with** (Studio 1 → A,
Studio 2 → B, Studios 3-7 → A, B or D "can change using Dante", Studio D → 6, Studio E → 7) and **Records Vocals In-Room**
(7, 8, C, D, F).

- **A session that needs a booth** (Room Requirements say so: Localization Dubbing): the room list offers **pairs** -
  "Studio 1 + Studio A", "Studio 2 + Studio B" - built from Paired with, only where both rooms are free. One pick, no
  second question.
- **Holding rooms** (Room Requirements mention conference rooms: Celebrity Recording): a **Holding rooms** checklist of the
  conference rooms free then; one or more, or none.
- Both go on the one booking, as today; Move and Cancel take every room with them.

| Feature now | After the pivot | |
|---|---|---|
| Several rooms on one booking; booth only with a studio | Same | Keep |
| Booth chosen by the model / requester's words | Pairs offered from Airtable's Paired with | Change |
| A booth with any studio when asked (special cases) | Pair with a vocal booth checkbox, off by default | Change |
| "Want a holding room?" note, answered in chat | Holding rooms checklist on the form | Change |
| Which rooms record vocals in-room (Airtable checkbox, v229) | Same data; a typed question answers it | Keep |

Decided (13 Oct): no booth by default unless the session type is set up that way (Room Requirements). Any studio can still
be connected to a vocal booth in special cases, so studio sessions get an unticked **Pair with a vocal booth** checkbox
under the room list; ticking it adds **Which booth?** - the vocal booths (Airtable Vocal Booth: A, B, D) free then, the
studio's Paired with booths first - and a note when the pairing is not the usual one (the engineer patches it).
Not shown for internal rooms. **Where it lives:** both rare options - *Show all suitable rooms* and *Pair with a vocal
booth* - sit in a small ⋯ menu at the end of the 🗓️ line (decided 13 Oct), so they take no space; picking one redraws
the form with the full room list or the Which booth? dropdown.

## 2b. After Book — results

(Proposed 13 Oct, not yet agreed.) Slack wants an answer to a form within 3 seconds and a booking takes longer (calendar,
Airtable, the room's read-back). So: quick checks (a required field, end before start) answer on the form at once; on
Book the form turns into "Booking Studio 7…", then into **Booked** or, for a problem, back into the form with the problem
at the top and everything entered kept. The result also goes to the DM as the lasting record, with its buttons.

| Outcome now (chat) | After the pivot (DM message) | |
|---|---|---|
| "Booked." reply | ✅ Booked: title, room · date · time, session type · engineer · booking type; Move · Cancel · ⋯ (Book another, Book again another day, My bookings, Studios) | Keep + Gain |
| "Booked" said ~6 s later, after the room's read-back (Book Session v106) | Booked at once with "⏳ Waiting for Studio 7 to accept…", updated in place to "✓ accepted" | Change (faster) |
| Room declined → "❌ Studio 7 turned this booking down … Nothing is booked." (44); Jessie's event stayed on the calendar | Same message; Jessie's event is deleted; free rooms then and one-tap Book instead / Pick another room or time | Keep + Change + Gain |
| Long-session / past-date heads-up on the card and the reply | On step 2 before Book, and on the result | Keep |
| Room taken between the check and the yes (`ROOM_OCCUPIED`) | Shown on the form, other free rooms listed, entries kept | Change |
| Client near miss, unknown engineer, Last Resort room (refusals with a question) | Shown on the form next to the field | Change |
| Consent request opened (priority / held M booth) — a chat reply | ⏳ Requested, with the deadline; **Withdraw request** | Keep + Gain |
| Series: booked / skipped (room taken or declined) / failed, with "want these at a different time?" | Same report; one-tap fix for a skipped date; Cancel the whole series | Keep + Gain |
| New client logged for review | Same, one line on the result | Keep |
| Honest failure when nothing was booked (Guard Probe claim check) | ⚠️ Nothing was booked; Try again / Edit the booking | Keep |

Decided (13 Oct):
- **The form stays open after Book** and turns into "Booking..." then the result (or the problem, entries kept); Done
  closes it. The DM gets the result as the record.
- **PENDING 44: a declined booking is deleted.** When a room turns a booking down, Jessie deletes her own event and says
  so; the calendar never keeps a booking the room refused. The DM result offers the free rooms and a one-tap rebook.

## 2c. Recurring bookings (series)

(Proposed 13 Oct, not yet agreed.) Today: the model reads the pattern and calls Prepare Series; Expand Series computes the
dates in code (daily or weekly on chosen weekdays, a count or an end date, never open-ended, within a year); Book Series
books up to 16 dates server-side and reports booked / skipped / failed; before the yes a date can be skipped or given
another room or time; a taken date gets alternatives; one series card, one yes.

- **Step 1:** a small *Repeats* checkbox (like the booth one); ticking it adds **How often** (Weekly / Daily), **On**
  (weekday checkboxes, the first date's weekday ticked), **Ends** (after a number of occurrences, 2-16, or on a date).
- **Step 2:** the 🗓️ line says the pattern ("Every Tuesday · 10:00 AM – 12:00 PM · 4 dates"); the room list says how many
  dates each room is free on ("free on all 4 dates" / "3 of 4"); a **Dates** list shows every date with ✓ or ⚠️, each with
  a ⋯ menu (Skip this date / Use another room / Change the time); a taken date offers its alternative as one tap. The
  button says how many dates it books ("Book 4 dates").
- **Result:** as in 2b (booked N of M, a skipped date with a one-tap fix, Cancel the whole series).

| Feature now | After the pivot | |
|---|---|---|
| Pattern read from words ("every tuesday for 3 weeks") | Repeat fields; a typed pattern pre-fills them | Change |
| Dates computed in code (Expand Series), never open-ended, within a year, up to 16 | Same | Keep |
| Series card + one yes (Prepare Series, v226) | Step 2 with the Dates list; Book N dates | Change |
| Per-date skip / room / time before the yes (Book Series v6) | ⋯ on each date | Keep |
| Taken date: alternatives or left out (v7) | Same, as a one-tap swap per date | Keep + Gain |
| Booked / skipped / failed report | Same, on the result | Keep |
| Each date cancelled on its own | Cancel this date or the whole series (needs a series id, section 5) | Gain |
| In-progress lock while a series books (~25 s a date) | Same; the form shows "Booking 4 dates…" | Keep |
| Each date moved on its own | Move this date, or the whole series from a chosen date | Gain |

**Move a whole series** (decided 13 Oct): on a booking that is part of a series, Move offers *Move this date* or *Move the
whole series*. The series form is pre-filled with the pattern (weekdays, start, end, room) and a *From* date (this
occurrence and the ones after it); the Dates list shows each new date with ✓ / ⚠️ and its ⋯ menu, as when booking; the
button says how many it moves. Each date is moved the safe way (new one created before the old one is removed), and the
result reports moved / skipped / failed. Needs the series id (section 5).

## 3. Booking details

Step 2 is built for the requester (Bookers department → **Booking Defaults** row) and the session type, so only fields
that apply are shown.

| Field | Shown when | Default / source |
|---|---|---|
| Project | studio sessions | typed; title uses it in ALL CAPS (post and music) |
| Project code | Localization sessions | searched from **Localization Projects**; client and title come from it; written as in the table |
| Client | studio sessions except Localization | **typed** (option A): on Book, exact match → that record; near miss → "Did you mean …?" on the field; not found → booked as typed + New Clients sheet |
| Engineer | studio sessions | Slack people picker; you if your department's rule is "self"; required if "ask" (arrangers, Marketing) |
| Arranger | music sessions | you, if you are an arranger |
| What kind of booking? Client work / Internal / Personal | departments with more than one option | department default; code decides Advertising vs Entertainment (department + client's Client Type; Localization always Entertainment) |
| Department | only for people in more than one | — |
| Booking for someone else | behind a checkbox | empty = you |
| Meeting title | Meeting, Event | typed |
| Notes | always, optional | — |
| Repeats (days of week, number of weeks) | step 1 | — |

| Feature now | After the pivot | |
|---|---|---|
| Title written by the AI, then repaired by code (initials, project / client put back, "(new client)" stripped, M booth first name) | Title assembled by code from the fields: `PROJECT / Client / initials`, `ROOM - title` for meetings, `<code> / initials` for Localization | Change (the repairs become formatting) |
| Nickname → staff (Booked For, Bookers "Goes by") | Same reader pre-fills the people picker (all 58 Bookers have a Slack User ID) | Keep |
| Client / staff nickname clash asked ("Anj", 82) | The picker stays empty for an unresolved or shared nickname | Change |
| "for X" → booked for / client (Booked For, forClient) | Pre-fills the checkbox field or the client field | Keep |
| Near-miss client "Did you mean …?" | Same, on the form field | Keep |
| New client → New Clients sheet | Same | Keep |
| NEED_DEPARTMENT / NEED_BOOKING_TYPE / NEED_ARRANGER questions | Form fields shown only when needed | Change |

## 4. Finding out

| Feature now | After the pivot | |
|---|---|---|
| "What's free …" typed, answered in code (Room Availability) | Same, typed; answers carry Book buttons | Keep + Gain |
| — | **Studios** day board: each room's free and taken times (no titles), date picker, filter, previous / next day, one Book button per room, refreshed in place. 🟢 nothing booked in 24 h · 🟡 partly free · 🔴 no free time 8 AM – 11 PM | Gain |
| "What do I have booked" — list written by the AI (PENDING 100) | **My bookings** — list built by code | Change |
| Availability answers borrowing an earlier request's window (wide test D1 / D2) | Questions do not inherit booking details | Lose (the bug) |

### Typed questions (proposed 13 Oct, not yet agreed)

The AI's job on a typed message is to **route it and pull out the parameters** (date or range, room, session type); code
writes every answer that states a fact, and each answer carries buttons to act on it. Follow-ups use the short window.

| Question now (tool behind it) | After the pivot | |
|---|---|---|
| "Is Studio 7 free Friday?" (Room Availability, code layout) | Same code answer; **Book Studio 7 on Friday** (form pre-filled) · **All studios on Friday** (the day board) | Keep + Gain |
| "What's free tomorrow afternoon?" (Room Availability) | One line per free room with a **Book** button (room, date, time pre-filled); studios only unless rooms are asked | Keep + Gain |
| "What do I have / what's in Studio 4 Thursday?" (Find Booking / List Events, model-written list - 100) | My bookings, or that room's line from the day board, built by code | Change (fixes 100) |
| Room facts: formats (5.1 / Atmos), vocals in-room (code lists from Airtable, v229) | Same | Keep |
| Other room / equipment questions (model reads Rooms and Studios) | Same, model-written from Airtable (low stakes); ends with Studios / Book | Keep |
| People and clients ("who is drey?", Bookers / Clients) | Same, from Airtable | Keep |
| Session type facts ("how long does VO usually run?", Session Types) | Same | Keep |
| Off-topic ("what's the weather?") | One line + the menu | Change |
| Not understood | "I didn't catch that" + the menu | Change |
| A question picking up an earlier request's details (wide test D1 / D2 / F2) | Questions read only themselves and the previous question | Lose (the bug) |

Decided (13 Oct): a whole day ("what's free Friday?") is answered with the day board; part of a day ("tomorrow afternoon",
"2-4 PM Friday") with the per-room list.

## 5. Cancel and move

(Proposed 13 Oct, not yet agreed.) Cancel Booking and Move Booking already accept an `event_id`, so a button can hand
them the exact booking; finding it by title is only needed for the typed path.

**Ways in:** My bookings (each booking with Move / Cancel) · the "Booked." result · a typed request ("cancel my friday
booking", "make it 3pm"), where the AI finds the booking and shows it with buttons · notices.

**Cancel:** Cancel button → Slack's confirm pop-up ("Cancel this booking?" with the title, room, date, time; *Cancel
booking* / *Keep it*) → Cancel Booking with the event id → the message updates in place to "Cancelled".

**Move:** Move button → a small form pre-filled with the booking's date, start, end and room (room: "Keep Studio 7" or
another free room that fits) → **Move** = the confirmation. The new time is checked first; if taken, the form says so on
the field with the nearest free times. A typed "make it 3pm" shows the booking with a one-tap **Move to 3:00–5:00 PM**
button and **Pick another time**.

| Feature now | After the pivot | |
|---|---|---|
| Find by title, exact or close; by description; without a date (Find Booking, Cancel v20+) | Buttons carry the exact booking; the typed path still finds by description | Keep (typed) + Change |
| Two bookings with the same title on a day → "which one?" by time (72) | Each booking has its own buttons; typed path lists each match with its own buttons | Lose (the question) |
| Two cancels in one message → one card (55 / 60) | Typed path lists every match with its own buttons | Gain (fixes the gap) |
| Cancel card + typed "yes" | Slack confirm pop-up | Change |
| Move card ("Now: … → New: …") + typed "yes" | Move form; Move button = confirmation | Change |
| "make it 3pm" (Move Direct) | One-tap move suggestion | Keep + Change |
| New time checked before the card; taken → free times, no card (v29) | Same check, shown on the form field | Keep |
| Replacement created before the original is deleted; `PARTIAL` if the delete fails | Same | Keep |
| Room change in a move (`new_rooms`) | Room choice in the Move form | Keep |
| Duration kept unless changed | End time pre-filled to keep the duration | Keep |
| Only your own bookings (`NOT_YOURS`); coordinators within their department; HAIST Dev any | Same checks on every click; buttons shown only where allowed | Keep |
| Moving into a priority slot opens a consent request | Same | Keep |
| Notices to the booker and engineer (DEV_REDIRECT during QA) | Same | Keep |
| — | Old messages updated when a booking changes (no stale "Booked." with live buttons) | Gain |
| — | A click on an old message re-reads the calendar ("already cancelled") | Gain |
| Each date of a series cancelled on its own | Cancel this date, or the whole series (future dates) | Gain |
| "What do I have booked" covers bookings made and engineered | My bookings: made + tagged, 7 days by default, all upcoming on request | Keep + Gain |
| — | Department bookings view for coordinators (nice-to-have) | Gain |

Decided (13 Oct):
- **My bookings** lists bookings you made and bookings you are tagged on (engineer, arranger; later, people tagged on a
  meeting). Tagged ones show without buttons unless you may change them. Default view: the next 7 days; **See all
  upcoming** opens a scrollable form with everything ahead (more pages if it runs long), so the DM stays short.
- **Coordinators:** typed requests work now; a **Department bookings** view (same list, the whole department) is a
  nice-to-have, shown only to people with booking authority.
- **Cancel series:** added. A booking that is part of a series offers *Cancel this date* or *Cancel the whole series*
  (future dates only). Needs a series marker on each event: Book Series books each date as its own event and links them
  by nothing today, so it would write a shared series id into each event. Series booked before that can only be matched
  by title, room, weekday and time.

## 6. Approvals and notices

(Proposed 13 Oct, not yet agreed.) The consent engine stays as built (one Google Sheet row per request, Consent Sweep
every ~10 min, compare-and-set finalize, the Sheet edit as break-glass). Buttons replace typed replies on both sides, and
every message updates in place when the request resolves.

**Priority request, holder:** a DM with their booking, who asks and why it takes priority, the free times they could move
to, and the deadline. **Agree and move my booking** opens the Move form pre-filled with the first free option; once moved,
Finalize places the requester. **Decline** (with a confirm pop-up) keeps the booking. No answer by the deadline: the booking
stays, the request expires.

**Priority request, requester:** ⏳ Requested, with the deadline. **I've already cleared it with them** (the requester-attest
path, with a confirm pop-up) · **Withdraw request** · **Pick another room or time**. It updates to Booked, or to Declined /
No answer with the free alternatives and a one-tap rebook.

**Shared booth (M booth with a standing hold), holder:** **Let them use it** / **Keep it**; no answer by the deadline books it
for the requester (as today), and the message says so up front.

**Notices:** a coordinator's cancel or move → booker and engineer, with My bookings; a new booking → the engineer, with
**Got it**; a declined room → the requester (section 2b).

| Feature now | After the pivot | |
|---|---|---|
| One Sheet row per request, sweep, idempotent finalize, Sheet break-glass | Same | Keep |
| Holder replies "yes" / "no" in chat, read by main's reply router | Agree and move / Decline buttons | Change |
| Requester types "cleared with <name>" (attest) — loops (79) | A button with a confirm pop-up | Change (fixes 79) |
| Blank names in the request messages (78) | Messages written in code from the row | Change (fixes 78) |
| Incumbent consents, then moves in a separate step | Agree opens the Move form with free times | Change |
| The same request can open twice (27) | The requester's pending request is shown; a second one is refused | Change (fixes 27) |
| M booth: timeout books for the requester | Same, stated in the message | Keep |
| Deadlines and timeouts (37, never run live) | Same; needs its live test either way | Keep |
| A priority request goes to the booker only (80; decided 4 Oct: the engineer too, first answer wins - not built) | Booker and engineer both get the buttons; the first answer decides, the other's message updates to say who answered | Change (fixes 80) |
| — | Withdraw request | Gain |
| Cancel / move notices to booker and engineer (DEV_REDIRECT in QA) | Same, with a My bookings button | Keep + Gain |
| — | Engineer told of every new booking, with Got it (decided) | Gain |
| — | Reminders (decided): **studio sessions** the day before (Still on / Move / Free up the room); **M booths and conference rooms** in one weekly message listing the week's bookings, each with Keep / Free up | Gain |

A button pressed during a Cloudflare outage fails with Slack's own error ("didn't respond") instead of being lost
silently, as a chat reply is now; the attest button and the Sheet edit remain as fallbacks.

Decided (13 Oct): the engineer may answer a priority request too (first answer wins); the engineer is told of every new
booking; reminders as in the table. The weekly message goes out **Monday 9:00 AM** and includes standing M booth holds ("Still need M4 on
Tuesday?" - freeing one releases that week's slot).

## Open questions

- Rooms outside both ranking lists (today bookable after a refusal and "go ahead"): offer them under Show all, or not at all?
