#!/usr/bin/env node
// main v282 (26 Oct): "what are my bookings nov 1-4" - the window is the span written (Nov 1 to Nov 4), not its first date.
// Usage: node scripts/sim-v282.js [main]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const W = require(P + (process.argv[2] || 'workflows/project-jessie-v282.json'));
const code = n => W.nodes.find(x => x.name === n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
if (code('Mine Check').indexOf('v282') === -1) { console.log('0 ok, 0 failed (an older build: v282 not in it)'); process.exit(0); }
// Gate Context passes the span's first date only (as live, 3:18 PM)
const mine = (text, dates) => new Function('$', '$input', code('Mine Check'))(n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text, user: 'U1', channel: 'D1' } : { todayIso: '2027-10-26', datesInMessage: dates || '', gate: {} } }) }),
  { first: () => ({ json: {} }) })[0].json.mineCheck;
const win = m => m.start + '..' + m.end + (m.week ? ' week' : '');
let m = mine('what are my bookings nov 1-4', '2027-11-01');
ok(m.go && win(m) === '2027-11-01..2027-11-05', '"what are my bookings nov 1-4" (live 3:18 PM) -> Nov 1 to Nov 4', win(m));
for (const [t, w] of [['my bookings nov 1 to 4', '2027-11-01..2027-11-05'], ['what do i have november 1 - nov 4', '2027-11-01..2027-11-05'],
  ['my bookings nov 1st to 4th', '2027-11-01..2027-11-05'], ['what do i have oct 30 - nov 2', '2027-10-30..2027-11-03'], ['my bookings 1-4 nov', '2027-11-01..2027-11-05'],
  ['what do i have nov 1–4', '2027-11-01..2027-11-05'], ['my sessions dec 30 - jan 2', '2027-12-30..2028-01-03'], ['what do i have jan 3-5', '2028-01-03..2028-01-06'],
  ['do i have studio 8 bookings nov 1-4', '2027-11-01..2027-11-05']])
  ok(win(mine(t, '')) === w, JSON.stringify(t) + ' -> ' + w, win(mine(t, '')));
ok(mine('do i have studio 8 bookings nov 1-4').room === 'Studio 8', 'the room still narrows it');
ok(win(mine('what do i have nov 1', '2027-11-01')) === '2027-11-01..2027-11-02', 'one date -> that day, as before');
ok(win(mine('what do i have nov 1 2-4pm', '2027-11-01')) === '2027-11-01..2027-11-02', '"nov 1 2-4pm" is a date and a time, not a span');
ok(win(mine('what do i have this week')) === '2027-10-26..2027-11-02 week', '"this week" as before');
ok(win(mine('what do i have in november')) === '2027-11-01..2027-12-01', '"in november" as before');
ok(win(mine('my bookings nov 4-1', '2027-11-04')) === '2027-11-04..2027-11-05' && win(mine('my bookings jan 1 - dec 31', '')) !== '2028-01-01..2029-01-01', 'a backwards or over-long span is not used');
console.log('Mine Reply');
const reply = mc => new Function('$', '$input', code('Mine Reply'))(n => ({ first: () => ({ json: { mineCheck: mc } }) }), { first: () => ({ json: { items: [] } }) })[0].json;
const r = reply(mine('what are my bookings nov 1-4', '2027-11-01'));
ok(/\*Your bookings\* · Mon, Nov 1 – Thu, Nov 4/.test(r.blocks[0].text.text), 'the header says Mon, Nov 1 – Thu, Nov 4', r.blocks[0].text.text);
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
