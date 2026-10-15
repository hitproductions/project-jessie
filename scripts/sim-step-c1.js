#!/usr/bin/env node
// Step C1 offline (Slack Interactions v11 + Cancel Booking v27 + Move Booking v30): the routes; Change / Cancel on the
// Booked DM; My bookings (whose, the note, paging, errors); Cancel (inputs, the message updated in place, refusals);
// the Change form (current values, rooms of the same kind, nothing changed, the working view), Move's inputs, Changed /
// the problem with free times, the message's row updated; the team rule in Cancel and Move.
// Usage: node scripts/sim-step-c1.js [slack interactions v11] [cancel v27] [move v30]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v16.json', 'utf8'));
const cx = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/cancel-booking-v27.json', 'utf8'));
const mv = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/move-booking-v30.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;

(async () => {
  const R = (id, name, extra) => ({ id, fields: Object.assign({ 'Room Name': name }, extra || {}) });
  const rooms = [R('r7', 'Studio 7'), R('r8', 'Studio 8'), R('rf', 'Studio F'), R('r10', 'Studio 1'), R('rl', 'Likha', { 'Room Type': ['Conference Room'] }),
    R('rs', 'Salin', { 'Room Type': ['Conference Room'] }), R('m4', 'M4'), R('m1', 'M1')];
  const bookers = [{ fields: { Name: 'Howard Luistro', 'Slack User ID': 'U1', Authority: [{ name: 'HAIST Dev' }], Department: [{ name: 'Audio Post' }] } },
    { fields: { Name: 'Daryl Reyes', 'Slack User ID': 'U2', Authority: ['Standard'], Department: ['Music'] } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes: [], bookers }) } }];
  const chk = u => [{ json: { user: u || 'U1', triggerId: 'T1', channel: 'D1' } }];
  const B = { id: 'ev1', d: '2027-10-16', s: '14:00', e: '16:00', r: 'Studio 7', t: 'ORANGE / Jem Lim / HL' };

  // ---- routes
  const route = async (payload) => (await j1(si, 'Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_actions', actions: [{ action_id: 'bk_cancel' }] }) === 9 && await route({ type: 'block_actions', actions: [{ action_id: 'bk_change' }] }) === 10
     && await route({ type: 'view_submission', view: { callback_id: 'change_booking' } }) === 11 && await route({ type: 'block_actions', actions: [{ action_id: 'my_page' }] }) === 12
     && await route({ type: 'block_actions', actions: [{ action_id: 'my_bookings' }] }) === 7, 'routes: cancel 9, change 10, change submit 11, page 12, my bookings 7');
  const C = si.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');
  ok(C.Route.main[7][0].node === 'Ack My Bookings' && C.Route.main[12][0].node === 'Ack My Bookings' && nx('Page?') === 'Update List | Post List', 'wiring: My bookings posts, a page updates');
  ok(nx('To Cancel') === 'Cancel' && nx('Cancel') === 'After Cancel' && nx('After Cancel') === 'Update Cancelled', 'wiring: cancel');
  ok(nx('Change OK?') === 'Read Cache 7' && nx('After Move') === 'Show Change Result' && nx('Moved?') === 'Get Message' && nx('Fix Message') === 'Update Changed', 'wiring: change');
  ok(si.nodes.find(n => n.name === 'Cancel').parameters.workflowId.value === 'bAyDw7udhmY0NL38' && si.nodes.find(n => n.name === 'Move').parameters.workflowId.value === 't7lwR2km4tfN8DbM', 'Cancel / Move Booking ids');

  // ---- the Booked DM carries Change / Cancel
  const F = { Title: B.t, Date: 'Saturday, October 16, 2027', Time: '2:00 PM – 4:00 PM', Room: 'Studio 7' };
  const ab = await j1(si, 'After Book', [{ json: { status: 'CREATED', event_id: 'ev1', title: B.t } }], {
    'Read Step 2': [{ json: { viewId: 'V1', channel: 'U1', room: 'Studio 7', s: { date: '2027-10-16', t0: '14:00', t1: '16:00', when: '' } } }],
    'After Prepare': [{ json: { F, book: { start_iso: '2027-10-16T14:00:00+08:00', end_iso: '2027-10-16T16:00:00+08:00' } } }], 'Read Request': [{ json: { payload: {} } }] });
  ok(ab.blocks[0].block_id === 'bk_ev1' && ab.blocks[0].text.text === ab.text && ab.blocks[1].block_id === 'bka_ev1', 'Booked DM: the card, then its buttons');
  const btns = ab.blocks[1].elements;
  ok(btns.map(x => x.action_id).join() === 'bk_change,bk_cancel' && JSON.stringify(JSON.parse(btns[0].value)) === JSON.stringify(B), 'buttons carry the booking - ' + btns[0].value);
  ok(btns[1].style === 'danger' && btns[1].confirm.title.text === 'Cancel this booking?' && btns[1].confirm.confirm.text === 'Cancel booking' && btns[1].confirm.deny.text === 'Keep it'
     && /ORANGE \/ Jem Lim \/ HL\*\nSat, Oct 16 · 2:00 PM – 4:00 PM · Studio 7/.test(btns[1].confirm.text.text), 'Cancel asks first (Slack pop-up)');
  ok(/"blocks: \$\('After Book'\)/.test(JSON.stringify(si.nodes.find(n => n.name === 'DM Booked').parameters.jsonBody)) || /blocks/.test(si.nodes.find(n => n.name === 'DM Booked').parameters.jsonBody), 'DM Booked sends the blocks');

  // ---- My bookings
  const win = async (a) => j1(si, 'My Window', [], { 'Check Signature': chk(), 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [a], container: { channel_id: 'D1', message_ts: '5.5' } } } }] });
  let W = await win({ action_id: 'my_bookings', value: 'menu' });
  const m = new Date(Date.now() + 8 * 3600e3);
  ok(!W.page && W.start === (m.getUTCFullYear() + 1) + '-' + String(m.getUTCMonth() + 1).padStart(2, '0') + '-' + String(m.getUTCDate()).padStart(2, '0')
     && W.timeMin === W.start + 'T00:00:00+08:00' && W.channel === 'D1', 'menu: from today (a year ahead in QA), 7 days');
  W = await win({ action_id: 'my_page', value: '2027-10-22' });
  ok(W.page && W.start === '2027-10-22' && W.end === '2027-10-29' && W.ts === '5.5', 'a page button: its week, the same message');
  const ev = (id, s, e, desc, extra) => Object.assign({ id, summary: 'T-' + id, start: { dateTime: s }, end: { dateTime: e }, description: desc,
    attendees: [{ email: 'x@resource.calendar.google.com', resource: true, displayName: 'KDC Plaza-Top Level-Studio 7 (8)' }] }, extra || {});
  const items = [
    ev('b', '2027-10-23T10:00:00+08:00', '2027-10-23T12:00:00+08:00', 'Engineer: Howard Luistro | Booked by: Daryl Reyes | ref: U2 | team: U1'),
    ev('a', '2027-10-22T14:00:00+08:00', '2027-10-22T16:00:00+08:00', 'Booked by: Howard Luistro | ref: U1'),
    ev('c', '2027-10-24T09:00:00+08:00', '2027-10-24T10:00:00+08:00', 'Booked by: Someone | ref: U9'),
    ev('d', '2027-10-25T09:00:00+08:00', '2027-10-25T10:00:00+08:00', 'Booked by: Howard Luistro | ref: U1', { status: 'cancelled' }),
    { id: 'h', summary: 'M4 - Howard', start: { date: '2027-10-26' }, end: { date: '2027-10-27' }, location: 'M4', description: 'ref: U1' }];
  const render = async (res, Wx) => j1(si, 'Render My Bookings', [{ json: res }], { 'My Window': [{ json: Wx || W }], 'Read Cache 4': cache });
  let L = await render({ items });
  const secs = L.blocks.filter(b => /^bk_/.test(b.block_id || ''));
  ok(secs.map(b => b.block_id).join() === 'bk_a,bk_b,bk_h', 'mine and the team\'s, in time order; not someone else\'s, not cancelled - ' + secs.map(b => b.block_id).join());
  ok(secs[0].text.text === '*T-a*\nFri, Oct 22 · 2:00 PM – 4:00 PM · Studio 7' && /_You’re engineering_/.test(secs[1].text.text) && /all day · M4/.test(secs[2].text.text), 'rows: title, when, room; "You’re engineering"; all day');
  ok(L.blocks.filter(b => /^bka_/.test(b.block_id || '')).length === 3 && /\*Your bookings\* · Fri, Oct 22 – Thu, Oct 28/.test(L.blocks[0].text.text), 'each with Change / Cancel; the week in the header');
  const nav = L.blocks.find(b => b.block_id === 'my_nav').elements;
  ok(nav[0].value === '2027-10-15' && nav[1].value === '2027-10-29' && nav[0].text.text === '← Previous 7 days' && L.page && L.ts === '5.5', 'Previous / Next 7 days');
  // v16 (live: My bookings never showed): Slack refuses a block whose elements repeat an action_id
  ok(L.blocks.every(b => !b.elements || new Set(b.elements.map(e => e.action_id).filter(Boolean)).size === b.elements.filter(e => e.action_id).length),
     'every block\'s buttons have their own action_id (Slack refuses repeats) - ' + JSON.stringify(nav.map(e => e.action_id)));
  if (si.nodes.some(n => n.name === 'Report List')) {
    ok(await route({ type: 'block_actions', actions: [{ action_id: 'my_page_next' }] }) === 12 && await route({ type: 'block_actions', actions: [{ action_id: 'my_page_prev' }] }) === 12, 'v16: Previous / Next route to the page');
    const W2 = await win({ action_id: 'my_page_next', value: '2027-10-29' });
    ok(W2.page && W2.start === '2027-10-29', 'v16: the page button\'s week');
    const rep = async (res) => run(si, 'Report List', [{ json: res }], { 'Check Signature': chk() });
    ok((await rep({ ok: true })).length === 0 && /invalid_blocks/.test((await rep({ ok: false, error: 'invalid_blocks' }))[0].json.text), 'v16: Slack refusing the message -> a DM saying why');
    ok(nx('Post List') === 'Report List' && nx('Update List') === 'Report List' && nx('Report List') === 'DM List Failed', 'v16 wiring');
  }
  L = await render({ items: [] });
  ok(L.blocks.some(b => b.text && b.text.text === 'Nothing booked these 7 days.'), 'none -> said');
  L = await render({ error: { message: 'boom' } });
  ok(L.blocks.some(b => b.text && /couldn’t be read/.test(b.text.text)) && L.blocks.some(b => b.block_id === 'my_nav'), 'calendar error -> said, paging kept');
  const many = Array.from({ length: 25 }, (_, i) => ev('m' + i, '2027-10-22T' + String(8 + (i % 12)).padStart(2, '0') + ':00:00+08:00', '2027-10-22T20:00:00+08:00', 'ref: U1'));
  L = await render({ items: many, nextPageToken: 'x' });
  ok(L.blocks.length <= 50 && L.blocks.filter(b => /^bk_/.test(b.block_id || '')).length === 20 && /first 20 of 25/.test(JSON.stringify(L.blocks)) && /may be missing/.test(JSON.stringify(L.blocks)), 'at most 20 rows (Slack: 50 blocks); a partial read said');

  // ---- Cancel
  const msg = { text: 'Your bookings', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'head' } }, { type: 'section', block_id: 'bk_ev1', text: { type: 'mrkdwn', text: 'row' } },
    { type: 'actions', block_id: 'bka_ev1', elements: [] }, { type: 'section', block_id: 'bk_ev2', text: { type: 'mrkdwn', text: 'other' } }, { type: 'actions', block_id: 'bka_ev2', elements: [] }] };
  const cpay = { type: 'block_actions', actions: [{ action_id: 'bk_cancel', value: JSON.stringify(B) }], container: { channel_id: 'D1', message_ts: '7.7' }, message: msg };
  const tc = await j1(si, 'To Cancel', [], { 'Check Signature': chk(), 'Read Request': [{ json: { payload: cpay } }], 'Read Cache 5': cache });
  ok(tc.event_id === 'ev1' && tc.booking_date === '2027-10-16' && tc.title === B.t && tc.confirmed === true && tc.requester === 'U1' && tc.requester_name === 'Howard Luistro'
     && tc.authority === 'HAIST Dev' && tc.department === 'Audio Post' && tc.booking_time === '14:00', 'Cancel Booking inputs: the id on its date, confirmed, who is asking');
  let ac = await j1(si, 'After Cancel', [{ json: { status: 'CANCELLED' } }], { 'Read Request': [{ json: { payload: cpay } }] });
  ok(ac.ok && ac.channel === 'D1' && ac.ts === '7.7' && ac.blocks.find(b => b.block_id === 'bk_ev1').text.text === '❌ *Cancelled:* ORANGE / Jem Lim / HL\nSat, Oct 16 · 2:00 PM – 4:00 PM · Studio 7'
     && !ac.blocks.some(b => b.block_id === 'bka_ev1') && ac.blocks.some(b => b.block_id === 'bka_ev2'), 'cancelled -> the row says so, its buttons go, the others stay');
  ac = await j1(si, 'After Cancel', [{ json: { status: 'REJECTED', reason: 'NOT_YOURS' } }], { 'Read Request': [{ json: { payload: cpay } }] });
  const wi = ac.blocks.findIndex(b => b.block_id === 'bkw_ev1');
  ok(!ac.ok && wi === ac.blocks.findIndex(b => b.block_id === 'bka_ev1') + 1 && /only the person who booked it, or its engineer or arranger/.test(ac.blocks[wi].elements[0].text), 'refused -> why, under the row; the row stays');
  const again = Object.assign({}, cpay, { message: { blocks: ac.blocks } });
  ac = await j1(si, 'After Cancel', [{ json: { status: 'REJECTED', reason: 'LOOKUP_FAILED' } }], { 'Read Request': [{ json: { payload: again } }] });
  ok(ac.blocks.filter(b => b.block_id === 'bkw_ev1').length === 1 && /couldn’t be read/.test(ac.blocks.find(b => b.block_id === 'bkw_ev1').elements[0].text), 'a second problem replaces the first');

  // ---- Change form
  const chpay = { type: 'block_actions', trigger_id: 'T9', actions: [{ action_id: 'bk_change', value: JSON.stringify(B) }], container: { channel_id: 'D1', message_ts: '7.7' } };
  let bc = await j1(si, 'Build Change', [], { 'Check Signature': chk(), 'Read Request': [{ json: { payload: chpay } }], 'Read Cache 6': cache });
  let V = bc.view; const el = id => V.blocks.find(b => b.block_id === id).element;
  ok(bc.trigger_id === 'T1' && V.callback_id === 'change_booking' && V.submit.text === 'Change' && V.title.text === 'Change booking', 'the Change form');
  ok(el('date').initial_date === '2027-10-16' && el('start').initial_option.value === '14:00' && el('end').initial_option.value === '16:00' && el('room').initial_option.value === 'Studio 7',
     'starts at the booking\'s current date, times and room');
  ok(el('room').options.map(o => o.value).join() === 'Studio 7,Studio 1,Studio 8,Studio F', 'rooms: the current one first, then the other studios - ' + el('room').options.map(o => o.value).join());
  ok(/Now: Sat, Oct 16 · 2:00 PM – 4:00 PM · Studio 7/.test(V.blocks[0].text.text) && JSON.parse(V.private_metadata).ts === '7.7', 'shows Now; remembers the message');
  const Bm = Object.assign({}, B, { r: 'M4', s: '10:15', e: '11:45' });
  bc = await j1(si, 'Build Change', [], { 'Check Signature': chk(), 'Read Request': [{ json: { payload: Object.assign({}, chpay, { actions: [{ action_id: 'bk_change', value: JSON.stringify(Bm) }] }) } }], 'Read Cache 6': cache });
  V = bc.view;
  ok(el('room').options.map(o => o.value).join() === 'M4,M1' && el('start').initial_option.value === '10:15' && el('start').options.length === 50, 'an M booth -> M booths; an off-half-hour time kept');
  const sub = (d, s, e, r) => ({ type: 'view_submission', view: { id: 'V5', private_metadata: JSON.stringify({ b: B, ch: 'D1', ts: '7.7' }), state: { values: {
    date: { date_pick: { selected_date: d } }, start: { start_pick: { selected_option: { value: s } } }, end: { end_pick: { selected_option: { value: e } } }, room: { room_pick: { selected_option: { value: r } } } } } } });
  const readC = async (pl) => j1(si, 'Read Change', [], { 'Check Signature': chk(), 'Read Request': [{ json: { payload: pl } }] });
  let rc = await readC(sub('2027-10-16', '14:00', '16:00', 'Studio 7'));
  ok(!rc.valid && rc.answer.response_action === 'errors' && rc.answer.errors.date === 'Nothing changed - pick a new date, time or room.', 'nothing changed -> said on the form, nothing moved');
  rc = await readC(sub('2027-10-16', '16:00', '15:00', 'Studio 7'));
  ok(!rc.valid && /after the start/.test(rc.answer.errors.end), 'end before start -> error');
  rc = await readC(sub('2027-10-16', '15:00', '17:00', 'Studio 7'));
  ok(rc.valid && rc.answer.response_action === 'update' && /Changing ORANGE \/ Jem Lim \/ HL…\*\nSat, Oct 16 · 3:00 PM – 5:00 PM · Studio 7/.test(rc.answer.view.blocks[0].text.text)
     && /This takes a few seconds\./.test(JSON.stringify(rc.answer.view)), 'valid -> "Changing…" at once');
  const tm = await j1(si, 'To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache });
  ok(tm.event_id === 'ev1' && tm.booking_date === '2027-10-16' && tm.new_start_iso === '2027-10-16T15:00:00+08:00' && tm.new_end_iso === '2027-10-16T17:00:00+08:00'
     && tm.new_rooms === '' && tm.confirmed === true && tm.authority === 'HAIST Dev' && tm.title === B.t, 'Move Booking inputs: same room -> no new room');
  const rc8 = await readC(sub('2027-10-17', '14:00', '16:00', 'Studio 8'));
  ok((await j1(si, 'To Move', [], { 'Read Change': [{ json: rc8 }], 'Read Cache 7': cache })).new_rooms === 'Studio 8', 'a new room -> passed');
  let am = await j1(si, 'After Move', [{ json: { status: 'MOVED', event_id: 'ev9' } }], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache });
  ok(am.ok && am.view_id === 'V5' && am.nb.id === 'ev9' && am.card === '✅ *Changed.*\n\n*ORANGE / Jem Lim / HL*\n*Date:* Saturday, October 16, 2027\n*Time:* 3:00 PM – 5:00 PM\n*Room:* Studio 7'
     && am.view.close.text === 'Done' && am.ts === '7.7', 'moved -> Changed (the card), the new id kept for the message');
  am = await j1(si, 'After Move', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED', same_day_slots: [{ start: '2027-10-16T12:00:00+08:00', end: '2027-10-16T14:00:00+08:00' }, { start: '2027-10-16T17:00:00+08:00', end: '2027-10-16T19:00:00+08:00' }] } }],
    { 'Read Change': [{ json: rc }], 'Read Cache 7': cache });
  V = am.view;
  ok(!am.ok && V.blocks.find(b => b.block_id === 'problem').text.text === '⚠️ Studio 7 is taken then. Free that day: 12:00 PM – 2:00 PM, 5:00 PM – 7:00 PM.'
     && el('start').initial_option.value === '15:00' && el('end').initial_option.value === '17:00' && V.callback_id === 'change_booking', 'taken -> the form again at the new values, with the room\'s free times');
  am = await j1(si, 'After Move', [{ json: { status: 'REJECTED', reason: 'NOT_YOURS' } }], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache });
  ok(/only the person who booked it, or its engineer or arranger/.test(am.view.blocks.find(b => b.block_id === 'problem').text.text), 'not yours -> said');
  am = await j1(si, 'After Move', [{ json: { status: 'PARTIAL', event_id: 'ev9' } }], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache });
  ok(am.ok && /could not be removed/.test(am.card), 'partial -> Changed, and the old one to delete');

  // the message's row updates
  am = await j1(si, 'After Move', [{ json: { status: 'MOVED', event_id: 'ev9' } }], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache });
  const hist = blocks => ({ ok: true, messages: [{ ts: '7.7', text: 'x', blocks }] });
  let fx = await j1(si, 'Fix Message', [{ json: hist(msg.blocks) }], { 'After Move': [{ json: am }] });
  ok(fx.channel === 'D1' && fx.ts === '7.7' && fx.blocks.find(b => b.block_id === 'bk_ev9').text.text === '*ORANGE / Jem Lim / HL*\nSat, Oct 16 · 3:00 PM – 5:00 PM · Studio 7\n_Changed_'
     && JSON.parse(fx.blocks.find(b => b.block_id === 'bka_ev9').elements[0].value).id === 'ev9' && !fx.blocks.some(b => b.block_id === 'bk_ev1') && fx.blocks.some(b => b.block_id === 'bk_ev2'),
     'a list row -> the new time, Changed, buttons on the new booking');
  fx = await j1(si, 'Fix Message', [{ json: hist([{ type: 'section', block_id: 'bk_ev1', text: { type: 'mrkdwn', text: ':white_check_mark: *Booked.*\n\n…' } }, { type: 'actions', block_id: 'bka_ev1', elements: [] }]) }], { 'After Move': [{ json: am }] });
  ok(fx.blocks[0].text.text === am.card && fx.blocks[1].block_id === 'bka_ev9', 'the Booked DM -> the Changed card');
  ok((await run(si, 'Fix Message', [{ json: { ok: true, messages: [{ ts: '1.1', blocks: [] }] } }], { 'After Move': [{ json: am }] })).length === 0, 'message not found -> left alone');

  // ---- the team rule: Cancel Booking v27 / Move Booking v30
  const day = desc => ({ items: [{ id: 'ev1', summary: B.t, start: { dateTime: '2027-10-16T14:00:00+08:00' }, end: { dateTime: '2027-10-16T16:00:00+08:00' }, description: desc }] });
  const DESC = 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | team: U2 U4';
  const cancelAs = async (who, desc) => j1(cx, 'Check Ownership', [{ json: day(desc || DESC) }], { 'When Executed by Another Workflow': [{ json: { event_id: 'ev1', booking_date: '2027-10-16', title: B.t, confirmed: true, requester: who, authority: 'Standard', department: 'Music' } }], 'Find By Title': [{ json: { items: [] } }] });
  let r = await cancelAs('U2');
  ok(r.verdict === 'CLEAR' && r.notify === true && r.bookerRef === 'U1', 'Cancel v27: the engineer (team) may cancel; the booker is told');
  r = await cancelAs('U1');
  ok(r.verdict === 'CLEAR' && r.notify === false, 'Cancel v27: the booker cancels - nobody else told');
  r = await cancelAs('U9');
  ok(r.reason === 'NOT_YOURS', 'Cancel v27: someone not on it is refused');
  r = await cancelAs('U2', 'Booked by: Howard Luistro | ref: U1');
  ok(r.reason === 'NOT_YOURS', 'Cancel v27: no team on the event (chat bookings) -> as before');
  const moveAs = async (who) => j1(mv, 'Resolve Booking', [{ json: day(DESC) }], { 'When Executed by Another Workflow': [{ json: { event_id: 'ev1', booking_date: '2027-10-16', title: B.t, confirmed: true,
    requester: who, authority: 'Standard', department: 'Music', new_start_iso: '2027-10-16T15:00:00+08:00', new_end_iso: '2027-10-16T17:00:00+08:00' } }] });
  r = await moveAs('U4');
  ok(r.verdict === 'CLEAR' && r.notify === true, 'Move v30: the arranger (team) may change it; the booker is told');
  r = await moveAs('U9');
  ok(r.reason === 'NOT_YOURS', 'Move v30: someone not on it is refused');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
