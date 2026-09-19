// Offline tests for the M-Booth approval logic. Run: node workflows/drafts/mbooth/test.js
const { route, resolveConsent, computeDeadline, APPROVALS_CHANNEL } = require('./logic');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

console.log('Router');
const pend = { status: 'PENDING', approver: 'UPEEMO', thread_ts: '111.222' };
ok('a DM booking is a normal message', route({ channel: 'D0BTP8VQ6UB', user: 'UHOWARD', text: 'book M2' }, null).branch === 'normal');
ok("Jessie's own message is ignored", route({ channel: APPROVALS_CHANNEL, bot_id: 'B1', user: 'UJESSIE' }, pend).branch === 'ignore');
ok('approver reply in the channel goes to consent', route({ channel: APPROVALS_CHANNEL, user: 'UPEEMO', text: 'yes' }, pend).branch === 'consent');
ok('a non-approver in the channel is ignored', route({ channel: APPROVALS_CHANNEL, user: 'USOMEONE', text: 'yes' }, pend).branch === 'ignore');
ok('a channel message with no pending row is ignored', route({ channel: APPROVALS_CHANNEL, user: 'UPEEMO', text: 'hi' }, null).branch === 'ignore');
ok('an already-resolved request is ignored', route({ channel: APPROVALS_CHANNEL, user: 'UPEEMO', text: 'yes' }, { status: 'APPROVED', approver: 'UPEEMO' }).branch === 'ignore');
ok('a normal booking is NEVER touched by the approval branch', route({ channel: 'D0BTP8VQ6UB', user: 'UPEEMO', text: 'yes' }, pend).branch === 'normal');

console.log('\nConsent gate');
ok('"yes" approves', resolveConsent('yes') === 'approve');
ok('"Approved." approves', resolveConsent('Approved.') === 'approve');
ok('"no" rejects', resolveConsent('no') === 'reject');
ok('"deny" rejects', resolveConsent('deny') === 'reject');
ok('a vague reply is unclear (stays pending)', resolveConsent('maybe later') === 'unclear');
ok('empty is unclear', resolveConsent('') === 'unclear');

console.log('\nDeadline math');
const now = '2027-10-20T09:00:00+08:00';
ok('far request is capped by the window', computeDeadline(now, '2027-10-25T14:00:00+08:00', { maxWindowH: 24, minLeadMin: 60 }) === new Date('2027-10-21T09:00:00+08:00').toISOString());
ok('near request is capped by lead time', computeDeadline(now, '2027-10-20T13:00:00+08:00', { maxWindowH: 24, minLeadMin: 60 }) === new Date('2027-10-20T12:00:00+08:00').toISOString());
ok('a slot inside the lead time is too late (deadline === now)', computeDeadline(now, '2027-10-20T09:30:00+08:00', { maxWindowH: 24, minLeadMin: 60 }) === new Date(now).toISOString());

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
