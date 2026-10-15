#!/usr/bin/env node
// Round 2 of the Slack-test notes, offline (Slack Interactions v19 + main v270): the "you may close this window" lines and
// the change DM (1), My bookings' quotes (2), the proposed card while changing (3), client capitals (4), a free room off the
// lists and "Use another room" (5), the series view closing the form (6), the source message's ⏳ line (7), room names
// and same-kind rooms (8), Change / Cancel on the engineer notice (9).
// Usage: node scripts/sim-round-2.js [slack interactions v19] [main v270]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v19.json', 'utf8'));
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/project-jessie-v270.json', 'utf8'));
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
async function run(wf, name, input, outs) {
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const C = si.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');

(async () => {
  const R = (id, name, extra) => ({ id, fields: Object.assign({ 'Room Name': name }, extra || {}) });
  const rooms = [R('r2', 'Studio 2'), R('r7', 'Studio 7'), R('rf', 'Studio F'), R('ra', 'Studio A', { 'Vocal Booth': true }), R('rl', 'Likha', { 'Room Type': ['Conference Room'] }),
    R('rs', 'Salin', { 'Room Type': ['Conference Room'] }), R('rk', 'Katha', { 'Room Type': ['Conference Room'] }), R('m1', 'M1'), R('m4', 'M4')];
  const sessionTypes = [{ id: 'st1', fields: { Type: 'Music Mixing', Priority: ['rf'], 'Last Resort': ['r7'] } }, { id: 'st2', fields: { Type: 'Meeting', Priority: ['rl', 'rs'] } }];
  const bookers = [{ fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer' } }, { fields: { Name: 'Alec Elijah Gan', Initials: 'AEG', 'Slack User ID': 'U3', Info: 'Music Engineer' } }];
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
  const chk = [{ json: { user: 'U1', triggerId: 'T1', channel: 'D1' } }];

  // ---- 7: step 1 remembers the message it came from; step 1 read carries it
  const s1 = (await j1(si, 'Build Step 1', [], { 'Check Signature': chk, 'Read Cache': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: 'menu' }], container: { channel_id: 'D1', message_ts: '50.5' } } } }] })).view;
  ok(JSON.parse(s1.private_metadata).msg.ts === '50.5', '7: step 1 remembers the message it came from');
  const vals1 = { date: { date_pick: { selected_date: '2027-10-16' } }, start: { start_pick: { selected_option: { value: '10:00' } } }, end: { end_pick: { selected_option: { value: '14:00' } } }, purpose: { purpose_pick: { selected_option: { value: 'Music Mixing' } } } };
  const r1 = await j1(si, 'Read Step 1', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1', msg: { ch: 'D1', ts: '50.5' }, pre: { r: 'Studio 2' } }), state: { values: vals1 } } } } }] });
  ok(r1.s.msg.ts === '50.5', '7: carried into step 2');

  // ---- 5: Studio 2 (on neither Music Mixing list) free -> offered as not a usual room; "Use another room"
  const step2 = async (ra, s) => (await j1(si, 'Build Step 2', [].concat(ra).map(x => ({ json: x })), { 'Read Step 1': [{ json: { s: s || r1.s } }], 'Read Cache 2': cache })).view;
  let v = await step2({ status: 'OK', free_priority: ['Studio F'], free_last_resort: [], busy: ['Studio 7 (BREAD STICKS / Jem Lim / HL)'] });
  const room = v.blocks.find(b => b.block_id === 'room').element;
  ok(room.initial_option.value === 'Studio 2' && room.initial_option.description.text === 'not a usual room for Music Mixing' && !v.blocks.some(b => b.text && /taken/.test(b.text.text || '')),
     '5: Studio 2 free, on neither list -> offered and chosen as "not a usual room" (live: "taken")');
  ok(JSON.parse(v.private_metadata).nu.indexOf('Studio 2') !== -1, '5: remembered as not usual (booked as asked)');
  const others = JSON.parse(v.private_metadata).others;
  ok(!others && !v.blocks.some(b => b.block_id === 'room_toggle'), '5: no other free studio (Studio 7 busy, Studio A a booth, Studio 2 already listed) -> no "Use another room" box - ' + JSON.stringify(others));
  v = await step2({ status: 'OK', free_priority: ['Studio F'], free_last_resort: [], busy: ['Studio 2 (X)'] });
  ok(v.blocks.some(b => b.text && b.text.text === '⚠️ Studio 2 is taken then. These are free:'), '5: Studio 2 busy -> "taken"');
  const sNoPre = Object.assign({}, r1.s, { pre: undefined });
  v = await step2({ status: 'OK', free_priority: ['Studio F'], free_last_resort: [], busy: [] }, sNoPre);
  const oth = JSON.parse(v.private_metadata).others;
  ok(oth.join() === 'Studio 2,Studio 7' && v.blocks.some(b => b.block_id === 'room_toggle'), '5: "Use another room" lists the other free studios (not booths, not conference rooms) - ' + oth.join());
  // the box opens the list; Read Step 2 takes it, booked as asked
  const tog = await j1(si, 'Note Toggle', [], { 'Read Cache 9': cache, 'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'room_toggle', selected_options: [{ value: 'room' }] }],
    view: { id: 'V2', callback_id: 'book_step2', title: v.title, close: v.close, submit: v.submit, private_metadata: v.private_metadata, blocks: v.blocks, state: { values: {} } } } } }] });
  const ro = tog.view.blocks.find(b => b.block_id === 'room_other');
  ok(ro && ro.element.options.map(o => o.value).join() === 'Studio 2,Studio 7' && ro.element.options[0].description.text === 'not a usual room for Music Mixing'
     && tog.view.blocks.findIndex(b => b.block_id === 'room_other') === tog.view.blocks.findIndex(b => b.block_id === 'room_toggle') + 1, '5: ticked -> "Another room" with the free ones, each "not a usual room"');
  const sub2 = { type: 'view_submission', view: { id: 'V2', private_metadata: v.private_metadata, blocks: v.blocks, state: { values: {
    room: { room_radio: { selected_option: { value: 'Studio F' } } }, room_other: { room_other_pick: { selected_option: { value: 'Studio 7' } } }, project: { project_in: { value: 'mix1' } },
    client: { client_in: { value: 'john mcdonald' } }, engineer: { engineer_pick: { selected_option: { value: 'U3' } } } } } } };
  const rs2 = await j1(si, 'Read Step 2', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: sub2 } }], 'Read Cache 3': cache });
  ok(rs2.valid && rs2.room === 'Studio 7' && rs2.prep.room_override === true && rs2.prep.rooms === 'Studio 7', '5: another room wins over the radio, booked as asked');
  // ---- 4: client capitals
  ok(rs2.prep.client === 'John Mcdonald' && rs2.calTitle === 'MIX1 / John Mcdonald / AEG', '4: "john mcdonald" -> "John Mcdonald" in the booking and its title');
  const cap = async (c) => (await j1(si, 'Read Step 2', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: Object.assign({}, sub2, { view: Object.assign({}, sub2.view, { state: { values: Object.assign({}, sub2.view.state.values, { client: { client_in: { value: c } } }) } }) }) } }], 'Read Cache 3': cache })).prep.client;
  ok(await cap('ACME') === 'ACME' && await cap('mcDonald') === 'McDonald' && await cap("o'brien") === "O'Brien" && await cap('sasa abella') === 'Sasa Abella', '4: ACME stays; mcDonald -> McDonald; o\'brien -> O\'Brien');
  // ---- 1: Booking… says you may close it
  ok(/Your booking is being processed\. This takes a few seconds\. You may close this window\. You’ll be notified when it’s done\./.test(JSON.stringify(rs2.answer.view)) && rs2.answer.view.clear_on_close, '1: Booking… - "You may close this window…"');

  // ---- 7: the source message while booking, and after
  const offerMsg = { ts: '50.5', text: 'Here’s what I have so far', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Here’s what I have so far:' } },
    { type: 'actions', elements: [{ action_id: 'open_book', value: '{"r":"Studio 2"}' }, { action_id: 'my_bookings', value: 'menu' }] }, { type: 'context', elements: [{ type: 'mrkdwn', text: 'Opens the form…' }] }] };
  const menuMsg = { ts: '50.5', text: 'What would you like to do?', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Hi!' } }, { type: 'actions', elements: [{ action_id: 'open_book', value: 'menu' }, { action_id: 'my_bookings', value: 'menu' }] }] };
  const mark = async (m) => j1(si, 'Mark Source', [{ json: { ok: true, messages: [m] } }], { 'Read Step 2': [{ json: rs2 }] });
  let M = await mark(offerMsg);
  ok(M.ok && M.offer && M.blocks.length === 2 && M.blocks[1].elements[0].text === '⏳ Your booking is being processed…' && !M.blocks.some(b => b.type === 'actions'), '7: a booking reply -> buttons hidden, "⏳ Your booking is being processed…"');
  let D = await run(si, 'Source Done', [], { 'Mark Source': [{ json: M }], 'After Book': [{ json: { ok: true } }] });
  ok(D[0].json.blocks[1].elements[0].text === '✅ Booked.' && !D[0].json.blocks.some(b => b.type === 'actions'), '7: booked -> "✅ Booked." and the buttons stay hidden');
  D = await run(si, 'Source Done', [], { 'Mark Source': [{ json: M }] });
  ok(D[0].json.blocks === M.original, '7: a question on the form (no After Book) -> the reply back as it was');
  M = await mark(menuMsg);
  D = await run(si, 'Source Done', [], { 'Mark Source': [{ json: M }], 'After Book': [{ json: { ok: true } }] });
  ok(!M.offer && D[0].json.blocks === M.original, '7: the menu -> its buttons back after booking');
  ok((await run(si, 'Source Done', [], { 'Mark Source': [{ json: { ok: false } }] })).length === 0, '7: no source message -> nothing');
  const sq = nx('Series?'), sh = nx('Show Result'), sqq = nx('Show Question');
  ok(sq === 'To Prepare Series | Get Source' && nx('Get Source') === 'Mark Source' && nx('Source Shown?') === 'Show Source | Prepare' && nx('Show Source') === 'Prepare'
     && /Source Done/.test(sh) && /Source Done/.test(sqq) && nx('Source Done') === 'Update Source', '7 wiring: single booking');
  const MS = await j1(si, 'Mark Source Series', [{ json: { ok: true, messages: [offerMsg] } }], { 'Read Series Confirm': [{ json: { meta: { msg: { ch: 'D1', ts: '50.5' } } } }] });
  ok(MS.ok && MS.blocks[1].elements[0].text === '⏳ Your series is being processed…', '7: a series -> "⏳ Your series is being processed…"');
  const DS = await run(si, 'Source Done Series', [], { 'Mark Source Series': [{ json: MS }], 'After Book Series': [{ json: { text: '✅ *Booked 4 dates.*' } }] });
  ok(DS[0].json.blocks[1].elements[0].text === '✅ Booked.', '7: the series booked -> "✅ Booked."');
  ok(nx('Answer Series') === 'Get Source Series' && nx('Series Source Shown?') === 'Show Source Series | Read Saved Series' && /Source Done Series/.test(nx('Show Series Result')), '7 wiring: series');
  // the series carries the message on to the check screen
  const aps = await j1(si, 'After Prepare Series', [{ json: { status: 'PREPARED', card_text: '*X*\n\nConfirm to book.', title: 'X', dates: ['2027-10-19', '2027-10-26'], prep_key: 'k', prep_stored: true } }],
    { 'Read Step 2': [{ json: Object.assign({}, rs2, { s: Object.assign({}, rs2.s, { series: { dates: ['2027-10-19', '2027-10-26'] } }) }) }], 'Read Request': [{ json: { payload: sub2 } }] });
  ok(JSON.parse(aps.view.private_metadata).msg.ts === '50.5', '7: the series check screen keeps the message');

  // ---- 6 + 1: the series booking view
  const rsc = await j1(si, 'Read Series Confirm', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V3', private_metadata: JSON.stringify({ key: 'k', n: 2, title: 'X' }) } } } }] });
  ok(rsc.answer.view.clear_on_close === true && /This may take a while\. You may close this window\. You’ll be notified when it’s done\./.test(JSON.stringify(rsc.answer.view)), '6 + 1: closing the series booking view closes the form; the close line');

  // ---- 8: room names; the Change form lists rooms of the same kind
  const B = { id: 'evL', d: '2027-10-21', s: '10:00', e: '11:00', r: 'Likha (Big Room)', t: 'LIKHA - haist meeting' };
  const bc = await j1(si, 'Build Change', [], { 'Check Signature': chk, 'Read Cache 6': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify(B) }], container: { channel_id: 'D1', message_ts: '7.7' } } } }] });
  const rp = bc.view.blocks.find(b => b.block_id === 'room').element;
  ok(rp.options.map(o => o.value).join() === 'Likha,Katha,Salin' && rp.initial_option.value === 'Likha', '8: a meeting in "Likha (Big Room)" -> conference rooms only, Likha chosen (live: studios) - ' + rp.options.map(o => o.value).join());
  const bcM = await j1(si, 'Build Change', [], { 'Check Signature': chk, 'Read Cache 6': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify({ id: 'evM', d: '2027-10-21', s: '10:00', e: '11:00', r: 'M4', t: 'M4 - Howard' }) }], container: { channel_id: 'D1', message_ts: '7.7' } } } }] });
  ok(bcM.view.blocks.find(b => b.block_id === 'room').element.options.map(o => o.value).join() === 'M4,M1', '8: an M booth -> M booths only');
  const bcU = await j1(si, 'Build Change', [], { 'Check Signature': chk, 'Read Cache 6': cache, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify(Object.assign({}, B, { r: 'Somewhere Else' })) }], container: { channel_id: 'D1', message_ts: '7.7' } } } }] });
  ok(bcU.view.blocks.find(b => b.block_id === 'room').element.options.map(o => o.value).join() === 'Somewhere Else', '8: a room not on the list -> no others offered (never a wrong kind)');
  const subC = (r) => ({ type: 'view_submission', view: { id: 'V5', private_metadata: bc.view.private_metadata, state: { values: {
    date: { date_pick: { selected_date: '2027-10-21' } }, start: { start_pick: { selected_option: { value: '10:00' } } }, end: { end_pick: { selected_option: { value: '11:00' } } }, room: { room_pick: { selected_option: { value: r } } } } } } });
  let rc = await j1(si, 'Read Change', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: subC('Likha') } }], 'Read Cache 10': cache });
  ok(!rc.valid && /Nothing changed/.test(rc.answer.errors.date), '8: "Likha (Big Room)" kept as Likha -> nothing changed (not a pointless move)');
  rc = await j1(si, 'Read Change', [], { 'Check Signature': chk, 'Read Request': [{ json: { payload: subC('Salin') } }], 'Read Cache 10': cache });
  ok(rc.valid && rc.roomChanged && rc.newTitle === 'SALIN - haist meeting', '8: moved to Salin -> a room change, the title follows');
  // ---- 3 + 1: the Changing… screen shows the proposed booking
  ok(rc.answer.view.blocks[0].text.text === '⏳ *Changing…*\n\n*SALIN - haist meeting*\n*Date:* Thursday, October 21, 2027\n*Time:* 10:00 AM – 11:00 AM\n*Room:* Salin'
     && rc.answer.view.blocks[1].elements[0].text === 'This takes a few seconds. You may close this window. You’ll be notified when it’s done.', '3 + 1: Changing… shows the proposed card and the close line');
  const tm = await j1(si, 'To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache, 'Client Names': [] });
  ok(tm.new_rooms === 'Salin' && tm.new_summary === 'SALIN - haist meeting', '8: To Move passes the new room and title');
  // ---- 1: a finished change DMs the card
  const am = await j1(si, 'After Move', [{ json: { status: 'MOVED', event_id: 'evN' } }], { 'Read Change': [{ json: rc }], 'Read Cache 7': cache, 'To Move': [{ json: tm }] });
  ok(am.dmChannel === 'U1' && am.dmBlocks[0].block_id === 'bk_evN' && am.dmBlocks[0].text.text === am.card && am.dmBlocks[1].block_id === 'bka_evN' && /^✅ \*Changed\.\*/.test(am.card),
     '1: a finished change also DMs the Changed card with its buttons');
  ok(/DM Changed/.test(nx('Moved?').split(' | ')[0]), '1 wiring: DM Changed on a change that went through');

  // ---- 2: My bookings' example in quotes
  const L = await j1(si, 'Render My Bookings', [{ json: { items: [] } }], { 'My Window': [{ json: { user: 'U1', start: '2027-10-15', end: '2027-10-22', channel: 'D1', ts: '', page: false } }], 'Read Cache 4': cache });
  ok(L.blocks[L.blocks.length - 1].elements[0].text === 'Further ahead? Type it, like _"what do I have in November?"_', '2: the example in quotes');

  // ---- 9: the notice has the booking's Change / Cancel
  const bkv = JSON.stringify({ id: 'evB', d: '2027-10-16', s: '20:00', e: '22:00', r: 'Studio 7', t: 'MAKINA / Sasa Abella / AEG' });
  const bn = await run(si, 'Booked Notices', [], { 'Read Step 2': [{ json: { s: { requester: 'U1' }, engineerId: 'U3', arrangerId: '' } }], 'Read Cache 3': cache,
    'After Book': [{ json: { text: '✅ *Booked.*\n\n*MAKINA / Sasa Abella / AEG*\n*Date:* x', blocks: [{ type: 'section', block_id: 'bk_evB' }, { type: 'actions', block_id: 'bka_evB', elements: [{ action_id: 'bk_change', value: bkv }, { action_id: 'bk_cancel', value: bkv }] }] } }] });
  const nb = bn[0].json.blocks;
  ok(nb.length === 4 && /👋 \*Howard Luistro booked you as the engineer\.\*$/.test(nb[0].text.text) && nb[1].block_id === 'bk_evB' && /^\*MAKINA/.test(nb[1].text.text)
     && nb[2].block_id === 'bka_evB' && nb[2].elements.map(e => e.action_id).join() === 'bk_change,bk_cancel' && nb[3].elements.map(e => e.action_id).join() === 'my_bookings,open_book',
     '9: the notice - the line, the booking, its Change / Cancel, My bookings / Book a room');
  const rcN = { user: 'U1', newDetails: { team: 'U3' }, oldTeam: ['U1'], d: { en: 'U3' } };
  const cn = await run(si, 'Change Notices', [], { 'Read Change': [{ json: rcN }], 'Read Cache 7': cache,
    'After Move': [{ json: { ok: true, card: '✅ *Changed.*\n\n*MAKINA / Sasa Abella / AEG*', nb: { id: 'evN', d: '2027-10-16', s: '20:00', e: '22:00', r: 'Studio 7', t: 'MAKINA / Sasa Abella / AEG' } } }] });
  ok(cn[0].json.blocks.some(b => b.block_id === 'bka_evN'), '9: the "added you" notice too');
  const sn = await run(si, 'Series Notices', [], { 'Read Series Confirm': [{ json: { user: 'U1' } }], 'To Book Series': [{ json: { go: true, description: 'Engineer: Alec Elijah Gan | ref: U1 | team: U3' } }],
    'After Book Series': [{ json: { text: '✅ *Booked 3 dates.*\n\n*SER*' } }], 'Read Cache 8': cache });
  ok(sn[0].json.blocks.length === 2 && !sn[0].json.blocks.some(b => /^bka_/.test(b.block_id || '')), '9: a series notice keeps My bookings / Book a room only');

  // ---- main v270
  const fo = await j1(main, 'Form Offer', [{ json: {} }], { 'All Rooms': [], 'All Session Types': [], 'All Bookers': [], 'Slack Trigger': [{ json: { text: 'book studio 7 tomorrow, client john smithy', channel: 'D1', ts: '1' } }],
    'Gate Context': [{ json: { datesInMessage: '2027-10-16', todayIso: '2027-10-15', gate: {} } }], 'Booked For': [{ json: { client: 'john smithy', clientPhrase: 'client john smithy' } }], 'Get Recent Messages': [] });
  ok(fo.formOffer.prefill.c === 'John Smithy' && /Client: John Smithy/.test(fo.formOffer.text), 'main v270: the reply\'s client capitalised');
  const cr = await j1(main, 'Change Reply', [{ json: { items: [{ id: 'evL', summary: 'LIKHA - haist meeting', start: { dateTime: '2027-10-21T10:00:00+08:00' }, end: { dateTime: '2027-10-21T11:00:00+08:00' }, description: 'ref: U1',
    attendees: [{ resource: true, email: 'x@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Likha (Big Room)' }] }] } }],
    { 'Change Offer': [{ json: { changeOffer: { kind: 'cancel', user: 'U1', channel: 'D1', words: ['haist'], fDates: [], fRooms: [], n: {} } } }] });
  ok(/· Likha$/.test(cr.blocks[1].text.text) && JSON.parse(cr.blocks[2].elements[0].value).r === 'Likha', 'main v270: the typed reply names Likha (not "Likha (Big Room)")');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
