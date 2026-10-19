# Round 8 - plan before building (19 Oct)

Howard's notes from 19 Oct (with Tara's suggestions), reviewed against the live builds (Slack Interactions v24, main v274,
Book Session v111). Nothing here is built yet. Item numbers match the queue.

## What gets built, and where

| Workflow | Build | What changes |
|---|---|---|
| Jessie — Log Booking | **new** | the Jessie Log row and the New Clients row, written after "Booked." instead of before |
| Book Session | v112 | waits for the room's answer only as long as needed; logs through Log Booking; the second (booking) run skips the checks the first run just made; Atmos only in Studio C, Van Recording only in Studio M |
| Slack Interactions | v25 | the form changes and the wording below |
| main | v275 | the greeting, "reset", the "so far" message, the wording below |

Import order: **Log Booking first** (a new workflow - its id goes into Book Session), then Book Session, Slack Interactions,
main.

## 1. Speed (Tara's three fixes)

Measured 19 Oct 10:30: pressing **Book** to "Booked." took **21.7 s** - Slack Interactions ~4 s, Book Session's check run
3.8 s, its booking run 14.0 s.

1. **The room's answer:** checked at about 1.5 s, 3 s and 6 s instead of always waiting 6 s; stops at the first answer. A
   room that turns the booking down is still caught and the booking deleted.
2. **The log sheets after the reply:** Book Session hands the two sheet rows to the new Log Booking workflow and does not
   wait for it.
3. **No second round of checks:** the booking run reuses what the check run found seconds earlier (people, client) and
   only re-checks the calendar for a clash.

Expected: about **12-13 s** instead of 21.7 s.

## 2. The forms

| # | Change |
|---|---|
| 10 | **Room:** the recommended rooms, and right under them an **Another room** dropdown, always shown. Either one: picking from the dropdown clears the ticked room, ticking a room clears the dropdown. No "Another room…" option in the list. Book and Change. |
| 21 | **Vocal booth:** a dropdown, shown whenever the studio takes a booth - set to the usual booth when the session needs one ("Studio B (usual)"), optional with a *No booth* option when the studio records in the room. **Holding rooms:** a dropdown where several can be picked. No tick boxes. |
| 22 | **Events and meetings in studios:** Another room also lists the free studios (never Studio M). Lobby stays the recommended room for events (Airtable Event Priority, already first). |
| 18 | **Atmos Mixing** (one type for every department): *Project title or code* + Engineer + Note. Studio C only - no Another room; if Studio C is taken: "Studio C is taken then - pick another date or time." Book Session refuses any other room. Any type with "Atmos" in its name, so it works before and after the Airtable rename. |
| 23 | **Van Recording** (added in Airtable 19 Oct; Studio M = the mobile studio van): Project title, Client (optional), "Engineer and arranger: pick one or both" (its roles are Post Engineer + Music Arranger). **Studio M only** - no Another room; if Studio M is taken: "Studio M is taken then - pick another date or time." Book Session refuses any other room. One rule for both single-room types: Atmos → Studio C, Van Recording → Studio M. **Studio M never appears under Another room for any other booking** - it is only for Van Recording (decided 19 Oct). |
| 19 | **Localization project code:** a plain text box - any code, booked as typed (in capitals). Pressing Enter on a code that is in Airtable shows its title, client and people and sets the engineer. |
| 20 | **M booth:** *Who is it for?* - a text box, filled in with your first name; the title is "M2 - <what is typed>". If the name is exactly one person in Bookers, they are added and told. |
| 9 | **Meetings and events:** no "Booking this for someone else?" - just the title (meetings also the department). Title "<room chosen> - <title>", e.g. "LOBBY - Launch party" (decided 19 Oct). |
| 13 | **Meeting and event titles:** first letter capitalised ("LIKHA - Post weekly meeting"). Same for the M booth name. |
| 14, 15 | **Every dropdown:** "Select a booking type", "Select an engineer", "Select an arranger", "Select a department", "Select a person", "Select a start time", "Select an end time", "Select a room", "Select a booth", "Select how often", "Select a number", "Select a date". |
| 4 | **Text boxes blank** - no "Write something" (an invisible placeholder; checked in the first test) and no "Anything the session needs". |
| 17 | **While booking, the DM message shows the form's details:** "Your booking details:", the 🗓️ room · date · time from the form, then ⏳ Booking… / ✅ Booked. Same for a series and for Change (what it becomes). |
| 6 | **The Booking… window:** the date and the time on two lines. |
| 7 | **"Hi, I'm Jessie!"** with the two buttons - for hi, reset, "what can you do" (reset answered by code, not the AI). |

## 3. Wording (items 2, 3, 5, 8)

Rule: shortest wording, nothing that says what the form already shows, "booking" not "session" where it means any booking.

### Forms (Slack Interactions)

