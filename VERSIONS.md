# Versions

One row per build, newest first. The version numbers (`v167`) are this repo's convention: they are the file names
in `workflows/` and the titles of the commits that imported them. n8n itself keeps the same workflow names
("Project Jessie v2") and only an internal id per save, so **this file is where a version is looked up**.

- **Fixes** says what the build fixed and **which version had the problem**, so a problem can be traced back
  to when it appeared and when it was fixed. Detail (tests, eval numbers) stays in the commit messages.
- **Live** is the time (PHT, UTC+8) it was imported and confirmed; *candidate* means built and tested, not imported.
- Numbers only go up. A fix to a build is the next number, labelled with what it fixes; never a renamed file.
- **Two label styles** (29 Sep): `vN (vN-1 fixed)` only when the build repairs a problem the previous build
  introduced (v168 fixed v167's re-sent summary). When it fixes issues *found in use* that the previous build did
  not cause, or adds something, the label says what it does in 2–4 words: `v181 (prompt conflicts)`,
  `v182 (date + room fixes)`. Either way the *Fixes (found in)* column says where each problem goes back to.
- **In n8n, the title carries the current build** (from 2026-09-28): `Project Jessie — v168 (v167 fixed)`,
  `Jessie — Book Session — v55 (v54 fixed)`, so the workflow list shows it at a glance. `verify-ids` and
  `backup-live` use only the part before ` — v<n>`.
- **In n8n, the version itself carries the label too.** Each import is published with a version name, e.g.
  **"v168 - v167 fixed"** (`./scripts/n8n-write activate <id> "v168 - v167 fixed" "<one-line description>"`), so
  n8n's own version history shows which build fixed which. The stable part of the title never changes:
  `verify-ids` and `backup-live` key on it. Labelled from v168 on; earlier versions keep n8n's unnamed entries.

Started 2026-09-28. Earlier builds are in `git log`.

## Main — `Project Jessie` (`uVVYVB2M7kxpLleI`, called `Project Jessie v2` until 2026-09-28)

| Version | Live | Fixes (found in) | Adds |
|---|---|---|---|
| v188 (lowercase initials fix) | 2026-09-29 15:59 | A bare lowercase answer to "Who is the arranger?" ("bp") resolved to no one, and the model then refused it as "not on the staff list" without any check (live QA 29 Sep, execs 16890-16897; initials only counted in capitals since v167) | Initials in any case in a role slot (stop words never); a bare answer to "Who is the arranger / engineer?" is that person; Guard Probe replaces a "not on the staff list" reply no staff check backed (`scripts/build-lowercase-initials.py`) |
| v187 (bug 15 + two-cancel fix) | 2026-09-29 14:46 | Two cancels in one message showed only the last card (PENDING 55, long-standing since the code-written cards, main v177); "is Studio 7 free at 2pm?" answered "from 2:00 PM to 4:00 PM", an end nobody gave (QA bug 15, long-standing) | The first card shows the others as "_Next: ..._" lines; after each yes, Prepare Next Cancel renders the next card with its own code and yes. With only a start time, an availability line says "at 2:00 PM (checked until 4:00 PM)" and asks how long (`scripts/build-two-cancels.py`, `scripts/sim-two-cancels.js`) |
| v186 (move instead) | 2026-09-29 14:02 | A change after "Booked." was recognised (3-5 PM) but the model prepared a second booking anyway, ignoring the prompt notice (v185) | Prepare Booking gets move_instead and refuses with MOVE_INSTEAD, pointing at Move Booking with the exact move; more change words (`scripts/build-move-instead.py`). Verified live 14:09–14:10 PHT: book 2–4 PM → yes → "make that 3pm instead" → MOVE_INSTEAD → move card → yes → Moved to 3–5 PM; one event on the calendar (execs 16680–16689) |
| v185 (move times) | 2026-09-29 13:57 | The change after "Booked." moved 2-4 to 3-4, not 3-5: two "make it 3pm" messages were read together and gave no times, so the model guessed an hour (v184) | Newest message with a time decides; Move Booking's new start/end come from those times; the move confirmation shows them (`scripts/build-move-times.py`) |
| v184 (change after booking) | 2026-09-29 13:52 | Live QA: "Booked." then "actually make it 3pm instead" was prepared as a second booking and clashed with the first (v183) | A change right after a booking is a move of that booking, with the new times (`scripts/build-change-after-booking.py`) |
| v183 (QA bug fixes) | 2026-09-29 13:41 | QA N2: "make it 3pm instead" dropped the length, 2-4 became 3-4 (long-standing); a tool instruction reached the requester (bug 3, long-standing); a model-written cancel card showed an Event ID (bug B); a series summary's December Tuesdays said "(Mon)" (bug 19) and had no Booked by (bug 14) | Start/end changes keep or set the length; any sentence naming "the requester" or a tool is dropped; series dates written from Expand Series; a card from Cancel Booking shown as written (`scripts/build-qa-fixes-29sep.py`) |
| v182 (date + room fixes) | 2026-09-29 13:21 | Live QA 29 Sep ("tomorrow at Salin"): the model sent 1 Oct on follow-up turns though "tomorrow" was 30 Sep (v181) - Prepare Booking now uses the one date under discussion when the requester never typed the model's date; "And which day is it for?" added to a greeting (v181); "from 12:00 AM to 12:00 AM" for an all-day clash (v181) | `scripts/build-date-room-fixes.py`, `scripts/sim-date-room-fixes.js` |
| v181 | 2026-09-29 09:45 | ChatGPT review of v180: prompt/notice conflicts (1-6) | Cancel notice no longer says "call Cancel Booking" when the direct cancel declined; Clients lookup for unlabelled names; session type only for booking lookups; series exempt from Prepare Booking; List Events 2-week default removed; "not found" is not "deleted" (`scripts/build-prompt-fixes.py`) |
| v180 | 2026-09-29 04:53 | v179's series check missed dates written without a year ("Dec 7") | Series notice counts dates with or without a year |
| v179 | 2026-09-29 04:50 | v178's series check missed dates written on one line | Series notice counts dates anywhere after "Dates:" |
| v178 | 2026-09-29 04:44 | QA bugs 16-18 (v177): "Friday next week" read as this Friday and "every Tuesday" as a date; a repeated yes retried and called the room taken; a series yes re-sent the summary | Gate date fixes; "That's already booked" in code; series-approved notice to the model. `scripts/sim-repeat-yes.js` |
| Book Session v58 · Expand Series v4 | *candidate* (with main v177) | Wordy fixed replies: summary notes, series intro and repeated times (Book v56, Expand v3) | "Assumed 1 hour (usual for VO Recording).", "… isn't a usual VO Recording room - booking it as asked."; series: no intro, time once |
| main v177 · Cancel Booking v18 | *candidate* | Cancel cards written by the model (once with an invented room and time), Cancel Booking called before the booking was shown, a Gemini 503 on the cancel yes (QA bugs 5, 6, 8; main v175 / Cancel v17) | Prepare Cancel: code writes the card with a check code over the event; a yes cancels that exact, unchanged booking without the AI. One-line confirmation "Book it? Reply yes or no." (was two lines; the old form still confirms); greetings one line, questions only the question, shorter error and "Assumed…" lines. `scripts/sim-prepare-cancel.js`, `scripts/sim-short-marker.js` |
| main v176 · Open v11 · Finalize v10 · Sweep v2 · Book Session v57 · Move v25 | *candidate* | Consent: first-word approvals and newest-row guessing, a booking "yes" approving a consent (main v175); room_override skipping every recurring event (Book v56); Finalize trusting a stale row, deleting the hold before booking and carrying on after errors, one expired row per sweep, timeout messages saying "OK'd" (Finalize v9, Sweep v1) | Holds are no longer deleted (standing holds "Show as available"); Finalize re-reads, books, writes only if still PENDING; `scripts/sim-consent.js`. Needs 3 sheet columns + 4 holds set to available |
| Book Session v56 · Room Availability v11 · Find v6 · Cancel v17 · Move v24 | 2026-09-29 03:25 | Untitled or partial titles matched for cancel/move; all-day events read as 08:00 Manila; a second calendar page read as free; unflagged room attendees dropped on move (review 29 Sep, all in the builds before) | `scripts/sim-booking-review.js` |
| v175 | 2026-09-29 03:07 | Get Booker was a live Airtable read on every message, 1–4 s (v174 and earlier) | Get Booker served from the reference cache (sender matched on Slack User ID); cache block moved in front of it. Staff/authority changes take up to 15 min to apply (accepted by Tara). `scripts/sim-get-booker.js` |
| v174 | 2026-09-29 02:58 | v173 canvas: cache nodes on top of the Gemini / Memory nodes (v173) | Layout only |
| v173 | 2026-09-29 02:56 | Three Airtable reads (Rooms, Session Types, Bookers) on every message, ~3.3 s (v172 and earlier) | Reference cache (with Refresh Reference Cache v2); imported by Tara without sticky notes and the two disabled nodes |
| v168 | 2026-09-28 18:25 | After a "no", the refused summary re-sent unchanged instead of asking what to change (v167, live test) | — |
| v167 | 2026-09-28 17:52 | Invented engineer names (v166 and earlier: the prompt asked for a full name, role and initials); garbled project / client copies; "which studios" leaving out the M booths (v165); a refusal's instructions pasted into the reply (v165); "10am-12nn" booked as 10–11 (v166); "no client, it's client work" read as a client called "work" (v167 draft) | Engineer, arranger, project, client and times read from the requester's own words |
| v166 | 2026-09-28 16:28 | Claimed "I've asked the holder" with nothing behind it (PENDING 26) | **Prepare Booking on for everyone** (built across v163–v165); the in-house arranger notice |
| v165 | *candidate → v166* | The Booked For notice quoting three words (PENDING 41) | Client check and booking type in the prepared summary; the holding-room note (PENDING 30) |
| v164 | *candidate → v165* | Summary turns 4.5 s slower (v163); Localization titles picking up the client (v163); no question when no date was named (QA E1) | Placeholders in the prompt's examples; prompt trims |
| v163 | *candidate → v164* | Summary drift and missing titles (v160, eval 27 Sep) | First Prepare Booking build |
| v162 | 2026-09-28 11:33 | "Every room free" on a padded time in List Events (v160); Room Availability's instruction leaking into replies (v160) | The four eval decisions (for-name as client, typed new clients, heads-up only, studios vs rooms) |
| v161 | 2026-09-28 10:58 | Client room preferences guessed from record ids (v160) | Clients optional; new clients allowed and logged |

## Book Session (`EUG3sGXkfsJSYIMz`)

| Version | Live | Fixes (found in) | Adds |
|---|---|---|---|
| v64 (bug 9 fix) | 2026-09-29 15:08 | Summaries missing the Booking Type line when the model sent none: Check Conflicts worked it out and wrote it to the event, but Render Summary showed the model's empty input (QA bug 9, since Prepare Booking v51; seen again live 29 Sep, exec 16795) | final_booking_type from Check Conflicts is what the summary shows (`scripts/build-booking-type-line.py`, `scripts/sim-booking-type-line.js`) |
| v63 (bugs 11 + 13 fix) | 2026-09-29 14:54 | With no room named, the model picked one itself, sometimes a taken one, and summarised it as if asked for (QA bugs 11/13, long-standing) | Prepare mode: when the requester's messages name no room, the highest-ranked free room for the session type (Priority in order, then Last Resort; never conference rooms or the lobby); the summary notes "I picked Studio 7 ... OK with that room?"; none free -> NO_ROOM, offer other times (`scripts/build-room-suggest.py`, `scripts/sim-room-suggest.js`) |
| v62 (move instead) | 2026-09-29 14:02 | With move_instead set, prepare mode prepared a new booking (v61) | MOVE_INSTEAD: nothing prepared; Move Booking named with title, date and new times |
| v61 (own booking) | 2026-09-29 13:52 | A clash with the requester's own booking offered other rooms (v60) | Says it overlaps your own booking and asks whether to move it |
| v60 (instruction leak) | 2026-09-29 13:41 | The two "not the usual room" refusals ended with instructions the model pasted to users (bug 3) | with main v183 |
| v59 (room fixes) | 2026-09-29 13:21 | Conference room taken: nothing offered, so the model named rooms that were also taken (v58) - the other conference rooms free in that window are offered; an all-day clash is said to be "all day" (v58) | with main v182 |
| v55 | 2026-09-28 17:52 | Near-miss engineer names refused instead of resolved (v54); no role on the engineer line (v54); External/Personal and the client asked a turn apart (v54); "last Monday" answered as a missing date (v54) | Name, role and initials filled from Bookers |
| v54 | 2026-09-28 16:28 | No arranger asked on Music sessions (PENDING 29); booking over your own booking asked you for consent (PENDING 28) | In-house arrangers as booked-for and client |
| v53 | 2026-09-28 15:20 | Studio E's dead calendar id (PENDING 43); "room taken" re-offering the same slot (PENDING 23) | Client check and booking type (prepare mode) |
| v52 | 2026-09-28 15:02 | Localization titles (v51) | Staff list reused from main |
| v51 | 2026-09-28 13:58 | — | Prepare mode (the Prepare Booking engine) |
| v50 | 2026-09-28 11:33 | Padded-time conflict query checking the wrong day (v49, PENDING 51) | Tech requirements no longer written |
| v49 | 2026-09-28 10:58 | — | Clients optional; new clients logged to the New Clients sheet |

## Other sub-workflows

| Workflow | Version | Live | Fixes (found in) |
|---|---|---|---|
| Cancel Booking (`bAyDw7udhmY0NL38`) | v19 (cancel card fix) | 2026-09-29 13:41 | An unconfirmed call answered NOT_CONFIRMED and told the model to show the booking itself: it wrote its own card for a booking the requester could not cancel, and the refusal came only at the yes (v18, bug A). Now it is Prepare Cancel: ownership first, then the code-written card |
| Move Booking (`t7lwR2km4tfN8DbM`) | v22 | 2026-09-28 16:28 | Self-consent on your own booking (PENDING 28) |
| | v21 | 2026-09-28 15:20 | Studio E id (PENDING 43) |
| | v20 | 2026-09-28 11:33 | Padded times on the new window (PENDING 51) |
| Room Availability (`e7tBQB458nstrqei`) | v10 | 2026-09-28 15:20 | Studio E id (PENDING 43) |
| | v9 | 2026-09-28 11:33 | "Every room free" on a padded time (v8, PENDING 51); studios vs rooms |
| Find Booking (`yzirq12O227VTFp8`) | v5 | 2026-09-28 15:20 | Studio E id (PENDING 43) |
| | v4 | 2026-09-28 11:33 | Padded day query (PENDING 51) |
| Cancel Booking (`bAyDw7udhmY0NL38`) | v16 | 2026-09-28 11:33 | Padded day query (PENDING 51) |
| Expand Series (`hkx9PXcgW9nrzY2a`) | v3 | 2026-09-28 15:02 | — (series instructions moved out of the prompt) |
| | v2 | 2026-09-28 11:33 | Padded dates (PENDING 51) |
| Book Series (`UAwFoifgkfL1xNP2`) | v3 | 2026-09-28 11:33 | Padded dates and times (PENDING 51) |
