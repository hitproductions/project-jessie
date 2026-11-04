#!/usr/bin/env node
// PENDING 152 (4 Nov, Howard: "go ahead with skip step 1"): Slack Interactions v68 - a Book a room button that carries the date,
// the times (or all day) and the booking type, no Repeats, goes straight to the free rooms (Read Step 1's Continue booking path);
// step 2 then has "Change date or time", which swaps that window for step 1, filled in (Build Step 1 -> Open Step 1 by views.update).
//   node scripts/sim-skip-step1.js [slack-interactions v68]
const fs = require('fs');
const SI = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v68.json', 'utf8'));
const node = n => SI.nodes.find(x => x.name === n);
if (!/v68 \(PENDING 152\)/.test(node('Check Signature').parameters.jsCode)) { console.log('0 ok, 0 failed (an older build: v68 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const run = (name, input, outs) => new Function('$', '$input', 'return (async function(){' + node(name).parameters.jsCode + '\n})();')(n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] }),
  { first: () => input[0], all: () => input });
const j1 = async (...a) => ((await run(...a))[0] || {}).json;
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: FX.bookers }) } }];

(async () => {
  console.log('Which Book a room buttons skip step 1');
  const cs = node('Check Signature').parameters.jsCode;
  const done = new Function(cs.slice(cs.indexOf('function __stepOneDone'), cs.indexOf('\n}\n', cs.indexOf('function __stepOneDone')) + 3) + '\nreturn __stepOneDone;')();
  const V = o => JSON.stringify(o);
  for (const [v, want, why] of [
    [V({ d: '2026-11-05', s: '14:00', e: '16:00', p: 'Localization Dubbing', r: 'Studio 1', bo: 'Studio A' }), true, 'the typed offer: date, 2-4 PM, Localization Dubbing, rooms'],
    [V({ d: '2026-11-26', s: '14:00', e: '16:00', p: 'Localization Dubbing', cd: 'NET-KUBA' }), true, 'a skipped series date\'s Find another time'],
    [V({ d: '2026-11-05', ad: 1, p: '__booth', r: 'M4' }), true, 'an M booth all day'],
    [V({ d: '2026-11-05', s: '14:00', e: '16:00' }), false, 'no booking type -> step 1'],
    [V({ d: '2026-11-05', p: 'VO Recording' }), false, 'no time -> step 1'],
    [V({ d: '2026-11-05', ad: 1, p: 'VO Recording' }), false, 'all day for a studio session -> step 1 (only M booths / Events are all day)'],
    [V({ d: '2026-11-05', s: '16:00', e: '14:00', p: 'VO Recording' }), false, 'the end before the start -> step 1'],
    [V({ d: '2026-11-05', s: '14:00', e: '16:00', p: 'VO Recording', rep: { f: 'weekly', n: 4 } }), false, 'a series -> step 1 (Repeats is there)'],
    ['menu', false, 'the menu\'s Book a room -> step 1']])
    ok(done(v) === want, why + (want ? ' -> straight to the rooms' : ''));
  ok(cs.includes("action === 'open_book' && __stepOneDone(((p.actions || [])[0] || {}).value)) route = ROUTES.book_step1") && cs.includes("action === 'step1_back')) route = ROUTES.open_book"), 'routes: a complete one -> Read Step 1 (as Continue booking); Change date or time -> Build Step 1');

  console.log('Straight to the rooms (Read Step 1)');
  const val = V({ d: '2026-11-12', s: '14:00', e: '16:00', p: 'Localization Dubbing', r: 'Studio 1', bo: 'Studio A', cd: 'NET-KUBA' });
  const r1 = await j1('Read Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T9', channel: 'D1' } }], 'Timings 1': [],
    'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'open_book', value: val }], container: { channel_id: 'D1', message_ts: '5.5' } } } }] });
  ok(r1.valid && r1.cont === true && r1.trigger_id === 'T9' && r1.s.date === '2026-11-12' && r1.s.t0 === '14:00' && r1.s.kind === 'loc' && r1.s.skip === 1 && r1.s.pre.bo === 'Studio A' && r1.s.msg.ts === '5.5',
    'the booking from the button (Localization, Studio 1 + A kept for step 2), "Finding free rooms…" opened in a new window', r1);
  ok(/Finding free rooms/.test(JSON.stringify(r1.open)) && r1.open.external_id === r1.s.ext, 'the loading window step 2 replaces');

  console.log('Step 2: Change date or time');
  const step2 = async s => (await j1('Build Step 2', [{ json: { status: 'OK', busy: [], free_priority: ['Studio 1', 'Studio 2'], free_rooms: ['Studio 1', 'Studio 2', 'Studio A', 'Studio B'] } }],
    { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] })).view;
  let v2 = await step2(r1.s);
  const bk = v2.blocks.find(b => b.block_id === 'step1_back');
  ok(bk && v2.blocks.indexOf(bk) === 2 && bk.elements[0].action_id === 'step1_back' && bk.elements[0].text.text === 'Change date or time', 'step 2 has "Change date or time" under the date and time', v2.blocks.slice(0, 3).map(b => b.block_id || b.type));
  const g = JSON.parse(bk.elements[0].value);
  ok(g.d === '2026-11-12' && g.s === '14:00' && g.e === '16:00' && g.p === 'Localization Dubbing' && g.r === 'Studio 1' && g.bo === 'Studio A' && g.cd === 'NET-KUBA', 'it carries the booking, to fill step 1 in', g);
  v2 = await step2(Object.assign({}, r1.s, { skip: undefined }));
  ok(!v2.blocks.some(b => b.block_id === 'step1_back'), 'step 2 reached from step 1 (its Back button) -> no extra button, as before');
  const s1 = await j1('Build Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T10', channel: 'D1' } }], 'Read Cache': cache,
    'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'step1_back', value: bk.elements[0].value }], view: { id: 'V22' } } } }] });
  const pick = id => (s1.view.blocks.find(b => b.block_id === id) || {}).element || {};
  ok(s1.view_id === 'V22' && s1.view.callback_id === 'book_step1' && pick('date').initial_date === '2026-11-12' && ((pick('purpose').initial_option || {}).value === 'Localization Dubbing'),
    'Change date or time -> step 1 for that same window, filled in (date, Localization Dubbing)', { vid: s1.view_id, d: pick('date').initial_date, p: pick('purpose').initial_option });
  const o1 = node('Open Step 1').parameters, ex = (t, j) => new Function('$json', 'return (' + t.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '') + ');')(j);
  ok(ex(o1.url, s1) === 'https://slack.com/api/views.update' && JSON.parse(ex(o1.jsonBody, s1)).view_id === 'V22' && !JSON.parse(ex(o1.jsonBody, s1)).trigger_id, 'Open Step 1: views.update on that window');
  const s0 = await j1('Build Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T11', channel: 'D1' } }], 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: 'menu' }] } } }] });
  ok(!s0.view_id && ex(o1.url, s0) === 'https://slack.com/api/views.open' && JSON.parse(ex(o1.jsonBody, s0)).trigger_id === 'T11', 'the menu\'s Book a room -> views.open, as before');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('  FAIL  crashed: ' + (e && e.stack || e)); process.exit(1); });
