# Versions

One row per build, newest first. The version numbers (`v167`) are this repo's convention: they are the file names
in `workflows/` and the titles of the commits that imported them. n8n itself keeps the same workflow names
("Project Jessie v2") and only an internal id per save, so **this file is where a version is looked up**.

- **Fixes** says what the build fixed and **which version had the problem**, so a problem can be traced back
  to when it appeared and when it was fixed. Detail (tests, eval numbers) stays in the commit messages.
- **Live** is the time (PHT, UTC+8) it was imported and confirmed; *candidate* means built and tested, not imported.
- Numbers only go up. A fix to a build is the next number, labelled with what it fixes; never a renamed file.
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
| main v177 · Cancel Booking v18 | *candidate* | Cancel cards written by the model (once with an invented room and time), Cancel Booking called before the booking was shown, a Gemini 503 on the cancel yes (QA bugs 5, 6, 8; main v175 / Cancel v17) | Prepare Cancel: code writes the card with a check code over the event; a yes cancels that exact, unchanged booking without the AI. `scripts/sim-prepare-cancel.js` |
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
