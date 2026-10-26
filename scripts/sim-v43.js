#!/usr/bin/env node
// Slack Interactions v43 (QA round 4): Z1 - two cancels from one list, one right after the other, both end "❌ Cancelled."
// (each update reads the message as it is; the click's copy is stale); Keep and a change that failed touch only their own
// booking. Q3 - "REQUEST-QA / AEG" opens Change / Move my booking with the Project title filled in.
// Usage: node scripts/sim-v43.js [slack-interactions v43]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v43.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (!si.nodes.some(n => n.name === 'Get Message C2')) { console.log('0 ok, 0 failed (an older build: v43 not in it)'); process.exit(0); }
async function run(name, input, outs) { const js = si.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] }); const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input); }
const C = si.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');
const row = (id, t) => [{ type: 'section', block_id: 'bk_' + id, text: { type: 'mrkdwn', text: '*' + t + '*\nWed, Oct 27 · 2:00 PM – 4:00 PM · Studio 7' } },
  { type: 'actions', block_id: 'bka_' + id, elements: [{ type: 'button', action_id: 'bk_change', value: '{}' }, { type: 'button', action_id: 'bk_cancel', value: '{}' }] }];
const M0 = [{ type: 'section', text: { type: 'mrkdwn', text: '*Your bookings* · Tue, Oct 26 – Mon, Nov 1' } }].concat(row('A', 'QA-POST MIXING / RG'), row('B', 'REQUEST-QA / AEG'));
const B = id => ({ id, d: '2027-10-27', s: '14:00', e: '16:00', r: 'Studio 7', t: id === 'A' ? 'QA-POST MIXING / RG' : 'REQUEST-QA / AEG', st: 'VO Recording' });
const req = (id, copy) => [{ json: { payload: { actions: [{ action_id: 'bk_cancel_go', value: JSON.stringify(B(id)) }], container: { channel_id: 'D1', message_ts: '9.9' }, message: { ts: '9.9', text: 'Your bookings', blocks: copy } } } }];
const read = blocks => [{ json: { ok: true, messages: [{ ts: '9.9', text: 'Your bookings', blocks }] } }];
const state = bl => ['A', 'B'].map(id => { const r = bl.find(x => x.block_id === 'bk_' + id), w = bl.find(x => x.block_id === 'bkw_' + id), a = bl.find(x => x.block_id === 'bka_' + id);
  return id + ':' + (/Cancelled/.test(JSON.stringify(r || '')) ? 'cancelled' : w ? 'working' : a ? 'buttons' : '?'); }).join(' ');

