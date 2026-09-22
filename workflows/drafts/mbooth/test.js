// Offline tests for the M-Booth approval logic. Run: node workflows/drafts/mbooth/test.js
const {
  resolveConsent, isMBooth, parseHoldName, overlaps, holdCoversSlot,
  isStandingHold, decideMBooth,
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

console.log('\nM-booth recognition (any M<n>, no hard-coded list)');
ok('M1/M2/M4/M6/M8 are M-booths (case/space tolerant)', isMBooth('M1') && isMBooth('m2') && isMBooth(' M4 ') && isMBooth('M6') && isMBooth('M8'));
ok('Studio F / Katha / M (no digit) are NOT M-booths', !isMBooth('Studio F') && !isMBooth('Katha') && !isMBooth('M'));
ok('parseHoldName reads the label off the title', parseHoldName('M2 - Peemo') === 'Peemo' && parseHoldName('M6 - Marketing') === 'Marketing');

console.log('\nStanding-hold identification + decideMBooth (ref-tag based)');
// A hold is any recurring event; the holder is its ref: tag. Transparency is irrelevant now.
const holdBusy = { room: 'M4', summary: 'M4 - Tel', id: 'h1', transparent: false, recurring: true, description: 'ref: U098UFLG70B' };
const holdFree = { room: 'M2', summary: 'M2 - Peemo', id: 'h2', transparent: true, recurring: true, description: 'ref: UPPEY3F4G' };
const realC = { room: 'M2', summary: 'YELLOW / Jem Lim / EL', id: 'r1', transparent: false, recurring: false, description: 'ref: UCLIENT' };
ok('a recurring event is a standing hold (Busy or Free)', isStandingHold(holdBusy) && isStandingHold(holdFree));
ok('a one-off booking is NOT a hold', !isStandingHold(realC));
ok('non-holder wanting a held booth -> open_mbooth to the hold ref (any booth)', (() => { const d = decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[holdBusy] }, { rooms: 'M4', description: 'ref: UHOWARD' }); return d.action === 'open_mbooth' && d.approver === 'U098UFLG70B' && d.approverName === 'Tel'; })());
ok('holds carry over any booth with a ref: (M2)', decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[holdFree] }, { rooms:'M2', description:'ref: UHOWARD' }).approver === 'UPPEY3F4G');
ok('the hold owner booking their own booth -> book_as_holder', decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[holdBusy] }, { rooms: 'M4', description: 'ref: U098UFLG70B' }).action === 'book_as_holder');
ok('a real booking overlapping too -> room_taken (first-come)', decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[holdFree, realC] }, { rooms:'M2', description:'ref: UHOWARD' }).action === 'room_taken');
ok('recurring hold with NO ref: tag -> unidentified_holder (falls through)', decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[{ room:'M5', summary:'M5 - Trish', recurring:true, description:'' }] }, { rooms:'M5', description:'ref: UHOWARD' }).action === 'unidentified_holder');
ok('non-M-booth room -> none (normal path)', decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[{ room:'Studio F', summary:'x', recurring:true, description:'ref: UX' }] }, { rooms:'Studio F', description:'ref: UHOWARD' }).action === 'none');
ok('M-booth but conflict is a one-off booking -> none (falls to normal refuse)', decideMBooth({ reason:'ROOM_OCCUPIED', conflicts:[realC] }, { rooms:'M2', description:'ref: UHOWARD' }).action === 'none');

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
