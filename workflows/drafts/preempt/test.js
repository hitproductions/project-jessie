// Offline tests for the priority-preemption decision. Run: node workflows/drafts/preempt/test.js
const { normType, buildRankMap, rankOf, decidePreempt } = require('./logic');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

// Mirrors the suggested ranks in docs/design/consent-engine.md.
const rows = [
  { type: 'Celebrity Recording', rank: 100 },
  { type: 'Localization Dubbing', rank: 80 },
  { type: 'VO Recording', rank: 60 },
  { type: 'Music Vocal Recording', rank: 60 },
  { type: 'Post Mixing', rank: 50 },
  { type: 'Meeting', rank: 10 },
  { type: 'Blank Rank Type', rank: '' },   // present but blank -> 0
];
const M = buildRankMap(rows);
const auth = { authorized: true };
const noauth = { authorized: false };

console.log('Rank map + normalization');
ok('reads a rank', rankOf(M, 'Celebrity Recording') === 100);
ok('case/space-insensitive', rankOf(M, '  celebrity   recording ') === 100);
ok('blank rank becomes 0', rankOf(M, 'Blank Rank Type') === 0);
ok('unknown type is undefined (not 0)', rankOf(M, 'Nonexistent Type') === undefined);

console.log('\nDecision — the canonical case');
ok('Celebrity (100) outranks VO (60) -> preempt', decidePreempt('Celebrity Recording', 'VO Recording', M, auth).preempt === true);
ok('  reason OUTRANKS', decidePreempt('Celebrity Recording', 'VO Recording', M, auth).reason === 'OUTRANKS');
ok('VO (60) cannot preempt Celebrity (100)', decidePreempt('VO Recording', 'Celebrity Recording', M, auth).preempt === false);
ok('  reason LOWER_RANK', decidePreempt('VO Recording', 'Celebrity Recording', M, auth).reason === 'LOWER_RANK');

console.log('\nDecision — the safe defaults');
ok('equal rank never preempts (VO vs Music Vocal, both 60)', decidePreempt('VO Recording', 'Music Vocal Recording', M, auth).preempt === false);
ok('  reason EQUAL_RANK', decidePreempt('VO Recording', 'Music Vocal Recording', M, auth).reason === 'EQUAL_RANK');
ok('unauthorized requester never preempts, even outranking', decidePreempt('Celebrity Recording', 'VO Recording', M, noauth).preempt === false);
ok('  reason NOT_AUTHORIZED', decidePreempt('Celebrity Recording', 'VO Recording', M, noauth).reason === 'NOT_AUTHORIZED');
ok('unknown INCUMBENT type refuses (not silently preemptible)', decidePreempt('Celebrity Recording', 'Mystery Type', M, auth).preempt === false);
ok('  reason INCUMBENT_RANK_UNKNOWN', decidePreempt('Celebrity Recording', 'Mystery Type', M, auth).reason === 'INCUMBENT_RANK_UNKNOWN');
ok('unknown REQUESTER type treated as 0 -> cannot outrank Meeting(10)', decidePreempt('Mystery Type', 'Meeting', M, auth).preempt === false);
ok('requester outranks a blank-rank (0) incumbent', decidePreempt('Meeting', 'Blank Rank Type', M, auth).preempt === true);

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
