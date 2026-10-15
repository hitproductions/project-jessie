# Slack app — notes from the first full Slack test (15 Oct afternoon)

Fifteen notes came out of testing slice 1 in Slack. They ship in two builds: **A** (wording, cards, buttons - low risk) and
**B** (behaviour: free stretches, engineer notices, changing details).

## Build A - main v269 + Slack Interactions v17

| # | Note | Where |
|---|---|---|
| 1 | Booking screen: "Your booking is being processed. This takes a few seconds." | Slack Interactions |
| 2 | Change form: the bottom note is gone | Slack Interactions |
| 4 | Typed change / cancel reply: "Here's your proposed change – press *Change* to check the new time." / "Here's the booking – press *Change* to pick the new time." / "Here's the booking – press *Cancel* to cancel it." | main |
| 5 | A cancel, or a change started from a message, shows "⏳ Your cancellation / change is being processed…" under that booking with its buttons hidden until done; a change that fails puts the row back | Slack Interactions |
| 6 | Cancelled and Changed are the card (like Booked); a reply about one booking loses its "Here's…" line once done (a list keeps its heading) | Slack Interactions |
| 7 | The menu's examples in quotes | main |
| 8 | "Or until": 'Only applies if "How many times" is empty.' | Slack Interactions |
| 9 | Series check screen: "Checking availability for each date. This takes a few seconds." | Slack Interactions |
| 10 | Series booking screen: "Processing your series of bookings. This may take a while, so you can close this window for now. You will be notified once finished." | Slack Interactions |
| 11 | The series result DM has Book a room / My bookings | Slack Interactions |
| 12 | My bookings beside Book a room on the booking reply | main |
| 13 | A typed series naming several days ("every tuesday and thursday") starts on the first of them after today, not on the one the date reader resolved | main |

### Import (Slack Interactions first, then main) - Cmd+A then **Delete** (not D) before each import

0. **Slack Interactions v16** first, if not yet re-imported: its 14:33 download had every node deactivated (gotcha 43).
   Download into `workflows/imported/slack-interactions-v16-imported.json` after a clean re-import, or skip straight to v17.
1. **Slack Interactions v17** into `PyxSPoAMtSE1gzaH`: download into `workflows/imported/slack-interactions-live-before-v17.json`
   → clear (Cmd+A, Delete) → Import `workflows/slack-interactions-v17.json` → Save → Publish "v17 - build A: wording, cards,
   buttons" → download into `workflows/imported/slack-interactions-v17-imported.json`.
2. **main v269** into `uVVYVB2M7kxpLleI`: download into `workflows/imported/project-jessie-live-before-v269.json` (should
   MATCH v268) → clear → Import `workflows/project-jessie-v269.json` → Save → Publish "v269 - build A: wording, buttons,
   series first day" → download into `workflows/imported/project-jessie-v269-imported.json`.

### Test (2027 dates)

1. `hi` - the examples in quotes. Book a room → Book → "Your booking is being processed…" → Booked.
2. My bookings → **Cancel** on one → **Cancel booking** → "⏳ Your cancellation is being processed…" under it → the
   ❌ Cancelled card.
3. `make it 3-5pm` after a booking → "Here's your proposed change…" → Change → the row shows "⏳ Your change is being
   processed…" → the message becomes just the ✅ Changed card. Change into a taken time → the row comes back with its
   buttons. No note at the bottom of the Change form.
4. `book studio 7 tomorrow` → Book a room **and My bookings** on the reply.
5. `book likha every tuesday and thursday 10-11am, 4 times` → from **Tuesday**, October 19.
6. A series in the form → "Checking availability for each date…" → Book N dates → "Processing your series of bookings…" →
   the DM with Book a room / My bookings. Or until's hint.

Offline: sim-step-c1 60, sim-series-form 49, sim-typed-series 21, sim-step-c2 59, sim-typed-to-form 70, sim-slice1-a 57,
sim-slice1-b 34, hello 20; main v269 test-nodes 657, gate 69/69, fromai + audit clean; no block repeats an action id.

## Build B - next (Move Booking v31, Cancel Booking v28, Slack Interactions v18)

| # | Note |
|---|---|
| 3 | Change form, room taken: list every free stretch that day ("Free that day: 8:00 – 10:00 AM, 12:00 – 10:00 PM"), not the two nearest slots - Move Booking v31 returns them |
| 14 | Tell the engineer / arranger when someone else books them, and when anyone else on the session changes or cancels it (the booker too) - never the person who did it. During QA the same redirect as Cancel / Move (to Howard unless on ALLOW); a new DEV_REDIRECT for the launch checklist |
| 15 | Change form: "Change other session details" - Project, Client, Engineer (+ Arranger / Project code / Meeting title); checked like a new booking, then the booking updated (Move Booking v31 takes a new title and details) |
