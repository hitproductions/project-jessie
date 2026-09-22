// Offline tests for Decide Preempt assembly. Run: node workflows/drafts/preempt/test-decide.js
const { parseBookedBy, parseRefId, isAuthorized, ranksFromRef, decide } = require('./decide');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

console.log('parsers + authority + ranks');
const reqDesc = 'Engineer: HL | Booked by: Ms. Letty | ref: ULETTY | Type: External | Dept: Music';
ok('parseBookedBy', parseBookedBy(reqDesc) === 'Ms. Letty');
ok('parseRefId', parseRefId(reqDesc) === 'ULETTY');
ok('authorized: Dept Head', isAuthorized('Standard, Dept Head') === true);
ok('authorized: HAIST Dev', isAuthorized('HAIST Dev') === true);
ok('not authorized: Standard only', isAuthorized('Standard') === false);
const refData = JSON.stringify({ preemptionRanks: { 'Celebrity Recording': 100, 'VO Recording': 50 } });
ok('ranksFromRef normalizes keys', ranksFromRef(refData)['celebrity recording'] === 100);
ok('ranksFromRef empty when absent', Object.keys(ranksFromRef('{}')).length === 0);

// A single-conflict ROOM_OCCUPIED where a Celebrity Recording (rank 100) hits a VO (rank 50).
const incDesc = 'Booked by: JC | ref: UJC | Dept: Localization | Type: External\nSType: VO Recording';
const cc = { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED',
  conflicts: [{ room: 'Studio F', summary: 'NET-PUSO / JC', id: 'evt1', description: incDesc,
    start: '2027-10-22T14:00:00+08:00', end: '2027-10-22T17:00:00+08:00' }] };
const REQ = {
  summary: 'CELEB / Ms. Letty / HL', start_iso: '2027-10-22T14:00:00+08:00', end_iso: '2027-10-22T17:00:00+08:00',
  rooms: 'Studio F', description: reqDesc, session_type: 'Celebrity Recording',
  client: 'Some Celeb', department: 'Music', engineer: 'HL', bookingType: 'External', all_day: false,
  authority: 'Dept Head', reference_data: refData,
};

console.log('\ndecide()');
const d = decide(cc, REQ);
ok('offers preemption (authorized + 100>50 + readable incumbent + booker)', d.offer === true);
ok('open.approver = incumbent booker id', d.open.approver === 'UJC');
ok('open.requester parsed from own description', d.open.requester === 'ULETTY');
ok('open.requesterName parsed', d.open.requesterName === 'Ms. Letty');
ok('open carries ranks 100/50', d.open.reqPriority === 100 && d.open.incPriority === 50);
ok('open.incumbentEventId + title from the conflict', d.open.incumbentEventId === 'evt1' && d.open.incumbentTitle === 'NET-PUSO / JC');
ok('open.reqPayload is a JSON string carrying session_type', typeof d.open.reqPayload === 'string' && JSON.parse(d.open.reqPayload).session_type === 'Celebrity Recording');

console.log('\ndecide() safe refusals');
ok('unauthorized requester -> no offer', decide(cc, Object.assign({}, REQ, { authority: 'Standard' })).offer === false);
ok('equal/lower rank -> no offer', decide(cc, Object.assign({}, REQ, { session_type: 'VO Recording' })).offer === false);
ok('no ranks in reference_data -> no offer (unknown)', decide(cc, Object.assign({}, REQ, { reference_data: '{}' })).offer === false);
const ccNoSType = { verdict: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'Studio F', summary: 'X', id: 'e', description: 'ref: UJC' }] };
ok('incumbent without SType -> no offer', decide(ccNoSType, REQ).offer === false);
const ru = decide({ verdict: 'REJECTED', reason: 'ROOM_UNSUITABLE', human: 'that room is not suitable' }, REQ);
ok('non-ROOM_OCCUPIED rejection -> no offer', ru.offer === false);
ok('non-ROOM_OCCUPIED rejection -> preemptReason NOT_ELIGIBLE', ru.preemptReason === 'NOT_ELIGIBLE');
ok('non-ROOM_OCCUPIED rejection -> original reason passed through', ru.reason === 'ROOM_UNSUITABLE');
ok('non-ROOM_OCCUPIED rejection -> original human passed through', ru.human === 'that room is not suitable');
const mm = decide({ reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'A' }, { room: 'B' }] }, REQ);
ok('multi-room conflict -> no offer, preemptReason NOT_ELIGIBLE', mm.offer === false && mm.preemptReason === 'NOT_ELIGIBLE');
// The bug this guards: a NOT_CONFIRMED (confirmed=false) that hit an occupied room must keep its
// "present the summary now" guidance instead of collapsing to a bare "booking failed".
const nc = decide({ verdict: 'REJECTED', reason: 'NOT_CONFIRMED', human: 'present the summary now, end with "Confirm to book."' }, REQ);
ok('NOT_CONFIRMED passes through -> agent still told to present the summary', nc.offer === false && nc.reason === 'NOT_CONFIRMED' && /present the summary/.test(nc.human));
// A ROOM_OCCUPIED that cannot be preempted (unauthorized) still reads as "room taken", not "failed".
const roBlocked = decide(Object.assign({ human: 'Studio F is taken in that window' }, cc), Object.assign({}, REQ, { authority: 'Standard' }));
ok('occupied-but-not-preemptible -> ROOM_OCCUPIED message passes through', roBlocked.offer === false && roBlocked.reason === 'ROOM_OCCUPIED' && /taken/.test(roBlocked.human || ''));

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
