#!/usr/bin/env node
// Jessie — Reminders v11 (PENDING 155 follow-up): a booking made by hand gets a reminder too - to its creator when that is one of a
// booker's emails (Email / Alt email), with or without a ref:. Runs the real Build Reminders; made-up people.
//   node scripts/sim-reminders-hand-made.js [reminders v11] [reminders v10]
const fs = require('fs');
const L = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const RM = L(process.argv[2], 'workflows/reminders-v11.json'), RM0 = L(process.argv[3], 'workflows/reminders-v10.json');
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const run = async (wf, outs) => new Function('$', '$input', 'return (async function(){' + node(wf, 'Build Reminders').parameters.jsCode + '\n})();')(
  n => { if (outs[n] === undefined) throw new Error(n + ' not executed'); return { first: () => outs[n][0], all: () => outs[n] }; }, { first: () => ({ json: {} }), all: () => [] });
const B = (id, name, slack, email, alt) => ({ id, fields: Object.assign({ Name: name, Initials: 'X', 'Slack User ID': slack, Info: 'Coordinator', Department: ['Music'], Email: email }, alt ? { 'Alt email': alt } : {}) });
const bookers = [B('b1', 'Coord Person', 'UCOORD01', 'coord@example.com', 'coord.alt@example.com'), B('b2', 'Other Person', 'UOTHER01', 'other@example.com'), B('b3', 'Eng Person', 'UENG0001', 'eng@example.com')];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const S7 = { email: 'c_188dupcj6cqfaipohqffj07ruq8de@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio 7 (7)', resource: true, responseStatus: 'accepted' };
const EV = (id, title, creator, desc) => ({ id, summary: title, start: { dateTime: '2026-11-20T14:00:00+08:00' }, end: { dateTime: '2026-11-20T16:00:00+08:00' },
  location: 'KDC Plaza-Top Level-Studio 7 (7)', attendees: [S7], creator: { email: creator }, description: desc || '' });
const items = [EV('h1', 'TENTATIVE ISR - ONE GYEOMI', 'coord.alt@example.com'),                                   // hand-made by the coordinator, no description
  EV('h2', 'ISR - OTHER HAND', 'outsider@example.com'),                                                         // hand-made by someone not in Bookers
  EV('j1', 'JESSIE / EP', 'jessie-service@example.com', 'Engineer: Eng Person | Booked by: Other Person | ref: UOTHER01'),   // through Jessie
  EV('b1', 'BACKFILLED FOR OTHER', 'coord@example.com', 'Booked by: Other Person | ref: UOTHER01 | Dept: Music')];   // made by the coordinator, tagged to someone else
const W1 = { kind: 'daily', start: '2026-11-20', end: '2026-11-21' };
(async () => {
  const out = await run(RM, { 'Window': [{ json: W1 }], 'List Events R': [{ json: { items } }], 'Read Cache R': cache });
  const to = id => out.map(i => i.json).find(j => j.person === id);
  const ids = j => j ? j.blocks.filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id.slice(3)).sort().join() : '';
  ok(ids(to('UCOORD01')) === 'b1,h1', 'the coordinator: her hand-made booking (no description) and the one she made for someone else', ids(to('UCOORD01')));
  ok(ids(to('UOTHER01')) === 'b1,j1', 'the other person: the Jessie booking and the one tagged to them (ref:), as before', ids(to('UOTHER01')));
  ok(ids(to('UENG0001')) === 'j1', 'the engineer named on the Jessie booking, as before', ids(to('UENG0001')));
  ok(!out.some(i => JSON.stringify(i.json.blocks).includes('bk_h2')), 'a hand-made booking by someone not in Bookers -> no reminder (nobody to send it to)');
  const old = await run(RM0, { 'Window': [{ json: W1 }], 'List Events R': [{ json: { items } }], 'Read Cache R': cache });
  ok(!old.some(i => JSON.stringify(i.json.blocks).includes('bk_h1')), 'v10 (live): the hand-made booking got no reminder');
  const same = id => JSON.stringify((old.map(i => i.json).find(j => j.person === id) || {}).blocks) === JSON.stringify((to(id) || {}).blocks);
  ok(same('UOTHER01') && same('UENG0001'), 'everyone else\'s reminder is exactly v10\'s');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
