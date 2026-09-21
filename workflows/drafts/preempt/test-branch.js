// Offline tests for the preemption branch. Run: node workflows/drafts/preempt/test-branch.js
const { stypeStamp, parseSType, parseRef, preemptAtConflict } = require('./branch');
const { buildRankMap } = require('./logic');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

const M = buildRankMap([
  { type: 'Celebrity Recording', rank: 100 },
  { type: 'Band Recording', rank: 90 },
  { type: 'VO Recording', rank: 50 },
]);
const desc = 'Booked by Cristel Cube\nref: UJC\nDept: Localization\nType: External\nSType: VO Recording';

console.log('stamp + parsers');
ok('stypeStamp builds the segment', stypeStamp('Celebrity Recording') === 'SType: Celebrity Recording');
ok('stypeStamp blank when no type', stypeStamp('') === '');
ok('parseSType reads it', parseSType(desc) === 'VO Recording');
ok('parseSType null when absent', parseSType('ref: UJC\nDept: X') === null);
ok('parseRef reads booker', parseRef(desc) === 'UJC');

const base = {
  requesterAuthorized: true, requesterType: 'Celebrity Recording',
  requester: 'ULETTY', requesterName: 'Ms. Letty', room: 'Studio F',
  reqStart: '2027-10-22T14:00:00+08:00', reqEnd: '2027-10-22T17:00:00+08:00',
  reqPayload: { summary: 'CELEB / Ms. Letty / HL', session_type: 'Celebrity Recording' },
  incumbentEventId: 'evt1', incumbentTitle: 'NET-PUSO / JC', incumbentDescription: desc, rankMap: M,
};

console.log('\npreemptAtConflict');
const good = preemptAtConflict(base);
ok('authorized + outrank (100>50) + booker -> offer', good.offer === true);
ok('open context targets the incumbent booker as approver', good.open.approver === 'UJC');
ok('open carries both priorities', good.open.reqPriority === 100 && good.open.incPriority === 50);
ok('open carries the requester Req Payload', good.open.reqPayload.session_type === 'Celebrity Recording');
ok('unauthorized -> no offer', preemptAtConflict(Object.assign({}, base, { requesterAuthorized: false })).offer === false);
ok('equal/lower rank -> no offer', preemptAtConflict(Object.assign({}, base, { requesterType: 'VO Recording' })).offer === false);
ok('incumbent has no SType -> unknown -> no offer', preemptAtConflict(Object.assign({}, base, { incumbentDescription: 'ref: UJC\nDept: X' })).offer === false);
ok('  reason is INCUMBENT_RANK_UNKNOWN', preemptAtConflict(Object.assign({}, base, { incumbentDescription: 'ref: UJC' })).reason === 'INCUMBENT_RANK_UNKNOWN');
ok('outrank but no booker ref -> no offer', preemptAtConflict(Object.assign({}, base, { incumbentDescription: 'SType: VO Recording' })).offer === false);
ok('  reason NO_INCUMBENT_BOOKER', preemptAtConflict(Object.assign({}, base, { incumbentDescription: 'SType: VO Recording' })).reason === 'NO_INCUMBENT_BOOKER');

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
