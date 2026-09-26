# EOD update — 26 September 2026 (short version)

Paste-ready summary. Full notes: [`EOD-2026-09-26.md`](EOD-2026-09-26.md).

**Envoy mirror (PENDING 42): built and working, not published yet**
- Built v2 and applied it to n8n. It copies tablet bookings from the room calendars onto KDC Bookings every 2 min.
- Live test on the Studio 7 tablet: the booking showed up on KDC Bookings with the right title, time and
  room, and edits on the tablet (e.g. ending early) carry over to the copy.
- Fixed 3 issues found after the first run:
  - it would have filled the n8n database (successful runs are no longer saved)
  - Move Booking couldn't see the copies
  - failures showed green
- Ran Jessie's live code against the real copy: she reports the room busy and refuses to book or move into it.
- Note: we can't ask Jessie in Slack about tablet bookings until launch. The QA year shift makes "today"
  2027 for her.
- Also found: a tablet "release" ends the booking early rather than deleting it, and the mirror handles that.

**Studio E fix (PENDING 43): ready, not applied yet**
- Script ready. It found the dead id in 6 places across 5 workflows, and all tests pass after the swap.

**Next**
1. One last release check on the mirror, then publish.
2. Apply the Studio E fix.
3. Optional: make tablet copies read like Jessie's bookings (e.g. "Booked by: <name> (tablet)").
