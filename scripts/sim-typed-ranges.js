#!/usr/bin/env node
// main v294 (PENDING 157): typed requests from a Localization coordinator's week, through the real Gate Context, Booked For and
// Form Offer - date spans ("dec 9 to 25", "november 24 to nov 28"), day ranges ("wed to fri"), "days:" lists, the same request
// sent again after an offer, a project code that is not also the client, "engr" / "Engineer X." read as the engineer.
//   node scripts/sim-typed-ranges.js [main v294]
const fs = require('fs');
const MAIN = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v294.json', 'utf8'));
if (!/v294 \(PENDING 157\)/.test(JSON.stringify(MAIN.nodes))) { console.log('0 ok, 0 failed (older build: main v294 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const jsOf = n => MAIN.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const STAFF = FX.bookers.map(b => b.fields).concat([{ Name: 'Juan Test', Initials: 'JX', 'Slack User ID': 'U1', Department: ['Localization'], Info: 'Localization engineer' },
  { Name: 'Mara Test', Initials: 'MA', 'Slack User ID': 'U5', Department: ['Localization'], Info: 'Recordist, Goes by Mara.' }]);
async function turn(text, now, hist) {
  Date.now = () => Date.parse(now);
  const base = { 'Slack Trigger': [{ json: { text, user: 'U1', ts: '1794400000.1', channel: 'D1' } }], 'Get Recent Messages': [{ ts: '1794400000.1', text, user: 'U1' }].concat(hist || []).map(m => ({ json: m })),
    'Get Booker': [{ json: { fields: STAFF.find(s => s.Name === 'Juan Test') } }], 'All Bookers': STAFF.map(f => ({ json: { fields: f } })),
    'All Rooms': FX.rooms.map(r => ({ json: r })), 'All Session Types': FX.sessionTypes.map(t => ({ json: t })) };
  const g = new Function('$', '$input', '$getWorkflowStaticData', jsOf('Gate Context'))($f(base), { first: () => ({ json: {} }), all: () => [] }, () => ({}))[0].json;
  base['Gate Context'] = [{ json: g }];
  base['Booked For'] = [{ json: new Function('$', '$input', jsOf('Booked For'))($f(base), { first: () => ({ json: {} }) })[0].json }];
  return (await new Function('$', '$input', 'return (async function(){' + jsOf('Form Offer') + '\n})();')($f(base), { first: () => ({ json: { keep: 1 } }), all: () => [{ json: { keep: 1 } }] }))[0].json.formOffer;
}
const T12 = '2026-11-12T07:01:00Z', T15 = '2026-11-15T10:05:00Z';
const R = (fo, d, f, days, u) => fo && fo.offer && fo.prefill.d === d && fo.prefill.rep && fo.prefill.rep.f === f && (fo.prefill.rep.days || []).join() === (days || []).join() && fo.prefill.rep.u === u;

