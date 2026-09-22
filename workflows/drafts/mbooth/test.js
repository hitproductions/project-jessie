// Offline tests for the M-Booth approval logic. Run: node workflows/drafts/mbooth/test.js
const {
  resolveConsent, BOOTH_HOLDERS, isSharedBooth, holderOf, overlaps, holdCoversSlot,
  computeDeadline, sweepAction,
} = require('./logic');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

console.log('Consent gate');
ok('"yes" approves', resolveConsent('yes') === 'approve');
ok('"Approved." approves', resolveConsent('Approved.') === 'approve');
ok('"no" rejects', resolveConsent('no') === 'reject');
ok('"deny" rejects', resolveConsent('deny') === 'reject');
ok('a vague reply is unclear (stays pending)', resolveConsent('maybe later') === 'unclear');
ok('empty is unclear', resolveConsent('') === 'unclear');

console.log('\nShared-use booth set');
ok('M2/M6/M7 are shared-use', isSharedBooth('M2') && isSharedBooth('m6') && isSharedBooth(' M7 '));
ok('M3 / Studio F are NOT shared-use', !isSharedBooth('M3') && !isSharedBooth('Studio F'));
ok('holderOf resolves the booth holder', holderOf('M2').name === 'Peemo' && holderOf('M7').name === 'BD');
ok('holderOf a non-shared room is null', holderOf('Studio F') === null);
ok('an injected map overrides the default', holderOf('M2', { M2: { holder: 'UX', name: 'Test' } }).holder === 'UX');

console.log('\nHold overlap detection');
ok('slot inside the hold overlaps', overlaps('2027-10-20T10:00:00+08:00','2027-10-20T11:00:00+08:00','2027-10-20T09:00:00+08:00','2027-10-20T12:00:00+08:00'));
ok('adjacent (touching end) does NOT overlap', !overlaps('2027-10-20T12:00:00+08:00','2027-10-20T13:00:00+08:00','2027-10-20T09:00:00+08:00','2027-10-20T12:00:00+08:00'));
ok('holdCoversSlot true when any hold event overlaps', holdCoversSlot([{start:'2027-10-20T09:00:00+08:00',end:'2027-10-20T12:00:00+08:00'}], '2027-10-20T10:00:00+08:00','2027-10-20T11:00:00+08:00'));
ok('holdCoversSlot false when none overlap', !holdCoversSlot([{start:'2027-10-20T13:00:00+08:00',end:'2027-10-20T14:00:00+08:00'}], '2027-10-20T10:00:00+08:00','2027-10-20T11:00:00+08:00'));
ok('holdCoversSlot false with no hold events', !holdCoversSlot([], '2027-10-20T10:00:00+08:00','2027-10-20T11:00:00+08:00'));

console.log('\nDeadline tiers (Asia/Manila) — confirmed 2026-09-22');
// 2+ days out → now + 24h (booking Oct 25, now Oct 20 09:00)
ok('2+ days away -> now + 24h', computeDeadline('2027-10-20T09:00:00+08:00','2027-10-25T14:00:00+08:00') === new Date('2027-10-21T09:00:00+08:00').toISOString());
// booking tomorrow → 10:00 Manila on the booking day (now Oct 20, booking Oct 21 14:00)
ok('tomorrow -> 10:00 Manila on the booking day', computeDeadline('2027-10-20T09:00:00+08:00','2027-10-21T14:00:00+08:00') === new Date('2027-10-21T10:00:00+08:00').toISOString());
// same day → now + 3h (now Oct 20 09:00, booking Oct 20 15:00)
ok('same day -> now + 3h', computeDeadline('2027-10-20T09:00:00+08:00','2027-10-20T15:00:00+08:00') === new Date('2027-10-20T12:00:00+08:00').toISOString());
// same day but 3h would run past the session start → capped at start (booking Oct 20 10:00)
ok('same day capped at session start', computeDeadline('2027-10-20T09:00:00+08:00','2027-10-20T10:00:00+08:00') === new Date('2027-10-20T10:00:00+08:00').toISOString());
// tomorrow but 10:00 is after the (early-morning) start → capped at start (booking Oct 21 09:00)
ok('tomorrow capped when 10:00 is past the start', computeDeadline('2027-10-20T09:00:00+08:00','2027-10-21T09:00:00+08:00') === new Date('2027-10-21T09:00:00+08:00').toISOString());
// booking already started/past → deadline floored at now (no negative window)
ok('past/now start -> deadline === now', computeDeadline('2027-10-20T09:00:00+08:00','2027-10-20T08:00:00+08:00') === new Date('2027-10-20T09:00:00+08:00').toISOString());
// tier boundary uses Manila calendar days, not a rolling 24h: now late tonight, booking tomorrow morning = "tomorrow"
ok('crossing midnight counts as a calendar day (tomorrow tier)', computeDeadline('2027-10-20T23:00:00+08:00','2027-10-21T09:00:00+08:00') === new Date('2027-10-21T09:00:00+08:00').toISOString());

console.log('\nSweep action — MBOOTH books on timeout, PREEMPT expires (confirmed 2026-09-22)');
const past = '2027-10-20T13:00:00+08:00', dl = '2027-10-20T12:00:00+08:00';
ok('MBOOTH past deadline -> book (holder silent = book)', sweepAction({ Status:'PENDING', Kind:'MBOOTH', Deadline: dl }, past).action === 'book');
ok('PREEMPT past deadline -> expire (never auto-preempt)', sweepAction({ Status:'PENDING', Kind:'PREEMPT', Deadline: dl }, past).action === 'expire');
ok('before deadline -> wait', sweepAction({ Status:'PENDING', Kind:'MBOOTH', Deadline: dl }, '2027-10-20T11:00:00+08:00').action === 'wait');
ok('already resolved -> skip', sweepAction({ Status:'DONE', Kind:'MBOOTH', Deadline: dl }, past).action === 'skip');
ok('no deadline -> skip (never act blind)', sweepAction({ Status:'PENDING', Kind:'MBOOTH', Deadline: '' }, past).action === 'skip');
ok('unknown Kind past deadline -> expire (safe default)', sweepAction({ Status:'PENDING', Kind:'', Deadline: dl }, past).action === 'expire');

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
