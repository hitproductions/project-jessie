# Slice 2 — approvals and shared rooms (design, 21 Oct 2026)

**Built 21 Oct, not imported yet** (answers below in *Decided 21 Oct*). Was: for review before building. What a request looks like from each side in the Slack app, what stays from the consent engine
that is already live, what changes, and the build order. Earlier decisions this builds on: `slack-app-processes.md` section 6
(agreed 13 Oct), `consent-engine.md` (the engine), `mbooth-approval.md` (shared booths).

**Decided already, not reopened here:**
- Who may ask stays as it is today (20 Oct). **Priority requests** only for someone with Bookers `Authority` Dept Head,
  Client Booking or HAIST Dev, only when their booking type's `Preemption Rank` (Airtable Session Types) is strictly higher
  than the booking in the room, and only when one booking is in the way. **Shared booths**: anyone, for an M booth whose only
  conflict is a standing (recurring) hold.
- One Google Sheet row per request (`Consent Requests` tab), Consent Sweep every ~10 min, Finalize that acts only once, the
  Sheet edit as the break-glass path. No tentative bookings.
- Buttons replace typed replies on every side; every message updates in place when the request ends.
- A priority request goes to the booking's **booker and engineer**; the first answer decides (PENDING 80).
- **During testing every request message goes to Howard**, the QA roster included (21 Oct), marked who it is really for.

## What happens today (live)

- The booking form only offers free rooms, so it never opens a request. M booths with a standing hold are left out of the
  form.
- The engine is live but reached only through the old typed chat: the holder replies "yes" / "no" in their DM, main's
  Consent Router reads it; the requester types "cleared with <name>". Known faults: blank names in the messages (78), the
  "cleared with" reply going in circles (79), the request reaching the booker only (80), the same request opening twice (27);
  the deadlines have never run live (37).
- Two things already work and are kept: when the incumbent's booking is **changed** (Move Booking), Move's tail hook finds
  the request and calls Finalize, which books the requester into the freed room; an M booth request that gets no answer by
  its deadline is booked for the requester by the Sweep.

## 1. Asking - the booking form (requester)

Step 2 is unchanged until someone opens **Choose a different room**. Its dropdown gets a second group under the free rooms:

```
Choose a different room
  Available
    Studio 3
    Studio 4
  Booked – ask to use
    Studio F · VO Recording, until 4:00 PM
    M4 · Jem's standing hold
```

- Only rooms a request can actually be made for appear there (the rules above, worked out for this person, this time, this
  booking type). Everything else that is taken stays out, as now. A Standard user sees M booths with holds only.
- Picking one redraws the form with one line under it and the button renamed:

  > 🔒 *Studio F is booked then* (SONG / Jem Lim / DR, 2:00 – 4:00 PM). Jessie will ask its booker and engineer; they have
  > until *Thu, Oct 22, 3:00 PM* to answer.
  >
  > [ **Send request** ]

  For an M booth: "M4 is held for Jem every Thursday. Jessie will ask Jem; if there's no answer by *Thu 10:00 AM*, it's
  booked for you."
- Everything else on the form (details, engineer, notes) is filled in as for a booking - the request carries the whole
  booking, so it can be placed later without asking again.

After **Send request**, the window says "Request sent." and the DM gets the requester's card:

