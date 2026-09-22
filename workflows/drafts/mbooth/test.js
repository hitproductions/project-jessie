// Offline tests for the M-Booth approval logic. Run: node workflows/drafts/mbooth/test.js
const {
  resolveConsent, BOOTH_HOLDERS, isSharedBooth, holderOf, overlaps, holdCoversSlot,
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

console.log('\nShared-use booth set');
ok('M2/M6 are shared-use (case/space tolerant)', isSharedBooth('M2') && isSharedBooth('m6') && isSharedBooth(' M2 '));
ok('M3 / M7 / Studio F are NOT shared-use', !isSharedBooth('M3') && !isSharedBooth('M7') && !isSharedBooth('Studio F'));
ok('holderOf resolves the booth holder (real ids)', holderOf('M2').holder === 'UPPEY3F4G' && holderOf('M6').holder === 'U06CTHTUS1Y');
ok('M7 is no longer shared-use (dropped)', !isSharedBooth('M7'));
ok('holderOf a non-shared room is null', holderOf('Studio F') === null);
ok('an injected map overrides the default', holderOf('M2', { M2: { holder: 'UX', name: 'Test' } }).holder === 'UX');

console.log('\nStanding-hold identification + decideMBooth');
const holdC = { room: 'M2', summary: 'M2 - Peemo', id: 'h1', transparent: true, recurring: true };
const realC = { room: 'M2', summary: 'YELLOW / Jem Lim / EL', id: 'r1', transparent: false, recurring: false };
ok('recurring+transparent is the standing hold', isStandingHold(holdC));
ok('opaque non-recurring booking is NOT the hold', !isStandingHold(realC));
ok('title "M2 - ..." identifies a hold even without flags', isStandingHold({ summary: 'M2 - Peemo' }));
const ccHold = { reason: 'ROOM_OCCUPIED', conflicts: [holdC] };
ok('non-holder wanting a held booth -> open_mbooth to the holder', (() => { const d = decideMBooth(ccHold, { rooms: 'M2', description: 'ref: UHOWARD' }); return d.action === 'open_mbooth' && d.approver === 'UPPEY3F4G' && d.approverName === 'Peemo'; })());
ok('the booth holder booking their own booth -> book_as_holder', decideMBooth(ccHold, { rooms: 'M2', description: 'ref: UPPEY3F4G' }).action === 'book_as_holder');
ok('a real booking overlapping too -> room_taken (first-come)', decideMBooth({ reason: 'ROOM_OCCUPIED', conflicts: [holdC, realC] }, { rooms: 'M2', description: 'ref: UHOWARD' }).action === 'room_taken');
ok('non-shared room -> none (normal path)', decideMBooth({ reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'Studio F', summary: 'x' }] }, { rooms: 'Studio F', description: 'ref: UHOWARD' }).action === 'none');
ok('shared booth but conflict is a real booking -> none (falls to normal refuse)', decideMBooth({ reason: 'ROOM_OCCUPIED', conflicts: [realC] }, { rooms: 'M2', description: 'ref: UHOWARD' }).action === 'none');
ok('M6 held -> open_mbooth to Nicole', decideMBooth({ reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'M6', summary: 'M6 - Marketing', transparent: true, recurring: true }] }, { rooms: 'M6', description: 'ref: UHOWARD' }).approver === 'U06CTHTUS1Y');

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
