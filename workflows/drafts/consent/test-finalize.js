// Offline tests for Finalize Consent core. Run: node workflows/drafts/consent/test-finalize.js
const F = require('./finalize');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

const reqPayload = { summary: 'CELEB SPECIAL / Ms. Letty / HL', start_iso: '2027-10-22T14:00:00+08:00',
  end_iso: '2027-10-22T17:00:00+08:00', rooms: 'Studio F', session_type: 'Celebrity Recording',
  description: 'ref: ULETTY', department: 'Music' };
const baseRow = {
  'Request ID': '20271020010000-ULETTY', 'Status': 'APPROVED', 'Kind': 'PREEMPT',
  'Requester': 'ULETTY', 'Requester Name': 'Ms. Letty', 'Approver': 'UJC', 'Approver Name': 'JC',
  'Room/Booth': 'Studio F', 'Req Start': '2027-10-22T14:00:00+08:00', 'Req End': '2027-10-22T17:00:00+08:00',
  'Incumbent Event Id': 'evt123', 'Incumbent Title': 'NET-PUSO / JC',
  'Incumbent New Start': '2027-10-22T18:00:00+08:00', 'Incumbent New End': '2027-10-22T21:00:00+08:00',
  'Req Priority': 100, 'Inc Priority': 50, 'Req Payload': JSON.stringify(reqPayload),
};

console.log('finalizePlan');
ok('valid APPROVED PREEMPT row -> ok', F.finalizePlan(baseRow).ok === true);
ok('parses Req Payload', F.finalizePlan(baseRow).req.session_type === 'Celebrity Recording');
ok('already DONE -> not actionable', F.finalizePlan(Object.assign({}, baseRow, { 'Status': 'DONE' })).reason === 'ALREADY_DONE');
ok('missing relocation slot -> refuse', F.finalizePlan(Object.assign({}, baseRow, { 'Incumbent New Start': '' })).reason === 'NO_RELOCATION_SLOT');
ok('bad Req Payload -> refuse', F.finalizePlan(Object.assign({}, baseRow, { 'Req Payload': '{not json' })).reason === 'BAD_REQ_PAYLOAD');
ok('missing req slot -> refuse', F.finalizePlan(Object.assign({}, baseRow, { 'Req Start': '' })).reason === 'MISSING_REQ_SLOT');

console.log('\nmovePayload (invoked AS the incumbent)');
const mp = F.movePayload(baseRow);
ok('requester = incumbent booker (owner=true path)', mp.requester === 'UJC');
ok('confirmed true (consent)', mp.confirmed === true);
ok('moves to the agreed new slot', mp.new_start_iso === '2027-10-22T18:00:00+08:00');
ok('keeps the contested room (frees the req time)', mp.new_rooms === 'Studio F');
ok('booking_date is the contested slot date (Manila)', mp.booking_date === '2027-10-22');
ok('carries the incumbent title', mp.title === 'NET-PUSO / JC');

console.log('\nbookPayload (requester into freed room)');
const bp = F.bookPayload(baseRow, reqPayload);
ok('confirmed forced true', bp.confirmed === true);
ok('room_override true (sanctioned exception)', bp.room_override === true);
ok('carries requester summary + session type', bp.summary === 'CELEB SPECIAL / Ms. Letty / HL' && bp.session_type === 'Celebrity Recording');
ok('room = contested room', bp.rooms === 'Studio F');

console.log('\nclassifiers (match live status shapes)');
ok('MOVED -> moved', F.classifyMove({ status: 'MOVED' }) === 'moved');
ok('PARTIAL -> partial (stop, double-book risk)', F.classifyMove({ status: 'PARTIAL' }) === 'partial');
ok('REJECTED -> failed', F.classifyMove({ status: 'REJECTED', reason: 'ROOM_OCCUPIED' }) === 'failed');
ok('BOOKED -> booked', F.classifyBook({ status: 'BOOKED' }) === 'booked');
ok('book FAILED -> failed', F.classifyBook({ status: 'FAILED' }) === 'failed');

console.log('\nrow updates + messages');
const done = F.rowDone(baseRow, 'reply', '', '2027-10-20T10:00:00Z');
ok('rowDone sets DONE + keeps Request ID (match key)', done['Status'] === 'DONE' && done['Request ID'] === baseRow['Request ID']);
ok('rowDone records Resolved Via + Decided At', done['Resolved Via'] === 'reply' && done['Decided At'] === '2027-10-20T10:00:00Z');
ok('rowFailed sets FAILED', F.rowFailed(baseRow, 'MOVE_FAILED', '2027-10-20T10:00:00Z')['Status'] === 'FAILED');
ok('incumbent-moved notice names title + room', /NET-PUSO \/ JC/.test(F.notifyIncumbentMoved(baseRow)) && /Studio F/.test(F.notifyIncumbentMoved(baseRow)));
ok('requester-booked notice says Booked', /Booked/.test(F.notifyRequesterBooked(baseRow)));
ok('move-fail notice says nothing changed', /nothing changed/i.test(F.notifyRequesterFailed(baseRow, 'move')));
ok('book-fail notice says not double-booked', /double-booked/i.test(F.notifyRequesterFailed(baseRow, 'book')));

console.log('\nplacement kind (book-preempt vs move-preempt)');
ok('book reqPayload -> book placement', F.placementKind({ summary: 'X' }) === 'book');
ok('move reqPayload -> move placement', F.placementKind({ kind: 'move', event_id: 'e' }) === 'move');
const moveReq = { kind: 'move', title: 'CELEB / Ms. Letty / HL', event_id: 'evtB', booking_date: '2027-10-20',
  new_start_iso: '2027-10-22T14:00:00+08:00', new_end_iso: '2027-10-22T17:00:00+08:00', new_rooms: 'Studio F',
  requester: 'ULETTY', requester_name: 'Ms. Letty', confirmed: true };
const pm = F.placeMovePayload(baseRow, moveReq);
ok('placeMovePayload moves the requester booking (owner) confirmed', pm.event_id === 'evtB' && pm.requester === 'ULETTY' && pm.confirmed === true);
ok('placeMovePayload targets the freed window/room', pm.new_start_iso === '2027-10-22T14:00:00+08:00' && pm.new_rooms === 'Studio F');
ok('placeMovePayload no authority needed (owner move)', pm.authority === '');

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
