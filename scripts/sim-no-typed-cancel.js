#!/usr/bin/env node
// main v292 (12 Nov): no cancelling from typed text; the year on dates not in this year; a typed change searches up to the date
// typed. The case: "cancel my booking on nov 12 2028" on 12 Nov 2026 was answered "I couldn't find a booking of yours on Sun,
// Nov 12 from today on." and the same day's real booking was cancelled with a button a minute later.
//   node scripts/sim-no-typed-cancel.js [main v292]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v292.json', 'utf8'));
if (!/no cancelling from typed text/.test(JSON.stringify(main.nodes))) { console.log('0 ok, 0 failed (older build: main v292 not in it)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const jsOf = n => main.nodes.find(x => x.name === n).parameters.jsCode;
const run = async (name, input, outs) => new Function('$', '$input', 'return (async function(){' + jsOf(name) + '\n})();')(
  n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] }), { first: () => input[0], all: () => input });
const j1 = async (...a) => (await run(...a))[0].json;
const TODAY = '2026-11-12';
const gate = text => { Date.now = () => Date.parse('2026-11-12T03:54:00Z');
  const $ = n => ({ first: () => ({ json: n === 'Slack Trigger' ? { text, user: 'U1', ts: '1794400000.1', channel: 'D1' } : n === 'Get Booker' ? { fields: { Name: 'X' } } : {} }), all: () => [] });
  return new Function('$', '$input', '$getWorkflowStaticData', jsOf('Gate Context'))($, { first: () => ({ json: {} }), all: () => [] }, () => ({}))[0].json; };
const offer = async (text, dates) => { const g = Object.assign(gate(text), dates ? { datesInMessage: dates } : {});
  return (await j1('Change Offer', [{ json: { keep: 1 } }], { 'Slack Trigger': [{ json: { text, channel: 'D1', user: 'U1', ts: '1794400000.1' } }],
    'Gate Context': [{ json: Object.assign({}, g, { todayIso: TODAY }) }], 'Booked For': [{ json: {} }], 'Get Recent Messages': [] })).changeOffer; };
const ev = (id, title, s, e, room) => ({ id, summary: title, start: { dateTime: s }, end: { dateTime: e }, description: 'Booked by: X | ref: U1',
  attendees: [{ resource: true, email: 'x@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-' + room + ' (1)' }] });
const CAL = { items: [ev('likha', 'LIKHA - Patchbay Meeting', '2026-11-12T14:00:00+08:00', '2026-11-12T16:00:00+08:00', 'Likha'),
  ev('test', 'TEST BOOKING / TEST PRODUCER / JS', '2028-11-01T09:00:00+08:00', '2028-11-01T16:00:00+08:00', 'Studio F')] };
const reply = async (co, res) => j1('Change Reply', [{ json: res || CAL }], { 'Change Offer': [{ json: { changeOffer: co } }] });
const NOC = 'To cancel a booking, open *My bookings* and tap *Cancel* on it.';

(async () => {
  console.log('typed cancels: no card, no Cancel button');
  for (const t of ['cancel my booking on nov 12 2028', 'cancel my booking on nov 1 2028', 'cancel the likha booking today', 'delete LIKHA - Patchbay Meeting',
    'remove my 2pm today', 'pa-cancel yung booking ko bukas', 'cancel'])
  { const co = await offer(t), r = await reply(co);
    ok(co.kind === 'cancel' && r.count === 0 && r.blocks[0].text.text === NOC && r.blocks[1].elements[0].action_id === 'my_bookings'
       && !/bk_cancel|bk_change|bk_/.test(JSON.stringify(r.blocks)), JSON.stringify(t) + ' -> "' + NOC + '" + My bookings', r.blocks); }
  const co0 = await offer('cancel my booking on nov 12 2028');
  ok((await reply(co0, { error: 'x' })).blocks[0].text.text === NOC, 'a typed cancel with the calendar unreadable -> the same line');

  console.log('Prepared Cancel: a typed yes to an old cancel card never cancels');
  const pc = jsOf('Prepared Cancel');
  ok(/if \(d && d\.use\) \{ d = \{ use: false, reason: 'v292: no typed cancel' \}; done = "To cancel a booking, open \*My bookings\* and tap \*Cancel\* on it\."; \}\s*\/\/ v292[^\n]*\nreturn \[\{ json: Object\.assign\(\{\}, \$input\.first\(\)\.json \|\| \{\}, \{ _cancelDirect: d, _alreadyDone: done \}\) \}\];\s*$/.test(pc),
     'the last step before its return turns use off and answers with the line (Already Done? sends it)');

  console.log('typed changes: the year, and the search reaches the date typed');
  let co = await offer('move my nov 1 2028 booking to nov 2 2028', '2028-11-01,2028-11-02');
  ok(co.kind === 'change' && co.fDates.join() === '2028-11-01' && co.n.d === '2028-11-02' && co.timeMax === '2028-11-03T00:00:00+08:00' && co.timeMin === TODAY + 'T00:00:00+08:00',
     'two dates in 2028 -> found by the first, the search runs to the day after the last (was today + 61 days)', co);
  let r = await reply(co);
  ok(r.count === 1 && r.blocks[1].block_id === 'bk_test' && /\nNow: Wed, Nov 1, 2028 · 9:00 AM – 4:00 PM · Studio F\nNew: Thu, Nov 2, 2028 · 9:00 AM – 4:00 PM · Studio F$/.test(r.blocks[1].text.text),
     'the 2028 booking found: "Wed, Nov 1, 2028" / "Thu, Nov 2, 2028"', r.blocks[1]);
  const cf = r.blocks[2].elements.find(e => e.action_id === 'bk_cancel');
  ok(cf && /Wed, Nov 1, 2028/.test(cf.confirm.text.text), 'the Cancel button on it (Slack confirm box) names the year too', cf && cf.confirm);
  co = await offer('move my nov 12 2028 booking to nov 13 2028', '2028-11-12,2028-11-13');
  r = await reply(co);
  ok(r.count === 0 && r.blocks[0].text.text === 'I couldn’t find a booking of yours on Sun, Nov 12, 2028 from today on.', 'not found -> "on Sun, Nov 12, 2028" (was "Sun, Nov 12")', r.blocks[0]);
  co = await offer('move the likha booking to 3pm');
  r = await reply(co);
  ok(r.count === 1 && /Now: Thu, Nov 12 · 2:00 PM – 4:00 PM · Likha\nNew: Thu, Nov 12 · 3:00 PM – 5:00 PM · Likha/.test(r.blocks[1].text.text)
     && co.timeMax === '2027-01-12T00:00:00+08:00', 'this year: no year on the date; no date typed -> 61 days as before', [r.blocks[1], co.timeMax]);

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
