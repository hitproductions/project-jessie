// Decide Preempt (Move) — the assembly the Move Booking `Decide Preempt` node inlines. Like the Book
// version, but adapted for a MOVE: the requester's session type comes from the MOVED event's SType
// (Resolve Booking carries its description), and the requester is placed by MOVING their booking into
// the freed room, so reqPayload is a MOVE payload (kind:'move'). Pure, offline-tested. Draft.
const { preemptAtConflict } = require('./branch');
const { isAuthorized, ranksFromRef } = require('./decide');

function parseSType(desc) { const m = String(desc || '').match(/SType:\s*([^\n|]+)/i); return m ? m[1].trim() : null; }

// cnw = Check New Window output (conflicts[0] carries id/description/summary at ROOM_OCCUPIED).
// R   = Resolve Booking output (the booking being moved: description, original_id, title, bookerRef…).
// REQ = the Move Booking inputs.
function decideMove(cnw, R, REQ) {
  const eligible = cnw && cnw.reason === 'ROOM_OCCUPIED' && Array.isArray(cnw.conflicts) && cnw.conflicts.length === 1;
  if (!eligible) return { offer: false, reason: 'NOT_ELIGIBLE' };
  const inc = cnw.conflicts[0] || {};
  const requesterType = parseSType((R || {}).description);   // the moved booking's session type
  const room = REQ.new_rooms || inc.room;
  // The requester is PLACED by moving their existing booking into the freed room (kind:'move').
  const reqPayload = JSON.stringify({
    kind: 'move',
    title: R.title, event_id: R.original_id, booking_date: REQ.booking_date,
    new_start_iso: R.new_start, new_end_iso: R.new_end, new_rooms: room,
    requester: R.bookerRef, requester_name: R.bookerName, confirmed: true,
  });
  return preemptAtConflict({
    requesterAuthorized: isAuthorized(REQ.authority),
    requesterType: requesterType,
    requester: R.bookerRef, requesterName: R.bookerName,
    room: room, reqStart: R.new_start, reqEnd: R.new_end,
    reqPayload: reqPayload,
    incumbentEventId: inc.id, incumbentTitle: inc.summary, incumbentDescription: inc.description,
    rankMap: ranksFromRef(REQ.reference_data),
  });
}

module.exports = { parseSType, decideMove };
