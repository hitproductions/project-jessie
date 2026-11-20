#!/usr/bin/env node
// main v300 + Slack Interactions v87 (Howard, 20 Nov): a meeting's / an event's title typed in the first message fills the form's title
// box, and "tom" / "tmrw" are tomorrow - through the real Gate Context, Booked For, Form Offer and Build Step 2. Made-up names only.
//   node scripts/sim-typed-title.js [main v300] [slack-interactions v87]
const fs = require('fs');
const MAIN = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v300.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const jsOf = n => MAIN.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const rooms = FX.rooms.concat(['Likha', 'Katha', 'Salin', 'Lobby'].filter(n => !FX.rooms.some(r => r.fields['Room Name'] === n)).map((n, i) => ({ id: 'cr' + i, fields: { 'Room Name': n, 'Room Type': [n === 'Lobby' ? 'Lobby' : 'Conference Room'] } })))
  .concat(['M3', 'M4'].map((n, i) => ({ id: 'mb' + i, fields: { 'Room Name': n, 'Room Type': ['M Booth'] } })));
const types = FX.sessionTypes.filter(x => !/^(Meeting|Event)$/.test(x.fields.Type)).concat([{ id: 'mt', fields: { Type: 'Meeting' } }, { id: 'ev', fields: { Type: 'Event' } }]);
const P = (id, Name, Initials, Info, Department) => ({ Name, Initials, 'Slack User ID': id, Info, Department: [Department], Authority: ['Standard'] });
const STAFF = [P('UREQ01', 'Sales Person', 'SP', 'Account Manager', 'Sales & Accounts'), P('UANA01', 'Ana Reyes', 'AR', 'Account Manager, Goes by Annie.', 'Marketing'),
  P('ULEA01', 'Lea Santos', 'LS', 'Marketing Lead', 'Marketing'), P('UJDC01', 'John Dela Cruz', 'JDC', 'Producer', 'Business Development'),
  P('UJTN01', 'John Tan', 'JT', 'Producer', 'Business Development'), P('UVIC01', 'Victor Ramos', 'VR', 'Managing Director, Goes by Vic, Sir Vic.', 'Management'),
  P('UBEN01', 'Ben Ong', 'BO', 'Post Engineer', 'Audio Post'), P('UNIK01', 'Nicole Lim', 'NL', 'Account Manager, Goes by Nikki', 'Sales & Accounts'), P('UTOM01', 'Tom Villa', 'TV', 'Post Engineer', 'Audio Post')];
