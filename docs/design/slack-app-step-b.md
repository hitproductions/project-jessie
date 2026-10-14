# Slack app — slice 1, step B: Book really books

- **Book Session v109 (declined event removed):** when a room turns a booking down, Jessie deletes her own event and says
  so (PENDING 44). Everything else is v108 - the chat books exactly as before.
- **Slack Interactions v7 (booking for real):** Book shows "⏳ Booking…" at once, then calls Book Session **prepare** (every
  check and question the chat has) and books **what prepare returned** - the same two steps as the chat's card and yes.
  A question or problem comes back **on the form, entries kept**: "Did you mean …?" for a client typo (press Book again to
  keep a new name), a Department or Kind-of-booking choice when Book Session needs one, "Who's the arranger? (or No
  arranger)", the room just taken, the room declining. On success the form says **Booked** and the DM gets the result.
  The engineer's and arranger's Slack ids ride on the event ("team:") for the who-can-change rule (used from step C).
  Change / Cancel buttons come in step C.

## Import (Book Session first)

1. **Book Session v109** - into `EUG3sGXkfsJSYIMz` (open it first). Download into
   `workflows/imported/book-session-live-before-v109.json` (should MATCH v108) → Import `workflows/book-session-v109.json`
   → Save → Publish "v109 - declined event removed" → download into `workflows/imported/book-session-v109-imported.json`.
2. **Slack Interactions v7** - into `PyxSPoAMtSE1gzaH`. Download into `…/slack-interactions-live-before-v7.json` → Import
   `workflows/slack-interactions-v7.json` → Save → Publish "v7 - booking for real" → download into
   `…/slack-interactions-v7-imported.json`.

## Test (real bookings, on 2027 dates)

1. **hi → Book a room** → VO Recording, a free time → Find rooms → Project `QATEST1`, Client `Jem Lim`, engineer you →
   **Book** → "Booking…" then **✅ Booked** with `QATEST1 / Jem Lim / HL`; a DM with the same. Check the calendar.
2. **A client typo:** Client `Jem Lin` → Book → "⚠️ "Jem Lin" isn't in the client list. Did you mean Jem Lim?" with your
   entries kept → fix it and Book (or Book again to keep it as new).
3. **A music session** (e.g. Music Mixing, Studio F) → the arranger: pick one or **No arranger** → Book.
4. **A meeting** (Likha) and **an M booth** → Book → Booked.
5. Clean up: cancel the test bookings in the chat ("cancel QATEST1 on <date>") - Change / Cancel buttons come in step C.

Offline: `node scripts/sim-slice1-b.js` 25 ok; `node scripts/sim-slice1-a.js workflows/project-jessie-v262.json
workflows/slack-interactions-v7.json` 55; hello 20; Book Session v109: test-nodes 657, sim-room-decline 6.

## Fixes from the step B test (15 Oct): Book Session v110 + Slack Interactions v8

Found in the step B test (14 Oct, Howard's DM): a booking went through, but the "Did you mean …?" notice read `"" isn't in
the client list. Did you mean **?`, the Booked result was not in the card's format, and the time pickers opened at the
current hour. Typed booking requests still going the chat way is the next build (main v263 + Slack Interactions v9).

- **Book Session v110 (details passed back):** `Return Rejection` kept only the reason and Book Session's sentence for
  the chat, so the form never got the typed client or the suggestions. It now passes them on (typed, suggestions, options,
  askClient, client, staff, guessed, removed - only when the check sent them). The chat reads only the sentence:
  unchanged.
- **Slack Interactions v8 (step B fixes):**
  - **Booked** on the form and in the DM is the card: the title, then `Date:`, `Time:`, `Room:` - nothing else (an
    unusual length still gets its heads-up line in the DM).
  - **Start / End** are a list of half-hour times opening at **8:00 AM**, running to 11:30 PM and round to 7:30 AM -
    every time still bookable, nothing chosen in advance, always Philippine Time.
  - The **notices are never blank**: the form also reads the typed client and the suggestions from Book Session's
    sentence (and the client field), and says it plainly if there is nothing to read.

### Import (Book Session first)

1. **Book Session v110** - into `EUG3sGXkfsJSYIMz`. Download into `workflows/imported/book-session-live-before-v110.json`
   (should MATCH v109) → Import `workflows/book-session-v110.json` → Save → Publish "v110 - details passed back" →
   download into `workflows/imported/book-session-v110-imported.json`.
2. **Slack Interactions v8** - into `PyxSPoAMtSE1gzaH`. Download into
   `workflows/imported/slack-interactions-live-before-v8.json` (should MATCH v7) → Import
   `workflows/slack-interactions-v8.json` → Save → Publish "v8 - step B fixes" → download into
   `workflows/imported/slack-interactions-v8-imported.json`.

### Test (2027 dates)

1. **hi → Book a room:** Start and End open at 8:00 AM, in half hours; scroll down - 11:30 PM, then 12:00 AM … 7:30 AM.
2. Book something with Client `Jem Lin` → the notice reads *"Jem Lin" isn't in the client list. Did you mean Jem Lim?* →
   press Book again → booked as a new client (or fix the name).
3. **Booked** on the form and in the DM: title, Date, Time, Room only.
4. Clean up the test bookings in the chat ("cancel <title> on <date>").

Offline: `node scripts/sim-slice1-b.js` 33 ok (every refusal now goes through Book Session's real Return Rejection,
v110's and v109's); `node scripts/sim-slice1-a.js` 57 (the time list); hello 20; Book Session v110: test-nodes 657,
check-fromai and audit-model-text clean.
