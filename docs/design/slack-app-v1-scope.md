# Slack app — v1 scope

What the first build includes, what comes next, and what waits. Every feature in
[`slack-app-processes.md`](slack-app-processes.md) is sorted here, each in its **simplest version** - the test for each
was: is it possible, is it needed, what is the simplest thing that does the job.

**The rule that makes this safe:** the chat keeps working throughout. A flow moves to forms only when its slice is built
and tested; until then it stays on today's chat path. So leaving something out of v1 loses nothing - it just stays in chat
a little longer.

Status: proposed 14 Oct, for review.

## v1 - the everyday booking loop

Enough to move the most-used flows (book, see, cancel, move) off the chat.

| Feature | Simplest version in v1 |
|---|---|
| **Menu** | "What would you like to do?" + **Book a room · My bookings** (Studios joins with the day board in v1.1). Shown on a greeting, on anything not understood, and on "menu". |
| **Typed request → form** | The first message pre-fills the form with what today's code already reads (date, time, room, session type, project, client, engineer). Nothing is booked from it. |
| **Book a room - step 1** | Date, start, end, What's it for? (session types + Meeting / Event / Booth time). |
| **Book a room - step 2** | Room: free rooms that fit, ranked from Airtable, top one recommended; Last Resort rooms listed only when no usual room is free; a note for usual rooms not free then. Localization Dubbing offered as studio + booth pairs. Then the details. **Book** is the confirmation. |
| **Details** | Project (text) · Client (text, checked on Book: "Did you mean…?", new names to the New Clients sheet) · Engineer (people picker, defaults to you; required for arrangers / Marketing) · Arranger (music sessions) · Kind of booking (only for departments with a choice) · Project code (text, Localization) · Meeting title (meetings, events) · **Booking for (optional people picker)** · Notes. |
| **Title** | Built by code from the fields (ALL CAPS project for post and music; Localization code as written; `ROOM - title` for meetings). |
| **After Book** | The form shows "Booking…", then **Booked** (after the room's answer is read back) or the problem with entries kept. The DM gets the result with **Move · Cancel**. A room that declines: Jessie deletes her event and says so, with **Pick another room or time**. |
| **My bookings** | Next 7 days: bookings you made (with Move · Cancel) and ones you engineer (no buttons). |
| **Cancel** | Slack's "Are you sure?" pop-up, then the message updates to Cancelled. |
| **Move** | A form pre-filled with date, start, end and room; the new time is checked first. |
| **Typed cancel / move** | "cancel my friday booking" → the matching bookings, each with Move · Cancel. "make it 3pm" → opens the Move form pre-filled. |
| **Typed questions** | Today's code-written availability answers, plus one **Book** button per free room (opens the form pre-filled). Room facts, people, session types answered as today. Off-topic and not understood → the menu. Each question reads only itself and the previous one. |
| **Behind the scenes** | Interactions log; date pickers open a year ahead during QA; one new Slack URL (Interactivity) in the Cloudflare rule. |

## v1.1 - next, once v1 is proven

| Feature | Note |
|---|---|
| **Series** (Repeats in step 1, dates list in step 2) | Stays on the chat path until then - it works there today. |
| **Approvals as buttons** (priority and shared-booth requests; engineer may answer; withdraw) | Rare. Open decision below. |
| **Studios day board** (third menu button) | Typed "what's free…" covers it in v1. |
| **Holding rooms** checklist (Celebrity Recording) | Rare; stays on chat. |
| **Engineer notice** on every new booking | Needs the shared recipient filter (one `DEV_REDIRECT`). |
| **Reminders** (studio day-before; weekly booths and meeting rooms, standing holds) | New feature, builds on the same filter. |
| **⋯ at the end of results** (Book another, My bookings) | The menu covers it in v1. |

## Later - nice to have

- Move or cancel a whole series (needs a series id on each event).
- "See all upcoming" (v1 shows 7 days).
- Department bookings view for coordinators.
- Book again (copy a past booking).
- "Got it" on engineer notices; Withdraw if approvals land without it.
- One-tap "Move to 3:00–5:00 PM" (v1 opens the Move form instead).
- Updating every old message when a booking changes (v1 updates the one clicked; a click on an old message re-checks the
  calendar anyway).
- The ⋯ room options: *Show all suitable rooms* and *Pair with a vocal booth* (rare; chat covers them meanwhile).
- "Your recent clients" beside the client field; type-ahead search.

## Simplifications made in this pass

| Designed | v1 | Why |
|---|---|---|
| "Booking for someone else" behind a checkbox that redraws the form | An optional people field, always shown | No redraw; one less moving part |
| "Booked" at once, then a status line that updates when the room answers | "Booked" shown after the room's answer | One update instead of two; the wait is a few seconds on "Booking…" |
| Three menu buttons | Two (Studios comes with the day board) | Nothing behind the third button yet |
| One-tap typed move | Typed move opens the Move form | Same check, one screen fewer |
| Rooms on neither ranking list (bookable after a warning) | **Not offered in the form** | Rare; the chat path still allows it (settles the open question) |

## Back-end changes v1 needs

- **Book Session:** accept a form booking directly (no AI, no card) - fields in, title built from them; delete its own
  event when the room declines (PENDING 44).
- **Cancel / Move:** none - both already take the exact booking id.
- **Room Availability:** free rooms for a window, ranked for a session type - it already answers this; confirm the shape.
- **Main:** route a typed request to "pre-fill the form" instead of the chat booking flow, flow by flow.
- **New workflow:** `Jessie — Slack Interactions` (clicks and form submissions), with its own version numbers.

## Before the first slice

1. **"Hello form" test:** a button opens a one-field form; Submit says "got it" and then posts a message - proves the
   Cloudflare path, the signature check, the 3-second reply and the year-shifted date picker.
2. **Airtable data check:** a Booking Defaults row for every department; complete Session Types rankings; Client Name on
   every Localization project; Paired with on the studios.

## Decisions for review

1. **Approvals in v1 or v1.1?** v1.1 is proposed: they are rare, and the chat path keeps working - but it has known bugs
   (PENDING 27, 78-80). If priority requests matter early, approvals move up.
2. **The simplifications above** - agree, or keep any designed version.