const offer = async text => {
  Date.now = () => Date.parse('2026-11-20T06:00:00Z');
  const base = { 'Slack Trigger': [{ json: { text, user: 'UREQ01', ts: '1794500000.1', channel: 'D1' } }], 'Get Recent Messages': [{ json: { ts: '1794500000.1', text, user: 'UREQ01' } }],
    'Get Booker': [{ json: { fields: STAFF[0] } }], 'All Bookers': STAFF.map(f => ({ json: { fields: f } })), 'All Rooms': rooms.map(r => ({ json: r })), 'All Session Types': types.map(t => ({ json: t })) };
  base['Gate Context'] = [{ json: new Function('$', '$input', '$getWorkflowStaticData', jsOf('Gate Context'))($f(base), { first: () => ({ json: {} }), all: () => [] }, () => ({}))[0].json }];
  base['Booked For'] = [{ json: new Function('$', '$input', jsOf('Booked For'))($f(base), { first: () => ({ json: {} }) })[0].json }];
  const r = await new Function('$', '$input', 'return (async function(){' + jsOf('Form Offer') + '\n})();')($f(base), { first: () => ({ json: { keep: 1 } }), all: () => [{ json: { keep: 1 } }] });
  return r[0].json.formOffer || {};
};
const SI = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v87.json', 'utf8'));
const TOMORROW = '2026-11-21';
const C = [
  // [text, expect {key: value | null for absent}, why]
  ['book a meeting with ana this sunday, for test meeting 12-3pm', { ti: 'test meeting', gu: 'UANA01', d: '2026-11-22' }, 'Howard\'s message: "for test meeting" is the title, Ana a guest, Sunday the date'],
  ['book likha tomorrow 2-3pm titled Q4 Planning', { ti: 'Q4 Planning' }, '"titled Q4 Planning" (a digit in a title is kept)'],
  ['meeting in katha friday 3-4pm called "Budget review" with lea', { ti: 'Budget review', gu: 'ULEA01' }, '"called "Budget review"" - quotes dropped; the guest still read'],
  ['book salin monday 9-10am, title: Team huddle', { ti: 'Team huddle' }, '"title: Team huddle"'],
  ['book likha tomorrow 2-3pm titled BD x Marketing sync', { ti: 'BD x Marketing sync' }, '"titled BD x Marketing sync" (departments in the title)'],
  ['book a meeting for the launch plan tomorrow 10am-12pm', { ti: 'launch plan', d: TOMORROW }, '"for the launch plan" - "the" dropped, ends at the date'],
  ['meeting with ana re budget tomorrow 2pm-3pm', { ti: 'budget', gu: 'UANA01' }, '"re budget" when nothing else names it'],
  ['meeting with ana to discuss the launch tomorrow 2-3pm', { ti: 'launch', gu: 'UANA01' }, '"to discuss the launch"'],
  ['book the lobby dec 5 all day for the year end party', { ti: 'year end party', p: 'Event' }, 'an Event: "for the year end party"'],
  ['book salin for sir vic tomorrow 9-10am', { ti: null }, '"for sir vic" - a colleague, not a title'],
  ['book a meeting for tomorrow 2-3pm', { ti: null, d: TOMORROW }, '"for tomorrow" - a date, not a title'],
  ['book likha for 2 hours tomorrow', { ti: null }, '"for 2 hours" - not a title'],
  ['book a meeting tomorrow 2-3pm', { ti: null }, 'nothing typed: no title'],
  ['book studio 7 tomorrow 1-3pm for VO recording', { ti: null }, 'a studio session: no title box'],
  ['meeting with ana tom 2-3pm', { d: TOMORROW, gu: 'UANA01' }, '"tom" = tomorrow ("ana tom")'],
  ['book likha tom 3-4pm', { d: TOMORROW }, '"likha tom 3-4pm"'],
  ['book m3 tmrw', { d: TOMORROW, p: '__booth', ad: 1 }, '"tmrw" (an M booth, all day)'],
  ['book a meeting tom with lea 10-11am', { d: TOMORROW, gu: 'ULEA01' }, '"a meeting tom with lea"'],
  ['book a meeting tomorrow 2-3pm with ana and tom', { d: TOMORROW, gu: 'UANA01,UTOM01' }, '"with ana and tom" - Tom the person'],
  ['book studio 7 tomorrow 1-3pm for VO recording, engineer tom', { d: TOMORROW, en: 'UTOM01' }, '"engineer tom" - Tom the engineer'],
  ['book a meeting with Tom 3-4pm tomorrow', { d: TOMORROW, gu: 'UTOM01' }, '"with Tom" (a capital) - the person'],
];
(async () => {
  console.log('main v300: the title and "tom"');
  for (const [text, want, why] of C) {
    const fo = await offer(text), pf = fo.prefill || {};
    const bad = Object.keys(want).filter(k => want[k] === null ? pf[k] !== undefined : String(pf[k] === undefined ? '' : pf[k]) !== String(want[k]));
    ok(!bad.length, why, { bad, pf, text: fo.text });
  }
  let fo = await offer('book a meeting with ana this sunday, for test meeting 12-3pm');
  ok(/\nMeeting\nTitle: Test meeting\nGuests: Ana Reyes(\n|$)/.test(fo.text), 'the offer: "Title: Test meeting" under Meeting, then the guests', fo.text);
  console.log('Slack Interactions v87: the title box');
  const FXr = FX.rooms, ST = t => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': '', Priority: [], 'Last Resort': [], 'Engineer Role Required': [] } });
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FXr, sessionTypes: FX.sessionTypes.concat([ST('Meeting'), ST('Event')]), bookers: STAFF.map((f, i) => ({ id: 'r' + i, fields: f })) }) } }];
  const step2 = async s => { const js = SI.nodes.find(x => x.name === 'Build Step 2').parameters.jsCode;
    const r = await new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $f({ 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] }),
      { first: () => ({ json: { status: 'OK', busy: [], free_priority: ['Likha'], free_rooms: ['Likha', 'Katha'] } }), all: () => [{ json: { status: 'OK', busy: [], free_priority: ['Likha'], free_rooms: ['Likha', 'Katha'] } }] });
    return r[0].json.view; };
  const S = (p, pre) => ({ date: TOMORROW, t0: '10:00', t1: '11:00', purpose: p, kind: 'meeting', requester: 'UREQ01', channel: 'D1', ext: 'x', when: 'x', pre });
  let v = await step2(S('Meeting', { ti: 'test meeting' }));
  ok((v.blocks.find(b => b.block_id === 'title') || {}).element.initial_value === 'Test meeting', 'Meeting: the title box starts with "Test meeting" (first letter capital)');
  v = await step2(S('Event', { ti: 'year end party' }));
  ok((v.blocks.find(b => b.block_id === 'title') || {}).element.initial_value === 'Year end party', 'Event: "Year end party"');
  v = await step2(S('Meeting', {}));
  ok(!(v.blocks.find(b => b.block_id === 'title') || {}).element.initial_value, 'no title typed: the box empty, as before');
  console.log('\n' + pass + ' ok, ' + fail + ' failed'); process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
