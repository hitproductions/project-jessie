# Slack tests owed - 4 Nov 2026

Every build since the 27 Oct launch fixes whose Slack test is not recorded as done, from `PENDING.md` and the EODs. Some may have
been tested without being written down - tick those off. Since the flip these are real bookings with real notices: use a willing
colleague, and cancel what you book.

## A. Today's builds (main v289 / v290, Slack Interactions v64, Book Session v126) - PENDING 149

1. "book studios a and 1 for tomorrow 2-4pm" -> Studio 1 + Studio A. **Done 4 Nov 1:44 PM.**
2. Book a room from that message, Localization Dubbing -> step 2 has Studio A ticked under Vocal booths; add Studio E -> "Picked: Studio A,
   Studio E" under it (on a phone too); Book -> booked with Studio E as a booth.
3. Change that booking -> the Change form's Vocal booths keep both, with the Picked: line.
4. "book studio 1 and m tomorrow 2-4pm" -> Studio 1 and "⚠️ Studio M is only for Van Recording, so it's left off." (v290)
5. "show me bookings i made on december 2027" -> the list with Change / Cancel and Jump to a date (not a text answer).
6. My bookings -> Jump to a date next year -> that week, headline with the year.
7. A Repeats booking (3 dates) -> "Checking 3 dates…" says "Keep this window open – the dates show here."
8. Post Processing -> Studio E still offered as the room.

## A2. The series review (Room Availability v26, Book Series v9, Slack Interactions v66) - PENDING 150

1. A weekly series over a date where the room is taken -> the review shows that date in another room ("Studio 6 instead of Studio 1").
2. A date where every usual studio is taken then -> a required pick (earlier / later / skip).
3. 20 dates or more -> "Are you sure? You're about to book N appointments."; a six-month series is accepted, seven months is not.
4. Book all -> the DM lists what was booked; a skipped date has Find another time, which opens Book a room filled in for that date.
5. Note how long Find rooms and the review take for a long series (they should not grow with the number of dates).

## B. Rooms booked outside KDC Bookings (Room Availability v25 / Book Session v125) - PENDING 148

9. On your own calendar, an event tomorrow 3-4 PM inviting M8 (the room accepts) -> "is m8 free tomorrow at 3?" -> taken ("Booked outside
   KDC Bookings"); Book a room M8 at that time -> not offered / refused. Delete the event after.

## C. Owed since 27-29 Oct - most relevant to Localization first

10. **Room requests (121 / 122)** - the claim step has never run live: book a room someone else holds -> "Booked – ask to use" -> Send
    request; the holder answers (Keep / Give it up). Then a second request, and both people answer within a few seconds -> only one counts.
11. **A hand-made booking can be asked for (124)** - a calendar booking with no `ref:` but a "Booked by: <name>" line -> the room shows under
    "Booked – ask to use" and the request reaches that person.
12. **Several studios on one booking (141)** - + Multiple studios (Studio 1 + Studio 2) -> one calendar event with both rooms; Change keeps both.
13. **M booth all day, repeating (SI v56)** - M booth, All day, Repeats weekly on Monday x4 -> four all-day events.
14. **"Did you mean …?" on Change after the window is closed (128)** - Change a booking's client to a near-miss name, close the window ->
    the question arrives in the DM with Continue changing.
15. **Notices (129)** - book for someone else with an engineer -> the engineer's notice names who it is for; change the details -> the
    "for" person is still on it; remove the engineer -> they are told it was "taken off", not "moved".
16. **A note is not read as a person (127)** - a booking whose note mentions a staff name -> that person gets no reminder / notice.

## D. Owed since 27-28 Oct - other departments (before Audio Post / Music roll out)

17. **Atmos Mixing (136 / 138)** - its own form (project or code, engineer, Department), Studio C only; at a taken time -> Studio C's day shown.
18. **New client = client work (135)** - a non-studio department books for a client not in Airtable -> Type: External, not Internal.
19. **New client kept through Change (133)** - change a booking's client to a new name -> a New Clients row ("Close to" filled).
20. **Slash in a title (134)** - project "Backyard Live // Test" -> the title reads "BACKYARD LIVE - TEST".
21. **Room questions (139 / 140)** - "what rooms have symphony?" -> answered from Airtable; "is studio f and c free tomorrow?" -> both answered.

## Not testable by hand

- 125 (a failed step tells the person and Ops Alert) - only shows when Google / n8n fails; watch for it.
- 147 (Room Check's DM) - needs the 29 Oct ~6:15 PM Room Check execution (Send DM's output).
