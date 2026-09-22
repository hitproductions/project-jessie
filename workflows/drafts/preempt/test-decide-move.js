// Offline tests for Decide Preempt (Move). Run: node workflows/drafts/preempt/test-decide-move.js
const { decideMove } = require('./decide-move');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

const refData = JSON.stringify({ preemptionRanks: { 'Celebrity Recording': 100, 'VO Recording': 50 } });
// The booking being moved is a Celebrity Recording (rank 100); the new window is held by a VO (50).
const R = {
  original_id: 'evtB', title: 'CELEB / Ms. Letty / HL', bookerRef: 'ULETTY', bookerName: 'Ms. Letty',
  description: 'Booked by: Ms. Letty | ref: ULETTY | Dept: Music\nSType: Celebrity Recording',
  new_start: '2027-10-22T14:00:00+08:00', new_end: '2027-10-22T17:00:00+08:00',
};
const incDesc = 'Booked by: JC | ref: UJC | Dept: Localization\nSType: VO Recording';
const cnw = { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED',
  conflicts: [{ room: 'Studio F', summary: 'NET-PUSO / JC', id: 'evtC', description: incDesc }] };
const REQ = { authority: 'Dept Head', new_rooms: 'Studio F', booking_date: '2027-10-20', reference_data: refData };

console.log('decideMove');
const d = decideMove(cnw, R, REQ);
ok('offers preemption (moved-celeb 100 > incumbent VO 50)', d.offer === true);
ok('requester type read from the MOVED event SType', d.reason === 'OUTRANKS');
ok('open.approver = incumbent booker', d.open.approver === 'UJC');
ok('open.requester = the moved booking owner', d.open.requester === 'ULETTY');
ok('open carries ranks 100/50', d.open.reqPriority === 100 && d.open.incPriority === 50);
const rp = JSON.parse(d.open.reqPayload);
ok('reqPayload is a MOVE (kind:move) of the requester booking', rp.kind === 'move' && rp.event_id === 'evtB' && rp.confirmed === true);
ok('reqPayload targets the new window + room', rp.new_start_iso === '2027-10-22T14:00:00+08:00' && rp.new_rooms === 'Studio F');

console.log('\nsafe refusals');
ok('unauthorized -> no offer', decideMove(cnw, R, Object.assign({}, REQ, { authority: 'Standard' })).offer === false);
ok('moved booking equal/lower rank -> no offer', decideMove(cnw, Object.assign({}, R, { description: 'ref: ULETTY\nSType: VO Recording' }), REQ).offer === false);
ok('incumbent without SType -> no offer', decideMove({ reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'Studio F', summary: 'X', id: 'e', description: 'ref: UJC' }] }, R, REQ).offer === false);
ok('multi-room clash -> not eligible', decideMove({ reason: 'ROOM_OCCUPIED', conflicts: [{}, {}] }, R, REQ).reason === 'NOT_ELIGIBLE');
ok('no ranks -> no offer', decideMove(cnw, R, Object.assign({}, REQ, { reference_data: '{}' })).offer === false);

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
