#!/usr/bin/env node
// Slack Interactions v36 (21 Oct): shortcut buttons at the end of results (Book another / Book a room + My bookings), a
// booking's own message never used as the next booking's source, and Post Processing's "booked this for you" notice.
// Usage: node scripts/sim-shortcuts.js [slack-interactions v36] [main]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v36.json', 'utf8'));
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/imported/project-jessie-v277-imported.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const ids = bl => bl.map(x => x.block_id || x.type).join();
const nav = bl => { const n = bl.find(x => x.block_id === 'nav'); return n ? n.elements.map(e => e.action_id + ':' + e.value + ':' + e.text.text).join() : ''; };
const uniqueIds = bl => bl.every(b => { const a = (b.elements || []).map(e => e.action_id).filter(Boolean); return new Set(a).size === a.length; });   // gotcha 42

(async () => {
  console.log('Booked');
  const ab = await j1(si, 'After Book', [{ json: { status: 'CREATED', event_id: 'ev1', title: 'SONG / DR' } }], {
    'Read Step 2': [{ json: { s: { date: '2027-10-22', t0: '14:00', t1: '16:00', when: 'Friday, October 22, 2027 · 2:00 PM – 4:00 PM', purpose: 'VO Recording', kind: 'studio' }, room: 'Studio 7', viewId: 'V1', channel: 'D1' } }],
    'After Prepare': [{ json: { F: { Room: 'Studio 7' }, book: { start_iso: '2027-10-22T14:00:00+08:00', end_iso: '2027-10-22T16:00:00+08:00' } } }] });
  ok(ids(ab.blocks) === 'bk_ev1,bka_ev1,nav' && nav(ab.blocks) === 'open_book:menu:Book another,my_bookings:menu:My bookings' && uniqueIds(ab.blocks),
     'the Booked DM: card, Change / Cancel, then Book another / My bookings', ids(ab.blocks));
  ok(ab.view.blocks.every(b => b.type !== 'actions'), 'the form\'s result has no buttons (a button there would need a pushed view)');
  const ab0 = await j1(si, 'After Book', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED' } }], {
    'Read Step 2': [{ json: { s: {}, viewId: 'V1', channel: 'D1' } }], 'After Prepare': [{ json: { F: {}, book: {} } }], 'Read Request': [{ json: { payload: { view: { blocks: [], private_metadata: '{}' } } } }] });
  ok(ab0.ok === false && !ab0.blocks, 'not booked -> the form again, nothing added');

  console.log('Booked (series)');
  const abs = async res => j1(si, 'After Book Series', [{ json: res }], { 'Read Series Confirm': [{ json: { meta: { n: 2, title: 'SER / DR', time: '14:00-16:00', channel: 'D1' }, user: 'U1', viewId: 'V3' } }],
    'To Book Series': [{ json: { go: true, rooms: 'Studio 8' } }] });
  let X = await abs({ status: 'BOOKED_SERIES', booked: ['2027-10-19', '2027-10-26'], skipped: [], failed: [] });
  const btn = bl => bl.filter(b => b.type === 'actions').flatMap(b => b.elements.map(e => e.action_id + ':' + e.text.text)).join();
  ok(btn(X.blocks) === 'open_book:Book another,my_bookings:My bookings', 'booked -> Book another / My bookings', btn(X.blocks));
  X = await abs({ status: 'NONE_BOOKED', booked: [], skipped: ['2027-10-19', '2027-10-26'] });
  ok(btn(X.blocks) === 'open_book:Book a room,my_bookings:My bookings', 'nothing booked -> Book a room / My bookings');

  console.log('Changed');
  const am = await j1(si, 'After Move', [{ json: { status: 'MOVED', event_id: 'ev2' } }], {
    'Read Change': [{ json: { b: { id: 'ev1', d: '2027-10-22', s: '14:00', e: '16:00', r: 'Studio 7', t: 'SONG / DR' }, n: { d: '2027-10-22', s: '15:00', e: '17:00', r: 'Studio 7' }, viewId: 'V2', user: 'U1', meta: {} } }],
    'To Move': [{ json: {} }] });
  ok(ids(am.dmBlocks) === 'bk_ev2,bka_ev2,nav' && nav(am.dmBlocks) === 'open_book:menu:Book a room,my_bookings:menu:My bookings' && uniqueIds(am.dmBlocks), 'the Changed DM ends with Book a room / My bookings', ids(am.dmBlocks));

  console.log('Cancelled');
  const bval = JSON.stringify({ id: 'ev1', d: '2027-10-22', s: '14:00', e: '16:00', r: 'Studio 7', t: 'SONG / DR' });
  const cancel = async (blocks, res) => j1(si, 'After Cancel', [{ json: res || { status: 'CANCELLED' } }], { 'Read Request': [{ json: { payload: { actions: [{ value: bval }], message: { blocks, ts: '1' }, container: { channel_id: 'D1', message_ts: '1' } } } }] });
  let c = await cancel(ab.blocks);
  ok(ids(c.blocks) === 'bk_ev1,nav' && /Cancelled/.test(c.blocks[0].text.text) && nav(c.blocks) === 'open_book:menu:Book another,my_bookings:menu:My bookings', 'a v36 Booked DM cancelled -> its own buttons kept, none added', ids(c.blocks));
  const oldDm = ab.blocks.filter(b => b.block_id !== 'nav');
  c = await cancel(oldDm);
  ok(ids(c.blocks) === 'bk_ev1,nav' && nav(c.blocks) === 'open_book:menu:Book a room,my_bookings:menu:My bookings', 'a Booked DM from before v36 -> Book a room / My bookings added', ids(c.blocks));
  const list = [{ type: 'section', text: { type: 'mrkdwn', text: '*Your bookings*' } }].concat(oldDm, [{ type: 'actions', block_id: 'my_nav', elements: [{ action_id: 'my_page_prev' }, { action_id: 'my_page_next' }] }]);
  c = await cancel(list);
  ok(!c.blocks.some(b => b.block_id === 'nav'), 'My bookings (its own Previous / Next) -> nothing added');
  const rem = [{ type: 'section', text: { type: 'mrkdwn', text: 'Tomorrow' } }].concat(oldDm, [{ type: 'actions', elements: [{ action_id: 'my_bookings', value: 'menu' }] }]);
  c = await cancel(rem);
  ok(!c.blocks.some(b => b.block_id === 'nav'), 'a reminder (its own My bookings) -> nothing added');
  const two = oldDm.concat([{ type: 'section', block_id: 'bk_ev3', text: { type: 'mrkdwn', text: 'x' } }]);
  c = await cancel(two);
  ok(!c.blocks.some(b => b.block_id === 'nav'), 'a message with two bookings -> nothing added');
  c = await cancel(oldDm, { status: 'REJECTED', reason: 'LOOKUP_FAILED' });
  ok(!c.blocks.some(b => b.block_id === 'nav') && c.blocks.some(b => b.block_id === 'bka_ev1'), 'a failed cancel -> the row and its buttons kept, nothing added');

  console.log('Book another on a Booked message');
  const rs2 = { s: { date: '2027-10-23', t0: '10:00', t1: '12:00', msg: { ch: 'D1', ts: '9.9' } }, rooms: 'Studio 8' };
  const M = await j1(si, 'Mark Source', [{ json: { ok: true, messages: [{ ts: '9.9', text: 'Booked', blocks: ab.blocks }] } }], { 'Read Step 2': [{ json: rs2 }] });
  ok(M.ok === false, 'the Booked card is left as it is (the new booking\'s result comes as its own DM)');
  ok((await run(si, 'Source Done', [], { 'Mark Source': [{ json: M }], 'After Book': [{ json: { ok: true } }] })).length === 0, '… and nothing is put back over it after');
  const menuMsg = { ts: '9.9', text: 'Hi', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Hi, I’m Jessie!' } }, { type: 'actions', elements: [{ action_id: 'open_book', value: 'menu' }, { action_id: 'my_bookings', value: 'menu' }] }] };
  const M2 = await j1(si, 'Mark Source', [{ json: { ok: true, messages: [menuMsg] } }], { 'Read Step 2': [{ json: rs2 }] });
  ok(M2.ok === true && /Booking…/.test(JSON.stringify(M2.blocks)), 'the menu still shows "Your booking details: … ⏳ Booking…"');
  const MS = await j1(si, 'Mark Source Series', [{ json: { ok: true, messages: [{ ts: '9.9', blocks: ab.blocks }] } }], {
    'Read Series Confirm': [{ json: { meta: { msg: { ch: 'D1', ts: '9.9' }, rooms: 'Studio 8', dates: '2027-10-19', time: '10:00-12:00' }, user: 'U1' } }], 'Read Step 2': [{ json: rs2 }] });
  ok(MS.ok === false, 'a series started from a Booked card leaves it too');

  console.log('main reads the buttons as the menu');
  const mc = jsOf(main, 'Menu Check');
  ok(/lastButtons\.some\(x => x === 'open_book:m'\)/.test(mc) && /x === 'open_book:\{'/.test(mc), 'Menu Check: open_book "menu" = the menu (an opener), only a JSON value is an offer (gotcha 44)');
  const fo = jsOf(main, 'Form Offer');
  ok(/e\.action_id === 'open_book' && \/\^\\\{\/\.test/.test(fo), 'Form Offer: only a JSON value carries details');

  console.log('Post Processing: who it is for is told');
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: [], sessionTypes: [],
    bookers: [{ id: 'b1', fields: { Name: 'Howard Luistro', 'Slack User ID': 'U08V3CKDGJF' } }, { id: 'b2', fields: { Name: 'Dilan Diaz', 'Slack User ID': 'U4' } }] }) } }];
  const bn = await run(si, 'Booked Notices', [], { 'Read Step 2': [{ json: { s: { requester: 'U08V3CKDGJF', kind: 'post' }, engineerId: 'U4', arrangerId: '', forId: '' } }],
    'After Book': [{ json: { text: '✅ *Booked.*\n\n*POST PROCESSING - TRAILER / Dilan*', blocks: ab.blocks } }], 'Read Cache 3': cache });
  const t = bn.map(i => JSON.stringify(i.json)).join();
  ok(bn.length === 1 && /Howard Luistro booked this for you/.test(t) && !/as the engineer/.test(t), 'Post Processing for Dilan -> "Howard Luistro booked this for you."', t.slice(0, 300));
  const bn2 = await run(si, 'Booked Notices', [], { 'Read Step 2': [{ json: { s: { requester: 'U08V3CKDGJF', kind: 'studio' }, engineerId: 'U4', arrangerId: '', forId: '' } }],
    'After Book': [{ json: { text: '✅ *Booked.*\n\n*SONG / DD*', blocks: ab.blocks } }], 'Read Cache 3': cache });
  ok(/booked you as the engineer/.test(JSON.stringify(bn2)), 'a studio session -> "booked you as the engineer" as before');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
