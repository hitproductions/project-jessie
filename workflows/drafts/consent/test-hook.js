// Offline tests for the Move-Booking tail hook. Run: node workflows/drafts/consent/test-hook.js
const { findConsentForMove } = require('./hook');
let pass = 0, fail = 0;
const ok = (l, c) => { if (c) { pass++; console.log('  ok    ' + l); } else { fail++; console.log('  FAIL  ' + l); } };
const rows = [
  { 'Request ID': 'r1', 'Status': 'PENDING', 'Incumbent Event Id': 'evtC' },
  { 'Request ID': 'r2', 'Status': 'DONE', 'Incumbent Event Id': 'evtX' },
  { 'Request ID': 'r3', 'Status': 'PENDING', 'Incumbent Event Id': 'evtY' },
];
ok('finds the pending row whose incumbent is the moved booking', (findConsentForMove('evtC', rows) || {})['Request ID'] === 'r1');
ok('no match -> null', findConsentForMove('evtZ', rows) === null);
ok('ignores a resolved (DONE) row even if id matches', findConsentForMove('evtX', rows) === null);
ok('empty moved id -> null', findConsentForMove('', rows) === null);
ok('no rows -> null', findConsentForMove('evtC', []) === null);
console.log('\n' + (fail ? fail + ' failing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
