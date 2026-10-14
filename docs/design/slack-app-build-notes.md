# Slack app — build notes

Kept for when the build starts. These were the last two slides of the pivot deck (taken out of the deck on 14 Oct, since
they are for the people building it rather than for stakeholders). The full design is in
[`slack-app-processes.md`](slack-app-processes.md); section 7 there has the details behind the first part.

## What changes for running and testing it

**Running**
- Slack app: Interactivity turned on (one request URL, one search URL for the project-code search); scopes as now
  (`chat:write`, `im:write`, `users:read`); no slash command, no Home tab.
- Both new URLs added to the Cloudflare exemption rule (PENDING 21), and to the uptime monitor (PENDING 15).
- Slack expects an answer within 3 seconds: each click is acknowledged at once ("Booking…"); the work follows and updates
  the form or the message.
- During an outage, a click shows Slack's own error instead of being lost silently.
- Reminders, the weekly message and the approval sweep run on a schedule, outage or not.
- The signature check: the Webhook's Raw Body + n8n's Crypto node (HMAC-SHA256), so no server change is needed.

**Testing and records**
- A new log: every button press and form submission (who, what, result, time) - an Interactions tab beside the Turn Log,
  Log, New Clients and Consent Requests tabs.
- Form flows are tested by people following a script, checked afterwards from the logs (the Slack connector cannot click
  buttons or submit forms).
- Offline checks feed recorded Slack payloads through the same code; layouts are checked in the Block Kit Builder
  (`docs/design/blockkit/`).
- Test dates stay a year ahead: date pickers open on next year during testing; typed messages keep the existing shift.
- Launch notifications switch on in one place (one recipient filter carrying `DEV_REDIRECT`) instead of several.

## From design to build

Not a rebuild from scratch: the back end (Book Session, Cancel, Move, Room Availability, Book Series, the consent engine)
is kept and called by the forms; the chat side gets smaller as each flow moves over. The chat keeps working until each
form is tested.

1. **Set up:** Slack app Interactivity; the Cloudflare exemption for the new URLs; a series id written on new series
   events (for move / cancel whole series).
2. **Build in order:** the menu and Book a room (studios) → results, My bookings, cancel and move → the Studios board and
   typed answers → internal rooms, paired rooms, series → approvals, notices, reminders.
3. **Test each with people:** a script per flow; results checked from the logs; the chat path retires flow by flow.

**Open question:** rooms on neither ranking list (bookable today after a warning and "go ahead") - offer them under
*Show all suitable rooms*, or not in the form?
