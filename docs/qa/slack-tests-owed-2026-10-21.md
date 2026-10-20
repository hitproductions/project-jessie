# Slack tests owed - 21 Oct 2026

Everything built since round 5 (15 Oct) that has not been tested in Slack yet, in one list, as it works **now** (main
v277, Book Session v119, Slack Interactions v36 (live 21 Oct ~00:17), Move v34, Room Check v2, Reminders v2). Steps that
later builds replaced are left out (the project-code search list, the Post Processing Booker dropdown, "pick one or
both", Music Vocal Recording). Per-round detail: `docs/design/slack-app-test-round-1.md`.

Use 2027 dates (the QA year shift). Clean up from My bookings afterwards. Stop at the first thing that looks wrong and send
a screenshot - from n8n too if a step was slow or said nothing (open the run, then the sub-execution).

## A. Chat and the menu

1. "hi", then "reset" -> "Hi, I'm Jessie!" and the two buttons only. "thanks" -> "Anytime!".
2. "book studio 7 tomorrow 2-4pm" -> "Your booking details so far:" with the year; Book a room opens filled in.
3. Typed "for": "book studio e tomorrow 10-12 for dilan" -> Post Processing, *Who is it for?* Dilan; "book a vo session
   tomorrow for josiah" -> Josiah as Engineer; "… for bp" -> BP Valenzuela; "book m4 tomorrow for sasa" -> *Who is it
   for?* Sasa.
4. "what do I have this week?" -> rooms in order, all-day bookings say "all day"; Change from there knows the booking type.

## B. Book a room - step 1 and step 2

5. Step 1 starts with *What's it for?*; "Finding free rooms…" says "Usually under 10 seconds.".
6. VO Recording -> "Recommended rooms:" with the top one ticked; *Choose a different room* (no Studio E / M) - picking
   there clears the tick and the other way round; Vocal booth reads "No booth"; Engineer set to you; no hints.
7. A time when the usual rooms are taken -> "Available rooms:" and "The usual rooms … not available" under it; book one.
8. **Band Recording with Studio F and C both taken** (v35) -> other free studios offered the same way; book one.
9. Every studio taken -> "Nothing that does … is free then", no Book button.
10. Localization Dubbing -> "Recommended studios:", the usual booth "(usual)", project code a plain box (no "Press
    'enter'"); the title starts with the code. QC -> no client asked.
11. Music: Music Presentation, Mixing, Arranging and Recording each book (none says "Couldn't book this"); Arranger above
    Engineer; Arranging / Presentation need the arranger; you are pre-filled in your own role only; neither picked ->
    "Pick an engineer or an arranger.".
12. Celebrity Recording with a booth and two holding rooms -> all on the Booked card; with only a Post Engineer the
    department is Audio Post, with an arranger Music (no Department field).
13. Meeting -> tick one room then another: no flicker; title "LIKHA - Post weekly meeting" (capital); a studio can be
    picked under *Choose a different room*, never Studio E. Event -> at most 6 rooms.
14. M booth -> All day; *Who is it for?* your first name; change to "joaquin" -> "M2 - Joaquin".
15. Post Processing -> Studio E only; *Who is it for?*; no project -> "POST PROCESSING - Dilan", with one ->
    "POST PROCESSING - TRAILER / Dilan".
16. An Atmos type -> Studio C only; Van Recording -> Studio M only.
17. Repeats -> "How often?" Weekly / Weekdays / Daily; a weekly series of 4: Checking… and Booking… each show an
    estimate; all four booked.
18. A session longer or shorter than usual -> one small line under the card: "That's a bit longer than a usual …
    session (1–2 hours)."

## C. After Book

19. The Booking… view: date, then time on its own line, with the year; "Usually under 30 seconds.". The message you
    started from: "Your booking details:" + "⏳ Booking…", then "✅ Booked.".
20. "Booked." comes fast; the room's answer is checked after it.
21. Something that asks after Book (client "jem lin"), window closed at once -> the DM says "Not booked yet: Did you mean
    *Jem Lim*? …" with Book a room (opens filled in); the message you started from keeps your details with "⚠️ Not booked
    yet – see below".
22. Forced room decline: put Studio A in an event from a personal calendar, then book Studio A at that time through
    Jessie -> a DM "Studio A turned this booking down", the event gone; Book a room refills the form.
23. The Jessie Log row a few seconds after Booked; a new client -> New Clients; a made-up QC code (TEST-NEW-01) -> a row
    in New Projects (a code Airtable has adds nothing).
24. **v36:** the Booked DM ends with *Book another* / *My bookings*; *Book another* opens a blank form and
    the Booked card above stays as it is while the new one books; a booked series' DM says *Book another*; the Changed DM
    ends with *Book a room* / *My bookings*. Post Processing for Dilan: the notice says "… booked this for you." (comes to
    you in QA).

## D. My bookings, Change, Cancel

25. Change a VO Recording -> *What's it for?* at the top, the details shown, no Arranger; switch to Music Mixing ->
    Arranger appears; Change -> the title and the event's booking type change; "Changing…" shows an estimate.
26. Change with only a Note typed -> the event's note updated.
27. Change a Band Recording with no booth -> Vocal booth offered, empty; pick Studio A -> Studio F + Studio A. Change a
    Celebrity Recording -> Holding rooms offered; switch to Post Mixing -> both gone. A booth can be emptied.
28. Change an all-day M booth to another M booth -> still all day.
29. **A change a room turns down** (Room Check v2 + Move v34): move a booking to a time Studio A is busy on a personal
    calendar -> a DM "⚠️ Studio A turned down this change …" with Change / My bookings; the booking stays on the calendar at
    the new time (not deleted).
30. Cancel / Change from My bookings -> "⏳ Cancelling…" / "⏳ Changing…"; the length note goes after a change or cancel.

## E. Reminders (Reminders v2 - every one comes to you)

31. **Today 4:00 PM:** a DM for each person with a studio session tomorrow (22 Oct 2027), each marked "Test: this reminder
    is for X" (yours unmarked). Needs a 2027-10-22 studio booking made through Jessie - make two or three this morning
    (one with an engineer, one Post Processing for Dilan, one M booth - the M booth should NOT appear at 4 PM).
32. Press **Still on** -> the row becomes "✓ Still on". **Change** -> the Change form. **Free up the room** -> Slack's
    "Free up this room?" -> Cancelled.
33. **Monday 26 Oct 9:00 AM:** the week's bookings (in QA the week of 25–31 Oct 2027: studios, M booths, meeting rooms) per person, with **Keep** / Change /
    Free up the room; Keep -> "✓ Keeping it".
