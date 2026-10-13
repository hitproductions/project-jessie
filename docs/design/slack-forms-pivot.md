# Slack forms pivot — review (13 October 2026)

Status: proposal for review. Decided so far: move toward structured input after the first natural-language message.

## Why: the evidence

**The wide test (13 Oct, main v261 on Claude Haiku 5.5)** - 20 scenarios, ~45 messages in varied phrasing (Taglish, typos,
shorthand, vague requests, durations, two requests at once, mind changes, off-script). **8 passed, 12 failed or partial.**
Full log: `docs/qa/wide-test-2026-10-13.md`.

| Failure class | Count | Examples | Would a form fix it? |
|---|---|---|---|
| Details carrying over from one request to the next | 6 | An earlier "vo rec" made a later "post mix" ask "VO Recording or Post Mixing?" - and the answer looped. A vague "I need a room tomorrow afternoon" got a card with the project and time of a request just declined. "What's free tomorrow afternoon?" was answered for 10-11 AM, a window left over from before. "thanks! what's the weather?" got a "Studio 7 is already booked" warning | Yes for bookings - each form submission stands alone. Availability questions need the same isolation |
| Free text not read | 4 | "bukas" (tomorrow), "stdio 7" (became Studio F), "9am for 2 hours", two bookings in one message (one dropped) | Yes - pickers and selects, nothing parsed |
| The model's wording around code | 3 | Bookkeeping in replies ("The session type is VO Recording (typical duration 60 minutes), and it's Audio Post"), statement-shaped asks that bypass the code-written question, details asked before the time | Yes - every prompt and error is code's |

**What held** - everything code decides once the details are right: cards, the yes/no gate, taken rooms and alternatives,
refusing to double-book, cancel and move from a loose reference, internal rooms, a recurring series.

**The pattern across the last weeks** - fixes that moved a job from the model into code have held (cards, availability
answers, date rules, booking questions); fixes that patched the model's wording went in circles (v247-v257, about ten builds,
one phrasing at a time). The carry-over between requests is not one bug: each earlier fix drew the boundary between requests
for one case, and the next phrasing crossed it. A form draws that boundary by design.

## Recommended shape (hybrid)

| Step | What happens | Who decides |
|---|---|---|
| 1. First message | Natural language, as now ("book studio 7 tomorrow 2-4pm for jem lim") | Code reads what it can (Gate Context date, Booked For time / project / client / engineer, rooms); the model only routes intent: book, cancel / move, question |
| 2. Booking | Jessie replies with a **"Book a session" button** (or opens the form straight away from a slash command / shortcut); the form opens **pre-filled** with what step 1 read | Code |
| 3. The form | Date (date picker) · start and end time (time pickers) · studio (select, the usual rooms for the session type first) · session type (select, from Airtable Session Types) · project (text) · client (select with search over Clients, or "none", or a new name) · engineer (select from Bookers, defaulting to the requester when they are one) · notes | Code validates on submit |
| 4. Submit | Book Session runs as today (every guard, availability, consent engine); the reply is the result: "Booked." with the details, or the problem shown **inside the form** next to the field (taken room -> the free times / other studios) | Code |
| 5. Cancel / move | "My bookings" list (App Home tab and/or a DM message) with **Cancel** and **Move** buttons per booking; Move opens a small form (new date / time / room) | Code |
| 6. Questions | "is studio 7 free friday?" stays natural language, answered by Room Availability's code layout - but **without inheriting booking context** (fix D1/D2/F2) | Code answers; model routes |

What it removes: carry-over between requests (each submission is self-contained), parsing of dates / durations / typos /
Taglish, the confirmation card and the yes (the submit is the confirmation), model-worded questions. What stays model-driven:
recognising what the first message wants, and free-form chat.

## What to check before building (the pivot list)

**Slack app (owner account - not a code change)**
- Turn on **Interactivity & Shortcuts** and set its Request URL (a new n8n webhook path). Optional: a **slash command**
  (`/book`) and a **global shortcut** ("Book a studio") - both give a `trigger_id`, so the form opens immediately without a
  message round trip. Optional: the **App Home** tab (a "Book" button and the requester's bookings, always there).
- Scopes: `commands` (slash command), `chat:write`, `im:write` (already), `users:read` (already, for names).
- A modal can only be opened with a `trigger_id` from a click / command / shortcut, within **3 seconds**. A plain DM message
  cannot open one: step 2 needs a button, or the user starts from `/book` or the shortcut.

**n8n**
- The Slack Trigger node handles events, not interactivity payloads (`block_actions`, `view_submission`, `shortcut`, slash
  commands). Those need a **Webhook node** + **signature verification** (HMAC-SHA256 of the raw body with the signing secret,
  in a Code node - may need `NODE_FUNCTION_ALLOW_BUILTIN=crypto` on the server: IT).
- **3-second rule:** `view_submission` must be answered within 3 s, or Slack shows an error. A full Book Session run (calendar
  read, Airtable, the 6 s room re-read) is longer. Pattern: answer at once with `response_action: "update"` (a "Checking..."
  view) or `"clear"`, then post the result as a DM / update the view with `views.update`; or run only fast checks (field
  shape, required fields) inside the 3 s and the rest after. Validation errors next to a field (`response_action: "errors"`)
  are only possible within the 3 s.
- Dynamic fields (studios free on the picked date, client search) need `block_suggestion` (external selects, another
  webhook answering within 3 s) or a two-step form (`views.update` after the date is picked).
- Reuse: Book Session (prepare + book) is called directly by the form handler - no agent - so every guard stays; Move /
  Cancel Booking the same; Render Summary's card is not needed (the form is the confirmation).

**Cloudflare / outages (PENDING 21)**
- The new interactivity / slash-command URLs must be added to the **Cloudflare exemption rule**, or Slack's requests get 403 -
  the September outage mechanism. Add them to the external monitor (PENDING 15) too.

**QA / testing**
- Buttons and forms **cannot be clicked through the Slack connector** used for test rounds so far: form flows need human
  testers, or test payloads posted to the n8n webhook (n8n access is restricted - IT). Plan the QA rounds around people.
- The QA year shift: a date picker offers real dates (2026); submissions must be shifted like Gate Context does, or the year
  shift dropped for the form path.
- Time pickers are in the user's Slack time zone; convert to Manila explicitly.

**Product / process**
- Internal rooms (M booths, conference rooms, Lobby) need their own small forms (owner / meeting title, no session type).
- Series: repeat fields (weekdays, number of weeks or an end date) - Prepare Series / Book Series stay the backend.
- **Consent engine:** approve / decline as **buttons** in the incumbent's DM would also fix PENDING 79 ("cleared with
  <name>" looping) and 78 (names shown in the button message).
- End-user SOP and the orientation material change (screenshots of the form).
- Mobile Slack supports modals and date / time pickers.

## Suggested order

1. Owner: Slack app Interactivity (+ `/book` command), Cloudflare exemption for the new paths; IT: crypto for signature checks.
2. Build the booking form (studio bookings first), wired to Book Session; human-test it.
3. Cancel / move buttons on "my bookings" (covers PENDING 100).
4. Availability questions without inherited context; then internal rooms and series in the form.
5. Consent approve / decline buttons.
Meanwhile the chat path keeps working; the form path replaces it per flow once tested.
