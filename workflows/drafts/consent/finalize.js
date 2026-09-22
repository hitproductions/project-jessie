// Finalize Consent — the deterministic core for the sub-workflow that, on an APPROVED request,
// relocates the incumbent (via the live Move Booking) and places the requester (via the live Book
// Session), then marks the row DONE and notifies both. Pure functions, offline-tested. Draft.
// See docs/design/consent-engine.md.
//
// Key design points (all decided with Howard):
//  - Relocation reuses the LIVE Move Booking, invoked AS THE INCUMBENT (requester = the incumbent's
//    booker id) so owner===true and NOT_YOURS never triggers — consent is the authorization, and no
//    guard is modified. Move creates-replacement-before-delete, so the double-book guard is untouched.
//  - The requester is placed with the LIVE Book Session into the now-free room — a normal booking.
//  - All-or-nothing & move-first: if the incumbent can't be freed, the requester is never placed and
//    nothing changed; if the incumbent moved but the requester's book then fails, the incumbent is
//    only ever at the slot THEY agreed to (never homeless, never a double-book).
//  - Needs the requester's original Book Session inputs, which the row can't hold field-by-field, so
//    they ride a single `Req Payload` JSON column written at Open time.

function safeParse(s) {
  if (s && typeof s === 'object') return s;
  try { return JSON.parse(s || ''); } catch (_) { return null; }
}

function dateOf(iso) {
  try { return new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Manila', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date(iso)); }
  catch (_) { return ''; }
}

// Validate the row is actionable and gather what finalize needs. Returns {ok, reason?, kind, req?}.
// Place-only: Finalize is triggered by the Move-Booking tail hook AFTER the incumbent has already
// moved their own booking (freeing the room). So it only validates that we can place the requester —
// it no longer relocates the incumbent, and needs no relocation slot on the row.
function finalizePlan(row) {
  if (!row) return { ok: false, reason: 'NO_ROW' };
  const status = String(row['Status'] || '').toUpperCase();
  if (['DONE', 'REJECTED', 'EXPIRED', 'FAILED'].indexOf(status) !== -1) return { ok: false, reason: 'ALREADY_' + status };
  if (!row['Req Start'] || !row['Req End'] || !row['Room/Booth']) return { ok: false, reason: 'MISSING_REQ_SLOT' };
  const req = safeParse(row['Req Payload']);
  if (!req) return { ok: false, reason: 'BAD_REQ_PAYLOAD' };
  const kind = String(row['Kind'] || '').toUpperCase();
  return { ok: true, kind: kind, req: req };
}

// Move Booking inputs — invoked AS the incumbent booker so owner===true; consent===confirmed.
function movePayload(row) {
  return {
    title: row['Incumbent Title'] || '',
    event_id: row['Incumbent Event Id'] || '',
    booking_date: dateOf(row['Req Start']),           // the incumbent's current date (the contested slot)
    new_start_iso: row['Incumbent New Start'] || '',
    new_end_iso: row['Incumbent New End'] || '',
    new_rooms: row['Room/Booth'] || '',               // same room, new agreed time (or an agreed different room)
    requester: row['Approver'] || '',                 // incumbent booker -> owner===true -> not NOT_YOURS
    requester_name: row['Approver Name'] || '',
    confirmed: true, authority: '', department: '',
  };
}

// Book Session inputs — the requester's own booking into the freed room. Their original request rides
// `Req Payload`; we force confirmed (consent) and room_override (this is the sanctioned exception).
function bookPayload(row, req) {
  return Object.assign({}, req, {
    confirmed: true,
    room_override: true,
    rooms: req.rooms || row['Room/Booth'] || '',
    start_iso: req.start_iso || row['Req Start'],
    end_iso: req.end_iso || row['Req End'],
  });
}

// Placement kind: a book-preempt places the requester with a fresh Book Session; a move-preempt
// places them by MOVING their existing booking into the freed room (reqPayload carries kind:'move').
function placementKind(req) {
  return (req && req.kind === 'move') ? 'move' : 'book';
}

// Move payload to PLACE the requester (move their own booking into the freed room). The reqPayload
// already carries the move fields from the Move preempt branch; force confirmed and fill the room.
function placeMovePayload(row, req) {
  return {
    title: req.title || row['Incumbent Title'] || '',
    event_id: req.event_id || '',
    booking_date: req.booking_date || '',
    new_start_iso: req.new_start_iso || row['Req Start'],
    new_end_iso: req.new_end_iso || row['Req End'],
    new_rooms: req.new_rooms || row['Room/Booth'] || '',
    requester: req.requester || row['Requester'] || '',    // the requester owns this booking -> owner=true
    requester_name: req.requester_name || row['Requester Name'] || '',
    confirmed: true, authority: '', department: '',
  };
}

// Classify the sub-workflow results (both return a `status` field).
function classifyMove(r) {
  const s = String((r && r.status) || '').toUpperCase();
  if (s === 'MOVED') return 'moved';
  if (s === 'PARTIAL') return 'partial';   // replacement made but original not deleted = double-book; STOP
  return 'failed';
}
function classifyBook(r) {
  const s = String((r && r.status) || '').toUpperCase();
  return s === 'BOOKED' ? 'booked' : 'failed';
}

// Row updates (Google Sheets update, matched on Request ID). Only the changed cells.
function rowDone(row, resolvedVia, attestedBy, now) {
  return {
    'Request ID': row['Request ID'],
    'Status': 'DONE',
    'Resolved Via': resolvedVia || '',
    'Attested By': attestedBy || '',
    'Decided At': (now || new Date().toISOString()),
  };
}
function rowFailed(row, reason, now) {
  return {
    'Request ID': row['Request ID'],
    'Status': 'FAILED',
    'Resolved Via': reason || 'FAILED',
    'Decided At': (now || new Date().toISOString()),
  };
}

// Notification messages. (Place-only: the incumbent already moved their own booking via the normal
// move flow, so this is a brief thank-you/confirmation, not a "I moved it for you" note.)
function notifyIncumbentMoved(row) {
  return `Thanks for moving your "${row['Incumbent Title']}" — ${row['Room/Booth']} is now with `
    + `${row['Requester Name'] || 'the higher-priority booking'} for that slot. Appreciate it!`;
}
function notifyRequesterBooked(row) {
  return `Done — ${row['Room/Booth']} is yours for the requested time. ${row['Approver Name']} moved `
    + `their session to make way. Booked.`;
}
function notifyRequesterFailed(row, stage) {
  if (stage === 'move') {
    return `Couldn't free ${row['Room/Booth']} — ${row['Approver Name']}'s session couldn't be moved `
      + `to the agreed slot, so nothing changed. Want to try another time or room?`;
  }
  return `${row['Approver Name']}'s session was moved, but I couldn't place your booking in `
    + `${row['Room/Booth']} just now. Nothing is double-booked. Please try booking it again.`;
}

module.exports = {
  safeParse, dateOf, finalizePlan, movePayload, bookPayload, placementKind, placeMovePayload,
  classifyMove, classifyBook, rowDone, rowFailed,
  notifyIncumbentMoved, notifyRequesterBooked, notifyRequesterFailed,
};