(async () => {
  console.log('The week\'s messages (12 / 15 Nov)');
  let fo = await turn('Book studio 1 and studio A for NET-PANDA. Engr Juan. Time is 9am to 10pm every wed to fri starting on dec 9 to 25', T12);
  ok(R(fo, '2026-12-09', 'weekly', ['WE', 'TH', 'FR'], '2026-12-25'), '"every wed to fri starting on dec 9 to 25" -> from Wed 9 Dec, Wed + Thu + Fri, until 25 Dec (was: from Fri 13 Nov, Wed + Fri)', fo.prefill);
  ok(/from Wednesday, December 9, 2026/.test(fo.text) && /Every Wednesday and Thursday and Friday · until Friday, December 25, 2026/.test(fo.text), 'the reply says so', fo.text);
  ok(/Code: NET-PANDA/.test(fo.text) && !/Project: NET-PANDA/.test(fo.text) && !/Client:/.test(fo.text) && !fo.prefill.c, 'the code once - not also Project and Client', fo.text);
  ok(fo.prefill.enN === 'Juan Test', '"Engr Juan." -> the engineer', fo.prefill);
  fo = await turn('Date: dec 9 to 25 Time: 9am to 10pm Title: NET-PANDA engr: JX days: wed, thur, fri', T12);
  ok(R(fo, '2026-12-09', 'weekly', ['WE', 'TH', 'FR'], '2026-12-25') && fo.prefill.cd === 'NET-PANDA' && fo.prefill.enN === 'Juan Test', '"Date: dec 9 to 25 … days: wed, thur, fri" -> the same series, code, engineer (was: no date)', fo.prefill);
  fo = await turn('Date: december 9 to 25 Time: 9am to 10pm Title: NET-PANDA engr: JX Repeats: wed, thur, fri Studios: studio 1, studio A', T12);
  ok(R(fo, '2026-12-09', 'weekly', ['WE', 'TH', 'FR'], '2026-12-25') && fo.prefill.r === 'Studio 1' && fo.prefill.bo === 'Studio A', '"december 9 to 25 … Repeats: wed, thur, fri" -> from 9 Dec (was: from today, 12 Nov)', fo.prefill);
  fo = await turn('Book studio 2 and B november 24 to nov 28, 10am to 11pm for VSI-TRES, engineer is Mara', T15);
  ok(R(fo, '2026-11-24', 'daily', [], '2026-11-28') && fo.prefill.r === 'Studio 2' && fo.prefill.bo === 'Studio B' && fo.prefill.enN === 'Mara Test' && !fo.prefill.c,
    '"november 24 to nov 28" -> every day 24-28 Nov (was: no date)', fo.prefill);
  ok(/Every day · until Saturday, November 28, 2026/.test(fo.text), 'the reply: "Every day · until Saturday, November 28, 2026"', fo.text);

  console.log('The same request again after an offer');
  const offer = { ts: '1794399990.1', bot_id: 'B1', text: fo.text, blocks: fo.blocks || [{ type: 'actions', elements: [{ action_id: 'open_book', value: JSON.stringify(fo.prefill) }] }] };
  const again = await turn('Book studio 2 and B november 24 to nov 28, 10am to 11pm for VSI-TRES, engineer is Mara', T15, [offer, { ts: '1794399980.1', text: 'Book studio 2 and B november 24 to nov 28, 10am to 11pm for VSI-TRES, engineer is Mara', user: 'U1' }]);
  ok(again && again.offer === true && R(again, '2026-11-24', 'daily', [], '2026-11-28'), 'sent again -> the offer again (was: "I can only help with bookings.")', again && { offer: again.offer, why: again.why, p: again.prefill });

  console.log('Spans and day ranges');
  for (const [t, d, f, days, u] of [
    ['book studio 7 dec 28 to jan 2 9am-5pm', '2026-12-28', 'daily', [], '2027-01-02'],
    ['book studio 7 24-28 nov 9am-5pm', '2026-11-24', 'daily', [], '2026-11-28'],
    ['book studio 7 nov 30 - dec 4, mon to fri, 1-3pm', '2026-11-30', 'weekdays', [], '2026-12-04'],
    ['book studio 7 every wed thru fri until dec 18, 1-3pm', null, 'weekly', ['WE', 'TH', 'FR'], '2026-12-18'],
    ['book studio 7 dec 1 to 15 every tuesday 1-3pm', '2026-12-01', 'weekly', ['TU'], '2026-12-15'],
    ['book studio 7 dec 2 to 15 every tuesday 1-3pm', '2026-12-08', 'weekly', ['TU'], '2026-12-15']]) {
    const x = await turn(t, T12);
    ok(x && x.prefill && (d === null || x.prefill.d === d) && x.prefill.rep && x.prefill.rep.f === f && (x.prefill.rep.days || []).join() === days.join() && x.prefill.rep.u === u, JSON.stringify(t) + ' -> ' + [d, f, days.join('+'), 'until ' + u].filter(Boolean).join(' '), x && x.prefill);
  }

  console.log('Not spans (unchanged)');
  for (const [t, want] of [['book studio 7 dec 9 2-4pm', { d: '2026-12-09', s: '14:00', e: '16:00' }], ['book studio 7 dec 9 to 10am', { d: '2026-12-09' }],
    ['book studio 7 tomorrow 9 to 5pm', { d: '2026-11-13' }], ['book studio 7 every tuesday and thursday 1-3pm', { rep: { f: 'weekly', days: ['TU', 'TH'] } }]]) {
    const x = await turn(t, T12), p = (x && x.prefill) || {};
    const good = Object.keys(want).every(k => JSON.stringify(k === 'rep' ? { f: p.rep && p.rep.f, days: p.rep && p.rep.days } : p[k]) === JSON.stringify(want[k])) && !(want.d && p.rep);
    ok(good, JSON.stringify(t) + ' -> ' + JSON.stringify(want) + ', no span', p);
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