(async () => {
  console.log('Z1 - two cancels, one right after the other (22 Oct)');
  ok(nx('Ack Cancel') === 'Get Message C' && nx('Get Message C') === 'Mark Cancelling' && nx('Cancel') === 'Get Message C2' && nx('Get Message C2') === 'After Cancel'
     && nx('Ack Keep') === 'Get Message K' && nx('Get Message K') === 'Keep Row' && /Restore Message/.test(nx('Get Message R')) && nx('Get Message RA') === 'Restore Asked',
     'each update reads the message first');
  ok(si.nodes.filter(n => /^Get Message (C|C2|K|R|RA)$/.test(n.name)).every(n => n.onError === 'continueRegularOutput' && /conversations\.history/.test(n.parameters.url)), 'a failed read never stops it (the click\'s copy then)');
  // A: pressed on M0
  const mcA = (await run('Mark Cancelling', read(M0), { 'Read Request': req('A', M0) }))[0].json; const M1 = mcA.blocks;
  ok(state(M1) === 'A:working B:buttons', 'A: ⏳ Cancelling…', state(M1));
  // B pressed now - Slack's copy is M1 (A still working); then A finishes
  const acA = (await run('After Cancel', read(M1), { 'Read Request': req('A', M0), 'Cancel': [{ json: { status: 'CANCELLED' } }] }))[0].json; const M2 = acA.blocks;
  ok(state(M2) === 'A:cancelled B:buttons', 'A: ❌ Cancelled.', state(M2));
  const mcB = (await run('Mark Cancelling', read(M2), { 'Read Request': req('B', M1) }))[0].json; const M3 = mcB.blocks;
  ok(state(M3) === 'A:cancelled B:working', 'B: ⏳ Cancelling… - A stays ❌ Cancelled. (was put back to ⏳ Cancelling…)', state(M3));
  const acB = (await run('After Cancel', read(M3), { 'Read Request': req('B', M1), 'Cancel': [{ json: { status: 'CANCELLED' } }] }))[0].json;
  ok(state(acB.blocks) === 'A:cancelled B:cancelled', 'both end ❌ Cancelled.', state(acB.blocks));
  const old = (await run('After Cancel', [{ json: { error: 'x' } }], { 'Read Request': req('B', M1), 'Cancel': [{ json: { status: 'CANCELLED' } }] }))[0].json;
  ok(state(old.blocks) === 'A:working B:cancelled', 'the read failed -> the click\'s copy, as before (no worse)');
  const nf = (await run('After Cancel', read(M3), { 'Read Request': req('B', M1), 'Cancel': [{ json: { status: 'REJECTED', reason: 'NOT_YOURS' } }] }))[0].json;
  ok(!nf.ok && /Only the booker/.test(JSON.stringify(nf.blocks)) && state(nf.blocks).startsWith('A:cancelled'), 'not cancelled -> says why, A untouched');
  console.log('Keep');
  const kp = (await run('Keep Row', read(M2), { 'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_keep', value: JSON.stringify({ id: 'B', w: 'weekly' }) }], container: { channel_id: 'D1', message_ts: '9.9' }, message: { ts: '9.9', blocks: M0 } } } }] }))[0].json;
  ok(state(kp.blocks) === 'A:cancelled B:?' && /Keeping it/.test(JSON.stringify(kp.blocks)), 'Keep on B (copy taken before A was cancelled) -> A stays ❌ Cancelled.', state(kp.blocks));
  console.log('A change that did not go through');
  const orig = M0, now = M2.map(x => x.block_id === 'bka_B' ? null : x).filter(Boolean).concat([]);
  const nowB = JSON.parse(JSON.stringify(M2)); nowB.splice(nowB.findIndex(x => x.block_id === 'bka_B'), 1, { type: 'context', block_id: 'bkw_B', elements: [{ type: 'mrkdwn', text: '⏳ Changing…' }] });
  const rs = (await run('Restore Message', read(nowB), { 'After Move': [{ json: { ok: false } }], 'Mark Changing': [{ json: { ok: true, channel: 'D1', ts: '9.9', original: orig, text: 'x' } }], 'Read Change': [{ json: { b: { id: 'B' } } }] }))[0].json;
  ok(state(rs.blocks) === 'A:cancelled B:buttons', 'B back with its buttons, A stays ❌ Cancelled. (was the whole old message)', state(rs.blocks));
  const ra = (await run('Restore Asked', read(nowB), { 'Mark Changing': [{ json: { ok: true, channel: 'D1', ts: '9.9', original: orig, text: 'x' } }], 'Read Change': [{ json: { b: { id: 'B' } } }] }))[0].json;
  ok(state(ra.blocks) === 'A:cancelled B:buttons', 'the same when it stops at a question');
  console.log('Q3 - the project title kept');
  const bookers = [{ id: 'b1', fields: { Name: 'Angelo Gan', Initials: 'AEG', 'Slack User ID': 'U7', Info: 'Post Engineer', Department: ['Audio Post'] } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes.concat([{ id: 'stl', fields: { Type: 'Localization Dubbing', Priority: [], 'Last Resort': [], 'Engineer Role Required': ['Loc Engineer'], 'Room Requirements': 'vocal booth' } }]), bookers }) } }];
  const bc = async (b, aid) => { const v = (await run('Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { actions: [{ action_id: aid || 'bk_change', value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1.1' } } } }] }))[0].json.view;
    const f = id => { const x = v.blocks.find(y => y.block_id === id); return x ? (x.element.initial_value || '') : null; }; return { project: f('det_project'), client: f('det_client'), code: f('det_code') }; };
  let f = await bc({ id: 'e1', d: '2027-10-27', s: '14:00', e: '15:30', r: 'Studio F', t: 'REQUEST-QA / AEG', st: 'VO Recording', rid: 'R1', w: 'a1' }, 'cr_move');
  ok(f.project === 'REQUEST-QA' && f.client === '' && f.code === null, 'Move my booking on "REQUEST-QA / AEG" (Q3): Project title REQUEST-QA', f);
  f = await bc({ id: 'e2', d: '2027-10-27', s: '14:00', e: '16:00', r: 'Studio 7', t: 'QA-POST MIXING / RG', st: 'VO Recording' });
  ok(f.project === 'QA-POST MIXING', 'Change on "QA-POST MIXING / RG": Project title kept', f);
  f = await bc({ id: 'e3', d: '2027-10-27', s: '14:00', e: '16:00', r: 'Studio 7', t: 'ORANGE / Jem Lim / AEG', st: 'VO Recording' });
  ok(f.project === 'ORANGE' && f.client === 'Jem Lim', 'with a client - as before');
  f = await bc({ id: 'e4', d: '2027-10-27', s: '14:00', e: '16:00', r: 'Studio 7', t: 'TEST-QA-01 / AEG', st: 'Localization Dubbing' });
  ok(f.code === 'TEST-QA-01' && f.project === null, 'a Localization booking: its code, as before');
  f = await bc({ id: 'e5', d: '2027-10-27', s: '14:00', e: '16:00', r: 'Studio 7', t: 'NFX123 / AEG', st: 'Localization Dubbing' });
  ok(f.code === 'NFX123', 'a Localization code with no hyphen: filled too (was empty)', f);
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + (e && e.stack || e)); process.exit(1); });