> ⏳ *Requested - Studio F*
> SONG 2 / Netflix / HL · Thu, Oct 22 · 2:00 – 4:00 PM
> Asked: Daryl Reyes (booker), Angelo Villegas (engineer) · until Thu 3:00 PM
>
> [ I've cleared it with them ] [ Withdraw request ] [ Pick another room ]

- **I've cleared it with them** - for when they agreed in person (see 3, open question B). Slack's confirm pop-up first.
- **Withdraw request** - ends it (new status `WITHDRAWN`); the other side's messages update ("Withdrawn - nothing to do").
- **Pick another room** - opens the form at step 2 for the same date and time; the request stays open until withdrawn.
- Asking again for the same room and time shows the open request instead of a second one (27).

## 2. Answering - the booker and engineer (priority request)

Both get the same DM (in testing: to Howard, marked "Test: this request is for Daryl Reyes"):

> 🙋 *Celeste Cruz asks for Studio F* · Thu, Oct 22 · 2:00 – 4:00 PM
> For *Celebrity Recording* (SONG 2 / Netflix), which takes priority over your VO Recording.
>
> Your booking: *SONG / Jem Lim / DR* · 2:00 – 4:00 PM
> Free for you that day: Studio F 4:00 – 7:00 PM · Studio 7 2:00 – 6:00 PM · Studio 4 all day
> Please answer by *Thu 3:00 PM* - no answer keeps your booking.
>
> [ Move my booking ] [ Give it up ] [ Keep my booking ]

- **Move my booking** opens the Change form on their booking, with the free times above as the suggested room / time. When
  the change goes through, Move's tail hook places the requester (already live). If they close the form without changing,
  nothing happens and the buttons stay.
- **Give it up** cancels their booking (confirm pop-up) and places the requester at once. (New - see open question A.)
- **Keep my booking** (confirm pop-up) ends the request: `REJECTED`, which is final - the requester cannot override it with
  "I've cleared it with them".
- Whoever answers first decides; the other person's message updates: "✓ Daryl Reyes moved the booking - nothing to do".

## 3. Shared booth (M booth with a standing hold) - the holder

> 🙋 *Celeste Cruz asks to use M4* · Thu, Oct 22 · 10:00 AM – 12:00 PM - during your standing hold.
> If you don't need it that day, let them use it. *No answer by Thu 10:00 AM: it's booked for them.*
>
> [ Let them use it ] [ Keep it ]

- **Let them use it**: that day's hold is taken off (that one date only) and the requester is booked - Finalize's M booth
  path, already live.
- **Keep it**: `REJECTED`, final.
- No answer: the Sweep books it for the requester at the deadline (as today); the holder's message updates to say so.

## 4. How a request ends - every message updates in place

| Ends as | Requester's card | Booker / engineer / holder |
|---|---|---|
| Booked (moved, given up, let use, cleared, or M booth timeout) | ✅ *Booked.* card with Change / Cancel, Book another / My bookings | "✓ Done - Studio F is Celeste's from 2:00 PM" (+ their moved booking, if moved) |
| Kept (`REJECTED`) | ❌ *Daryl Reyes is keeping Studio F.* + the free rooms then, **Pick another room** | "✓ You kept it." |
| No answer, priority (`EXPIRED`) | ⌛ *No answer by Thu 3:00 PM - Studio F stays booked.* + **Pick another room** | "⌛ The request ended - your booking stays." |
| Withdrawn | "Withdrawn." | "Withdrawn - nothing to do." |
| Could not be placed (`FAILED`: the room was taken again by then) | ⚠️ *Couldn't book Studio F after all* - why, + **Pick another room** | their booking as it is now |

Engineer / arranger notices for the placed booking go out as for any booking.

## 5. Open questions (for Howard)

- **A. "Give it up"** on a priority request: offer it (cancel their booking, place the requester at once)? Recommended -
  today the only way to agree is to move, and someone who no longer needs the room would have to pick a time anyway.
- **B. "I've cleared it with them"** (they agreed in person): the requester still needs the room freed. Recommended: the
  button opens a small form - *"Where does their booking go?"* with the incumbent's free times, or *"They gave it up"* -
  and Jessie moves or cancels it with the request's authority, places the requester, and tells the booker and engineer
  what was done and by whom. (The live engine's attest path assumes the slot was agreed in a typed chat, which no longer
  exists.) Alternative: drop the button and keep only the booker's own answer.
- **C. The Change form**: should changing an existing booking into a booked room also be able to ask (the same group in
  its Room dropdown)? Recommended: **later** - the Book form first; Change keeps saying the room is taken.
- **D. Deadlines** stay as they are: priority - 24 h, but no later than 1 h before the session; M booth - same day 3 h,
  tomorrow 10:00 AM on the day, later 24 h, never past the start. Shown on every message.
- **E. Requests for a series** (Repeats on): not in this build - a series only books free dates, as now.

## 6. What gets built (no imports until your tests are done)

| # | Workflow | Change |
|---|---|---|
| 1 | Room Availability v23 | Each taken room comes back with its booking (title, times, booking type, booker / team ids, standing hold or not) next to today's busy list, so the form can tell which ones may be asked for. Nothing else changes. |
| 2 | Slack Interactions v37 | The *Booked – ask to use* group (same rules as Book Session's `Decide Preempt`, from the cache's ranks and Bookers authority); Send request; the requester's card; the new buttons (Move my booking, Give it up, Keep my booking, Let them use it, Keep it, I've cleared it with them, Withdraw, Pick another room) with confirm pop-ups; updates in place. |
| 3 | Open Consent Request v12 | Messages written in code from the row with real names (78); booker **and** engineer (80); a second request for the same room and time returns the open one (27); every message to Howard while testing (ALL_TO_DEV, inert at launch like Reminders); the message timestamps kept on the row so they can be updated. Built on the live 29 Sep snapshot - the unimported v11 candidate is not used. |
| 4 | Finalize Consent v-next, Consent Sweep v3 | Update every message of the request when it ends (table in 4); Give it up; WITHDRAWN respected; the Sweep's M booth booking and expiry update the messages too. |
| 5 | Book Session v120 | A request opened from the form answers with the request id, deadline and who was asked, for the requester's card (today it answers with a chat sentence). |
| 6 | main | Nothing new. Its typed Consent Router stays for any old open row, then goes once no row is open. |

