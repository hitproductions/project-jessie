// Offline tests for the consent-reply router. Run: node workflows/drafts/consent/test-router.js
const { routeConsent, rejectRow, notifyRequesterRejected, replyIncumbentDeclined, incumbentContext } = require('./router');
let pass = 0, fail = 0;
const ok = (label, cond, detail) => { if (cond) { pass++; console.log('  ok    ' + label); }
  else { fail++; console.log('  FAIL  ' + label + (detail ? '  :: ' + detail : '')); } };

const row = { 'Request ID': 'r1', 'Status': 'PENDING', 'Approver': 'UJC', 'Approver Name': 'JC',
  'Incumbent Title': 'NET-PUSO / JC', 'Room/Booth': 'Studio F', 'Requester Name': 'Ms. Letty' };

console.log('routeConsent (fail-open)');
ok('own-bot -> ignore', routeConsent({ bot_id: 'B1', text: 'x' }, row).branch === 'ignore');
ok('no pending row -> normal (plain message)', routeConsent({ user: 'UJC', text: 'hi' }, null).branch === 'normal');
ok('already-resolved row -> normal', routeConsent({ user: 'UJC', text: 'no' }, { Status: 'REJECTED' }).branch === 'normal');
ok('incumbent "no" -> reject', routeConsent({ user: 'UJC', text: 'no' }, row).branch === 'reject');
ok('incumbent "nope" -> reject', routeConsent({ user: 'UJC', text: 'nope' }, row).branch === 'reject');
ok('incumbent gives a time -> consent-help (agent moves it)', routeConsent({ user: 'UJC', text: 'move it to oct 22 6-9pm' }, row).branch === 'consent-help');
ok('incumbent "ok sure" -> consent-help (not a decline)', routeConsent({ user: 'UJC', text: 'ok sure, what times are free?' }, row).branch === 'consent-help');

console.log('\nreject handling (case a)');
const rr = rejectRow(row, '2027-10-20T10:00:00Z');
ok('rejectRow sets REJECTED + keeps Request ID', rr['Status'] === 'REJECTED' && rr['Request ID'] === 'r1');
ok('rejectRow records reply-no + Decided At', rr['Resolved Via'] === 'reply-no' && rr['Decided At'] === '2027-10-20T10:00:00Z');
ok('requester-rejected notice names holder + room (case a)', /JC kept their booking/.test(notifyRequesterRejected(row)) && /Studio F/.test(notifyRequesterRejected(row)));
ok('incumbent decline reply is gracious', /stays where it is/.test(replyIncumbentDeclined(row)));

console.log('\ncontext injection');
const ctx = incumbentContext(row);
ok('context names both parties + the booking + the room', /JC/.test(ctx) && /NET-PUSO \/ JC/.test(ctx) && /Studio F/.test(ctx) && /Ms\. Letty/.test(ctx));
ok('context tells agent to move via normal flow, NOT book the requester', /normal Move flow/.test(ctx) && /Do NOT book/.test(ctx));

console.log('\n' + (fail ? fail + ' failing, ' + pass + ' passing' : 'all ' + pass + ' checks pass'));
process.exit(fail ? 1 : 0);
