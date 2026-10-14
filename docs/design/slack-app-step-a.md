# Slack app — slice 1, step A: the menu and the booking form (dry run)

What step A adds ([`slack-app-v1-scope.md`](slack-app-v1-scope.md)):
- **main v262 (menu):** a greeting, "menu" or "help" - the whole message - gets the menu (**Book a room · My bookings**).
  Everything else goes to the chat exactly as before (typed bookings, changes and questions keep working).
- **Slack Interactions v3 (booking form, dry run):** **Book a room** opens step 1 (date, start, end, what it's for -
  session types from the reference cache); **Find rooms** pushes step 2 (the free rooms that fit, ranked, from Room
  Availability, then the details); **Book** is a **dry run** - the form shows exactly what would be booked (the calendar
  title built by code) and DMs it. **Nothing is written to the calendar.** **My bookings** says it comes next.

Not in step A (next steps): the real booking (step B - Book Session), My bookings / Cancel / Change (step C), Repeats,
the booth and holding-room extras, Localization's studio + booth fields, typed requests opening the form.

## Import (Slack Interactions first, then main)

**1. Slack Interactions v3** - into the existing workflow `PyxSPoAMtSE1gzaH` (open it first; gotcha 38):
- Download it (⋯ → Download) into `workflows/imported/slack-interactions-live-before-v3.json`, then
  `./scripts/check-import before workflows/imported/slack-interactions-live-before-v3.json workflows/slack-interactions-v2.json`
  → MATCHES.
- ⋯ → Import from File → `workflows/slack-interactions-v3.json` → Save → **Publish** "v3 - booking form dry run".
- Nothing to paste (the signature comes from Jessie — Slack Signature).
- Download again into `workflows/imported/slack-interactions-v3-imported.json`.

**2. main v262** - into main (`uVVYVB2M7kxpLleI`); say it in Slack first:
- Download into `workflows/imported/project-jessie-live-before-v262.json`, then
  `./scripts/check-import before workflows/imported/project-jessie-live-before-v262.json workflows/project-jessie-v261.json` → MATCHES.
- Import `workflows/project-jessie-v262.json` → Save → **Publish** "v262 - menu".
- Download again into `workflows/imported/project-jessie-v262-imported.json`.

Don't press the workflow-level **Execute** button on Slack Interactions (gotcha 39).

## Test (in your DM with Jessie)

1. Type **hi** → the menu: *Hi Howard! What would you like to do?* with **Book a room** and **My bookings**.
2. **Book a room** → step 1. The date shows next year (QA). Pick a start and end, **What's it for?** = VO Recording →
   **Find rooms** → "Finding free rooms…" → step 2: the free rooms (the top one *Recommended*), a "Not free then" line if
   a usual room is taken, then Project, Client, Engineer (set to you), Notes.
3. Fill Project (e.g. `project qaw1`) and Client → **Book** → "🧪 Test run - nothing was booked" with the title
   (`QAW1 / <client> / HL`), the room, the time; a DM with the same. **Done** closes the form.
4. Mistakes are caught on the form: an end before the start (step 1); an empty project (step 2).
5. On step 2, **Back** returns to step 1 with your entries.
6. Try **Meeting** (rooms like Likha, a Meeting title, no engineer) and **Booth time** (only M booths).
7. **My bookings** → a DM saying it comes next.
8. The chat still works: e.g. "is studio 7 free friday?" answers as before.

Send screenshots of anything that looks off (or of every step, if easier).

## Built and checked

`python3 scripts/build-slack-interactions-v3.py`, `python3 scripts/build-v262.py` (on the v261 download).
Offline: `node scripts/sim-slice1-a.js` 47 ok (menu on 9 greetings / not on 7 other messages; routes; step 1 from the
cache; step 1 checks; Room Availability input; step 2 for studio / meeting / booth / music / nothing free / calendar
error; step 2 checks and titles); `node scripts/sim-hello-form.js workflows/slack-interactions-v3.json` 20 ok;
`./scripts/test-nodes` (main v262 + Book v108, Cancel v26, Find v8, Move v29) 657 ok; `./scripts/test-gate` 69/69;
check-fromai and audit-model-text clean.