**The Sheet** (`Consent Requests` tab) needs four more header cells at the end, typed by hand before import: `Approver 2`,
`Approver 2 Name`, `Messages` (where each DM is, for updating it), `Withdrawn At`.

**Testing** (all messages come to you): ask for a room booked by a lower-priority type as a Dept Head / HAIST Dev, and
answer it from the booker's message (move, give up, keep); the engineer's message updating after; an M booth during a hold
(let use, keep, and no answer - the timeout test owed since PENDING 37); withdraw; asking twice; a Standard user sees M
booths only. Offline, every piece gets a sim before it reaches you.

**Size:** about three builds - (1)+(3) the engine side, (2)+(5) the form, (4) the endings - each imported in that order.

## Decided 21 Oct (Howard) and built

- **A** Give it up: yes (for an M booth holder, *Let them use it* already gives up that day). **B** I've cleared it with them on a
  priority request: the small form - *They'll move it – I'll pick where* (their booking's Change form, changed as its booker) or
  *They gave it up* (cancelled as its booker); on a shared booth it books at once after a confirm. **C** the Change form: later.
  **D** deadlines unchanged. **E** no requests for a series.
- Built: Jessie — Request Messages v1 (new), Open Consent Request v12, Finalize Consent v11, Consent Sweep v3, Room Availability
  v23, Book Session v120, Slack Interactions v37 - `VERSIONS.md` has what each changes; `node scripts/sim-approvals.js` (85).
- Two things found while building: a request must never be booked with `room_override` (it also skips standing holds), so
  "Booked – ask to use" lists only rooms that normally do the booking type; and a priority request now keeps every room it was
  made with (booth, holding rooms) and places them together.
- Not in this build: the engineer / arranger notice for the booking placed by a request (the messages say it is booked).
- During QA the deadline follows the real clock while the booking is a year ahead, so it is usually "now + 24 h".

### Import order (each by the usual routine: download before + check-import before, Cmd+A -> Delete, import, Save, Publish, download after + check-import after)

0. Jessie Log sheet, *Consent Requests* tab: four headers after **Req Payload** - `Approver 2`, `Approver 2 Name`, `Messages`,
   `Withdrawn At`.
1. **Jessie — Request Messages v1** - a NEW workflow, Publish; send its id, then `scripts/set-request-messages-id.py <id>`
   (Open Consent Request, Finalize, Sweep, Slack Interactions) - commit.
2. **Room Availability v23** (`e7tBQB458nstrqei`) - before = v22.
3. **Book Session v120** (`EUG3sGXkfsJSYIMz`) - before = v119.
4. **Open Consent Request v12** (`nEHnCMMXS0am59Zy`) - before = `workflows/live/jessie-open-consent-request__nEHnCMMXS0am59Zy.json`.
5. **Finalize Consent v11** (`TO1UnZTZ2LhtE9J3`) - before = `workflows/live/jessie-finalize-consent__TO1UnZTZ2LhtE9J3.json`.
6. **Consent Sweep v3** (`QHHDevaWhMk8gSBX`) - before = `workflows/live/jessie-consent-sweep__QHHDevaWhMk8gSBX.json`.
7. **Slack Interactions v37** (`PyxSPoAMtSE1gzaH`) - before = v36. Last: it is what offers requests.