| Now | After |
|---|---|
| *Step 1 of 2* · when, and what for | *Step 1 of 2* |
| *Step 2 of 2* · room and details | *Step 2 of 2* |
| A room will be recommended to you based on your session details. | You'll get a room recommendation based on the booking details. |
| Leave empty if there's no client. A new name is fine. | *(removed)* |
| Set to you. Change it if someone else is engineering. | *(removed)* |
| As you typed it. / Only engineers are listed (from Bookers). | *(removed)* |
| From the project. Change it if someone else is engineering. | From the project. |
| Set to yours. Change it if the meeting is for another team. / Which team is the meeting for? | *(removed)* |
| Engineer and arranger: pick one or both. | *(kept - Howard asked for it)* |
| Change it and the details below follow. / Leave it empty to keep the session as it is. | *(removed)* |
| Leave empty to keep the current note *(Change form note)* | *(removed - blank)* |
| For every week. The first date's day is ticked. | *(removed)* |
| Up to 16 dates. Each one is checked before anything is booked. | Up to 16 dates. |
| Only applies if "How many times" is empty. | *(kept - says which one wins)* |
| Recommended · usual for Meeting | Recommended |
| Recommended · can do VO Recording · not a usual room | Not a usual room for VO Recording |
| Not a usual room for Meeting - booked as asked. | Not a usual room for meetings. |
| *Studio 7* records vocals in the room - add a booth only if the session needs one. | *(removed - the booth is optional)* |
| Type to search Localization Projects. A new code is fine. | *(removed - a text box now)* |
| New project code - it is booked as typed. | New project code. |
| Your booking is being processed. You may close this window – we'll notify you once it's done. | You can close this window – we'll let you know once it's done. |
| Processing your series of bookings. This may take a while. You may close… | This may take a while. You can close this window – we'll let you know once it's done. |
| ⏳ Your booking is being processed… | ⏳ Booking… |
| ⏳ Your series is being processed… | ⏳ Booking the series… |
| ⏳ Your cancellation is being processed… | ⏳ Cancelling… |
| ⏳ Your change is being processed… | ⏳ Changing… |
| Which department is this session for? | Which department is this booking for? |
| Who's the arranger? Pick one, or *No arranger*. | Pick an arranger, or *No arranger*. |
| "X" isn't in the client list. Did you mean *Y*? Change the client, or press *Book* again to keep "X" as a new client. | Did you mean *Y*? Or press *Book* again to keep "X" as a new client. |
| "X" isn't in the client list. Check the spelling, or press *Book* again to keep it as a new client. | "X" is a new client. Press *Book* again to keep it. |
| This couldn't be booked. Check the details and press *Book* again, or go *Back*. | Couldn't book this. Check the details and press *Book* again. |
| The room list or the calendar couldn't be read just now. Press *Book* again in a moment. | Couldn't check the calendar. Press *Book* again in a moment. |
| That room was just booked by someone else for that time. Pick another room, or go *Back* to change the time. | That room was just taken. Pick another room, or go *Back*. |
| The room turned the booking down - its own calendar shows it is taken then, so it was taken off the calendar. | *Studio 7* is already taken then - nothing was booked. |
| You can't cancel this booking - only the person who booked it, or its engineer or arranger, can. | Only the booker, engineer or arranger can cancel this. |
| You can't change this booking - only the person who booked it, or its engineer or arranger, can. | Only the booker, engineer or arranger can change this. |
| Nothing changed - change the date, time, room or a detail. / Nothing changed - pick a new date, time or room. | Nothing changed. |
| ⚠️ The calendar couldn't be checked just now. Go *Back* and try again. | ⚠️ Couldn't check the calendar. Go *Back* and try again. |

### Chat (main)

| Now | After |
|---|---|
| Hi Howard! What would you like to do? / I book studios and rooms at Hit Productions - tap … / (reset) Hi, I'm Jessie. Ask me about… | Hi, I'm Jessie! |
| Or just type it, like "book studio 7 tomorrow 2-4pm" or … | *(removed)* |
| Anytime! Anything else? | Anytime! |
| I can help with bookings - what would you like to do? | I can only help with bookings. |
| Here's what I have so far: | Your booking details so far: |
| Opens the form with these filled in - only free rooms are offered. | *(removed)* |
| Let's book it with the form. + Pick the date, time and room in the form. | Let's book it with the form. |
| Tap *Book a room* below - the form asks for everything it needs. To change or cancel, open *My bookings*. | Use *Book a room* or *My bookings* below. |
| Here's the booking – press *Cancel* to cancel it. | Here's the booking: |
| Here's the booking – press *Change* to pick the new time. | Here's the booking: |
| Here's your proposed change – press *Change* to check the new time. | Your change so far: |
| Still booking that series - I'll post what was booked here when it's done. | Still booking that series - I'll post here when it's done. |

Kept as they are: the Booked / Cancelled / Changed cards, "Nothing booked for you then.", the engineer / arranger notices,
"Not free then: …", and the error lines that say what to do next (e.g. "That is more than 16 dates - pick an earlier end
date, or a number.").

## 4. Airtable (Howard, PENDING 120) - no build needed

| # | Change |
|---|---|
| 11 | Session Types → **Meeting** → Priority: add Studio F and Studio C after the conference rooms. |
| 12 | Bookers → Department option **P&C** → **People & Culture**. |
| 16 | Bookers → **Alec Elijah Gan** → **Elijah Gan** (initials stay AEG). |
| 18 | Session Types → **Localization Atmos Mixing** → **Atmos Mixing**; engineer roles: Loc / Post / Music Engineer; Priority stays Studio C. |

## 5. Open questions

Answered 19 Oct: events lose "for someone else" (9); studios under Another room for events, Lobby recommended (22).
Still open: the wording table - as written, or strike lines to keep.
