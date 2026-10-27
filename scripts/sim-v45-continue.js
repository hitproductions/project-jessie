#!/usr/bin/env node
// Slack Interactions v45 (27 Oct, Howard): "Continue booking" on a "Not booked yet" message (the window was closed) opens step 2
// again - rooms checked again, everything filled in - instead of step 1.
// Usage: node scripts/sim-v45-continue.js [slack-interactions v45]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v45.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (!si.nodes.some(n => n.name === 'Open Continue')) { console.log('0 ok, 0 failed (an older build: v45 not in it)'); process.exit(0); }
const run = async (name, input, outs) => { const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  return new Function('$', '$input', 'return (async function(){' + si.nodes.find(x => x.name === name).parameters.jsCode + '\n})();')($, { first: () => input[0], all: () => input }); };
const j1 = async (...a) => (await run(...a))[0].json;
const C = si.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');
const ST = t => ({ id: 'st-' + t.replace(/\s/g, ''), fields: { Type: t, Priority: ['r8', 'rf'], 'Last Resort': [], 'Engineer Role Required': ['Post Engineer'], 'Room Requirements': '' } });
const bookers = [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer', Department: ['Audio Post'] } }];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes.concat([ST('Celebrity Recording')]), bookers }) } }];
const AGAIN = { d: '2027-10-28', s: '14:00', e: '16:00', p: 'Celebrity Recording', r: 'Studio 8', pj: 'test-me', c: 'Harold Orazco', en: 'U1' };
(async () => {
  console.log('The "Not booked yet" message (22 Oct 11:54: "Did you mean Harold Orozco?")');
  const R = { channel: 'U1', again: AGAIN, s: { requester: 'U1' } };
  let q = await j1('Question DM', [{ json: { ok: false } }], { 'Read Step 2': [{ json: R }], 'After Prepare': [{ json: { warn: 'Did you mean *Harold Orozco*? Or press *Book* again to keep "Harold Orazco" as a new client.' } }] });
  const btns = q.blocks[1].elements;
  ok(btns[0].action_id === 'book_continue' && btns[0].text.text === 'Continue booking' && JSON.parse(btns[0].value).c === 'Harold Orazco' && btns[1].action_id === 'my_bookings', 'Continue booking (with what was filled in) + My bookings');
  q = await j1('Result DM', [{ json: { ok: false } }], { 'Read Step 2': [{ json: R }], 'After Book': [{ json: { ok: false, warn: 'Studio 8 is taken then.' } }] });
  ok(q.blocks[1].elements[0].action_id === 'book_continue', '"Not booked" (a taken room): Continue booking too');
  q = await j1('Question DM', [{ json: { ok: false } }], { 'Read Step 2': [{ json: { channel: 'U1', again: { d: '2027-10-28' } } }], 'After Prepare': [{ json: { warn: 'x' } }] });
  ok(q.blocks[1].elements[0].action_id === 'open_book' && q.blocks[1].elements[0].text.text === 'Book a room', 'the answers not all there -> Book a room, as before');
  const sd = si.nodes.find(n => n.name === 'Series DM').parameters.jsCode;
  ok(/action_id: 'open_book', value: again\(R\), text: \{ type: 'plain_text', text: 'Book a room' \}/.test(sd) && !/book_continue/.test(sd), 'a repeating booking keeps Book a room (its dates are not on the button)');
  console.log('The click');
  const route = async (payload) => (await j1('Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_actions', actions: [{ action_id: 'book_continue', value: JSON.stringify(AGAIN) }] }) === 5 && nx('Route').split(' | ')[5] === 'Timings 1' && nx('Timings 1') === 'Read Step 1', 'routed with step 1\'s answers (route 5 -> Read Step 1)');
  const pay = { type: 'block_actions', actions: [{ action_id: 'book_continue', value: JSON.stringify(AGAIN) }], container: { channel_id: 'D1', message_ts: '7.7' } };
  const r1 = await j1('Read Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T9', channel: 'D1' } }], 'Read Request': [{ json: { payload: pay } }], 'Timings 1': [] });
  ok(r1.valid && r1.cont && r1.trigger_id === 'T9' && r1.s.date === '2027-10-28' && r1.s.t0 === '14:00' && r1.s.t1 === '16:00' && r1.s.purpose === 'Celebrity Recording' && r1.s.kind === 'studio'
     && r1.s.pre.c === 'Harold Orazco' && r1.s.msg.ts === '7.7' && r1.open.external_id === r1.s.ext && /Finding free rooms/.test(JSON.stringify(r1.open)), 'Read Step 1: the booking from the button, the waiting window to open', r1);
  ok(nx('Step 1 OK?') === 'Continue?' && nx('Continue?') === 'Open Continue | Read Cache 2' && nx('Open Continue') === 'Read Cache 2'
     && /views\.open/.test(si.nodes.find(n => n.name === 'Open Continue').parameters.url), 'Continue? -> Open Continue (views.open) -> Read Cache 2; step 1 as before -> Read Cache 2');
  const ad = await j1('Read Step 1', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T9', channel: 'D1' } }], 'Read Request': [{ json: { payload: Object.assign({}, pay, { actions: [{ action_id: 'book_continue', value: JSON.stringify({ d: '2027-10-28', ad: 1, p: 'Event', r: 'Lobby' }) }] }) } }], 'Timings 1': [] });
  ok(ad.valid && ad.s.allDay && ad.s.t0 === '00:00' && ad.s.t1 === '23:59' && ad.s.kind === 'meeting', 'an all-day Event continues all day');
  console.log('Step 2 again');
  const b2 = await j1('Build Step 2', [{ json: { status: 'OK', free_priority: ['Studio 8', 'Studio F'], busy: [] } }], { 'Read Step 1': [{ json: r1 }], 'Read Cache 2': cache, 'Loc Projects 2': [] }), v = b2.view;
  const val = id => { const b = v.blocks.find(x => x.block_id === id); return b ? (b.element.initial_value || ((b.element.initial_option || {}).value) || '') : null; };
  const radio = v.blocks.find(b => /^room(~\d+)?$/.test(b.block_id || '')); const rv = radio && ((radio.element || radio.elements[0]).initial_option || {}).value;
  ok(rv === 'Studio 8' && val('project') === 'test-me' && val('client') === 'Harold Orazco' && (b2.external_id || v.external_id) === r1.s.ext, 'Studio 8 picked, project and client filled in, into the waiting window', { rv, p: val('project'), c: val('client') });
  console.log('Booked from it');
  const ms = si.nodes.find(n => n.name === 'Mark Source').parameters.jsCode;
  const isOffer = new Function(ms.slice(ms.indexOf('function srcIsOffer'), ms.indexOf('\n', ms.indexOf('function srcIsOffer'))) + '\nreturn srcIsOffer;')();
  ok(isOffer([{ type: 'actions', elements: [{ action_id: 'book_continue', value: JSON.stringify(AGAIN) }] }]), 'that message counts as a source - it becomes "✅ Booked."');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + (e && e.stack || e)); process.exit(1); });
