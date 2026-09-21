// Offline tests for the consent engine core. Run: node workflows/drafts/consent/test.js
const { classifyInbound, resolveConsent, parseAttestation, computeDeadline } = require('./logic');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

console.log('Router (pending-row keyed, fail-open)');
const pend = { status: 'PENDING', approver: 'UTEL' };
ok("own-bot message is ignored", classifyInbound({ bot_id: 'B1', user: 'UJESSIE', text: 'x' }, pend).branch === 'ignore');
ok("no pending row -> normal (a plain booking DM)", classifyInbound({ user: 'UHOWARD', text: 'book studio 1' }, null).branch === 'normal');
ok("sender is the approver of a pending row -> consent", classifyInbound({ user: 'UTEL', text: 'yes' }, pend).branch === 'consent');
ok("already-resolved row -> normal (not consent)", classifyInbound({ user: 'UTEL', text: 'yes' }, { status: 'APPROVED', approver: 'UTEL' }).branch === 'normal');
ok("empty message -> ignore", classifyInbound(null, pend).branch === 'ignore');

console.log('\nConsent gate');
ok('"yes" approves', resolveConsent('yes') === 'approve');
ok('"Approved." approves', resolveConsent('Approved.') === 'approve');
ok('"ok, 3pm works" approves (first word)', resolveConsent('ok, 3pm works') === 'approve');
ok('"no" rejects', resolveConsent('no') === 'reject');
ok('"deny" rejects', resolveConsent('deny') === 'reject');
ok('vague reply is unclear', resolveConsent('maybe later') === 'unclear');
ok('empty is unclear', resolveConsent('') === 'unclear');

console.log('\nAttestation parser (conservative, fixed phrase)');
ok('"cleared with Tel" attests, name=Tel', (() => { const a = parseAttestation('cleared with Tel'); return a.attested && a.name === 'Tel'; })());
ok('"confirmed with Peemo already" attests, name=Peemo already? trims trailing', (() => { const a = parseAttestation('confirmed with Peemo'); return a.attested && a.name === 'Peemo'; })());
ok('"cleared it with Ms. Letty" attests, name=Ms. Letty', (() => { const a = parseAttestation('cleared it with Ms. Letty'); return a.attested && a.name === 'Ms. Letty'; })());
ok('a plain "yes" does NOT attest', parseAttestation('yes').attested === false);
ok('free-text without the phrase does NOT attest', parseAttestation('she said it is fine').attested === false);
ok('empty does not attest', parseAttestation('').attested === false);

console.log('\nDeadline math');
const now = '2027-10-20T09:00:00+08:00';
ok('far request capped by the window', computeDeadline(now, '2027-10-25T14:00:00+08:00', { maxWindowH: 24, minLeadMin: 60 }) === new Date('2027-10-21T09:00:00+08:00').toISOString());
ok('near request capped by lead time', computeDeadline(now, '2027-10-20T13:00:00+08:00', { maxWindowH: 24, minLeadMin: 60 }) === new Date('2027-10-20T12:00:00+08:00').toISOString());
ok('slot inside lead time -> deadline === now', computeDeadline(now, '2027-10-20T09:30:00+08:00', { maxWindowH: 24, minLeadMin: 60 }) === new Date(now).toISOString());

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
