# Repeating bookings (change / cancel) and meeting guests - thinking before a build (20 Nov 2026)

Written for the commercial roll-out (S&A, BD, Marketing - 23 Nov). Nothing here is built yet. PENDING 118 (series) and 160 (guests).

## 1. Repeating bookings

**What exists today.** Two kinds of repeating booking sit on KDC Bookings:
- **Hand-made series** - real Google recurring events (one event with a repeat rule; 682 instances from Sep to Feb). Most standing
  holds are these: KATHA - S&A, SALIN - BD, M6 - Marketing, the M-booth holds.
- **Jessie series** - Book Series makes **separate single events**, one per date (same title, time, room, booker). Nothing links
  them as a series today.

Today Change / Cancel act on **one date** of either kind. That already covers "cancel one at a time".

**What people will want (Howard, 20 Nov):**
1. Cancel one date - exists.
2. Cancel **from a date onwards** ("we're stopping the Thursday huddle from Dec 10").
3. **Change the series from a date onwards** - another day ("weekly Thursdays -> Wednesdays"), time or room.

**Proposed shape (for discussion):**
- A booking that belongs to a series shows that on its card ("Repeats every Thursday until 22 Dec") and its buttons ask once:
  **Cancel** -> "Just this date" / "This and the dates after it". **Change** -> the same two, then the Change form - for "this and
  after" with the Repeats fields (How often / On / Until), so Thursdays can become Wednesdays.
- **Cancel from a date onwards:** hand-made series - end the repeat rule the day before (Google keeps the earlier dates, one edit);
  Jessie series - cancel each later event.
- **Change from a date onwards:** check the new dates first (the series review screen already does this: free / another room / pick /
  leave out), book them, and only then remove the old dates from that day on - like Move, create before delete, so a failure
  leaves the series as it was. Hand-made series: end its rule the day before, then the new dates are a new series.
- **Jessie series need a link** so "the dates after it" can be found: new series get a series tag in the event (one line in the
  description); older ones are found by same title + time + room + booker, from that date on.
- Who may do it: the same rule as one date (the booker, the engineer / arranger, a coordinator in that department, HAIST Dev).
- The notices / reminders already go per event; a series change sends one summary instead of one per date.

**Open questions for Howard:** keep hand-made series as Google repeats when changed, or turn the remaining dates into Jessie dates?
Should a "this and after" change offer a new end date? Cancel the **whole** series (including past dates) - needed, or only from a
date on?

## 2. Meeting guests

**Today** Jessie's bookings carry only the rooms; invitees are added in Google Calendar afterwards (not possible once the calendar
is view-only - PENDING 143).

**Proposed shape:**
- Meetings and Events get a **Guests** field: Slack's people picker (multi-select of workspace members - type a name, pick). Each
  person is added to the event by their **@hit email from Bookers** (Email); someone not in Bookers is looked up in Slack.
- Optional **Other guests (emails)** text box for people outside Hit (clients) - comma-separated.
- A typed request "with Nicole and Japs" pre-fills Guests.
- Google sends the invites (event created with notifications on), so guests get the normal calendar invite and can accept;
  a change or cancel through Jessie updates / cancels it for them the same way.
- Guests are not bookers: they cannot change or cancel the room booking through Jessie (only the booker / coordinator can).
- Change keeps the guests (and can edit them); Move's replacement event must carry them over - today it copies only the rooms.

**Open questions for Howard:** guests on studio sessions too, or only Meeting / Event? Outside emails (clients) - allow? Should
guests also get a Slack DM from Jessie, or only the Google invite?

## 3. Reminders and standing holds

The Monday 9 AM reminder lists the week's bookings per person, standing holds included (since Reminders v11 also the ones a person
made by hand for someone else). Next Monday: Camy's lists M6 - Marketing Mon-Fri (she made it; it is Marketing's, `ref:` Nicole -
Nicole gets it too) and KATHA - S&A Thursday. Options: leave as is; leave out repeating all-day holds; or remind only the person
the booking is for (`ref:`), not also the one who made it.
