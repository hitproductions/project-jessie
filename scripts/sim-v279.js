#!/usr/bin/env node
// main v279 (22 Oct, QA): "do i have studio 8 bookings" answered with the person's bookings in Studio 8 (code, not the AI), and Guard
// Probe's leak filter dropping the model's own reasoning ("Per the rules, I need a timeframe before calling List Events.").
// Usage: node scripts/sim-v279.js [main]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const W = require(P + (process.argv[2] || 'workflows/project-jessie-v279.json'));
const code = n => W.nodes.find(x => x.name === n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const mine = text => new Function('$', '$input', code('Mine Check'))(n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text, user: 'U1', channel: 'D1' } : { todayIso: '2027-10-22', gate: {} } }) }),
  { first: () => ({ json: {} }) })[0].json.mineCheck;
console.log('Mine Check');
let m = mine('do i have studio 8 bookings');
ok(m.go && m.room === 'Studio 8' && m.week, '"do i have studio 8 bookings" -> my bookings, Studio 8, this week', m);
ok(mine('do i have any bookings in m4 tomorrow').room === 'M4' && mine('do i have any bookings in m4 tomorrow').go, '"… in m4 tomorrow" -> M4');
ok(mine('my likha bookings').go && mine('my likha bookings').room === 'Likha', '"my likha bookings" -> Likha');
ok(mine('what do i have this week').go && mine('what do i have this week').room === '', 'plain "what do I have this week" -> every room, as before');
ok(!mine('book studio 8 tomorrow 2-4pm').go && !mine('can you cancel my studio 8 booking').go, 'a booking / cancel is not a my-bookings question');
ok(!mine('is studio 8 free tomorrow?').go, 'an availability question is not one either');
console.log('Mine Reply');
const ev = (id, room, ref) => ({ id, summary: 'T' + id, start: { dateTime: '2027-10-23T15:00:00+08:00' }, end: { dateTime: '2027-10-23T18:00:00+08:00' },
  attendees: [{ resource: true, displayName: 'KDC Plaza-Top Level-' + room + ' (6)' }], description: 'ref: ' + ref });
const reply = mc => new Function('$', '$input', code('Mine Reply'))(n => ({ first: () => ({ json: { mineCheck: mc } }) }),
  { first: () => ({ json: { items: [ev('a', 'Studio 8', 'U1'), ev('b', 'Studio 7', 'U1'), ev('c', 'Studio 8', 'U9')] } }) })[0].json;
let r = reply(Object.assign(mine('do i have studio 8 bookings'), { start: '2027-10-22', end: '2027-10-29' }));
ok(/\*Your bookings in Studio 8\*/.test(r.blocks[0].text.text) && r.blocks.filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id).join() === 'bk_a', 'only mine, only Studio 8', r.blocks.map(b => b.block_id || b.type));
r = reply(Object.assign(mine('do i have m4 bookings'), { start: '2027-10-22', end: '2027-10-29' }));
ok(/Nothing booked for you in M4 then\./.test(JSON.stringify(r.blocks)), 'none there -> "Nothing booked for you in M4 then."');
console.log('Guard Probe leak filter');
const g = code('Guard Probe'); const L = g.match(/const _LEAK = (\/.*\/i);/)[1]; const LEAK = eval(L);
const said = ['Howard is asking about Studio 8 bookings with no date given.', 'Per the rules, I need a timeframe before calling List Events.', "I'll ask for it."];
ok(said.every(x => LEAK.test(x)), 'the three leaked lines (12:47) are dropped');
ok(!LEAK.test('Which dates should I check for Studio 8 - tomorrow (Saturday, October 23), or a different day or range?') && !LEAK.test('Studio 7 is free 2:00 PM – 6:00 PM.') && !LEAK.test('Use Book a room to pick a time.'),
   'ordinary answers are kept');
console.log('\n' + pass + ' ok, ' + fail + ' failed');
process.exit(fail ? 1 : 0);
