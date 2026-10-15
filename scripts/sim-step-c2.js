#!/usr/bin/env node
// Step C2 offline (main v265 + Slack Interactions v12): typed cancel / change -> the booking(s) with Change / Cancel buttons
// (Change Offer + Change Reply); everything that is not a booking, a question or an answer -> the menu (Menu Check); the
// Change form starting at the time typed (Build Change).
// Usage: node scripts/sim-step-c2.js [main v265] [slack interactions v12]
const fs = require('fs');
const main = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/project-jessie-v265.json', 'utf8'));
const si = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/slack-interactions-v12.json', 'utf8'));
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
  const B = { id: 'ev1', d: '2027-10-16', s: '14:00', e: '16:00', r: 'Studio 7', t: 'ORANGE / Jem Lim / HL' };
  const bookedDM = { ts: '90.1', bot_id: 'B1', text: '✅ Booked.', blocks: [{ type: 'section', block_id: 'bk_ev1' },
    { type: 'actions', block_id: 'bka_ev1', elements: [{ action_id: 'bk_change', value: JSON.stringify(B) }, { action_id: 'bk_cancel', value: JSON.stringify(B) }] }] };
  const offerOf = async (text, o) => {
    o = o || {};
    return (await j1(main, 'Change Offer', [{ json: { keep: 1 } }], {
      'Slack Trigger': [{ json: { text, channel: 'D1', user: 'U1', ts: '100.1' } }],
      'Gate Context': [{ json: Object.assign({ datesInMessage: o.dates || '', todayIso: '2027-10-15', gate: o.gate || {} }, o.g || {}) }],
      'Booked For': [{ json: o.bf || {} }], 'Get Recent Messages': (o.history || []).map(m => ({ json: m })) })).changeOffer;
  };
  // ---- Change Offer
  let co = await offerOf('cancel ORANGE saturday', { dates: '2027-10-16' });
  ok(co.go && co.kind === 'cancel' && co.words.join() === 'orange' && co.fDates.join() === '2027-10-16' && co.timeMin === '2027-10-15T00:00:00+08:00'
     && co.timeMax === '2027-12-15T00:00:00+08:00', 'cancel: the title word, the date, from today for 60 days - ' + JSON.stringify(co.words));
  co = await offerOf('make it 3-5pm', { bf: { timeInNewest: true, timeStart: '15:00', timeEnd: '17:00' }, history: [{ ts: '100.1', text: 'make it 3-5pm' }, bookedDM] });
  ok(co.go && co.kind === 'change' && JSON.stringify(co.n) === '{"s":"15:00","e":"17:00"}' && co.recent.id === 'ev1' && !co.words.length, 'change: the new times; the booking in Jessie\'s newest message');
  co = await offerOf('move it to friday 3pm', { dates: '2027-10-22', history: [bookedDM] });
  ok(co.n.d === '2027-10-22' && co.n.s === '15:00' && !co.n.e && !co.fDates.length, 'change: a new date and a start alone');
  co = await offerOf('move my studio 7 booking to studio 8', {});
  ok(co.n.r === 'Studio 8' && co.fRooms.join() === 'Studio 7', 'change: two rooms -> the first finds it, the last is new');
  co = await offerOf('cancel my 2pm on saturday', { dates: '2027-10-16' });
  ok(co.time === '14:00' && !co.words.length, 'cancel: a time finds it');
  for (const [t, o, why] of [['is studio 7 free friday?', {}, 'an availability question'], ['yes', { g: { confirmedCancel: true } }, 'a yes to a chat card'],
    ['make it 4pm', { gate: { presentedMove: true } }, 'answering a chat card'], ['book studio 7 tomorrow', {}, 'not a cancel or change'], ['cancel every monday booking', {}, 'a series']])
    ok(!(await offerOf(t, o)).go && (await offerOf(t, o)).why === why, JSON.stringify(t) + ' -> ' + why);

  // ---- Change Reply
  const ev = (id, title, s, e, desc) => ({ id, summary: title, start: { dateTime: s }, end: { dateTime: e }, description: desc,
    attendees: [{ resource: true, email: 'x@resource.calendar.google.com', displayName: 'KDC Plaza-Top Level-Studio 7 (8)' }] });
  const cal = { items: [ev('ev1', 'ORANGE / Jem Lim / HL', '2027-10-16T14:00:00+08:00', '2027-10-16T16:00:00+08:00', 'ref: U1'),
    ev('ev2', 'KIWI / HL', '2027-10-16T17:00:00+08:00', '2027-10-16T18:00:00+08:00', 'ref: U2 | team: U1'),
    ev('ev3', 'ORANGE / Jem Lim / HL', '2027-10-20T10:00:00+08:00', '2027-10-20T12:00:00+08:00', 'ref: U1'),
    ev('ev4', 'THEIRS / X / DR', '2027-10-16T09:00:00+08:00', '2027-10-16T10:00:00+08:00', 'ref: U9')] };
  const reply = async (co, res) => j1(main, 'Change Reply', [{ json: res || cal }], { 'Change Offer': [{ json: { changeOffer: co } }] });
  let r = await reply(await offerOf('cancel ORANGE saturday', { dates: '2027-10-16' }));
  ok(r.count === 1 && r.blocks[0].text.text === 'Here it is - press *Cancel* to cancel it.' && r.blocks[1].block_id === 'bk_ev1'
     && r.blocks[1].text.text === '*ORANGE / Jem Lim / HL*\nSat, Oct 16 · 2:00 PM – 4:00 PM · Studio 7', 'cancel ORANGE saturday -> that one booking');
  const bt = r.blocks[2].elements;
  ok(bt.map(x => x.action_id).join() === 'bk_change,bk_cancel' && bt[1].confirm && bt[1].confirm.confirm.text === 'Cancel booking' && r.channel === 'D1',
     'its Change / Cancel (Cancel asks first) - the blocks Slack Interactions handles');
  r = await reply(await offerOf('cancel orange', {}));
  ok(r.count === 2 && r.blocks[0].text.text === 'Which one?' && r.blocks.filter(b => /^bk_/.test(b.block_id || '')).map(b => b.block_id).join() === 'bk_ev1,bk_ev3', 'two ORANGE -> which one, in date order');
  r = await reply(await offerOf('cancel kiwi', {}));
  ok(r.count === 1 && r.blocks[1].block_id === 'bk_ev2', 'a booking they engineer (team) counts');
  r = await reply(await offerOf('cancel theirs', {}));
  ok(r.count === 0 && r.blocks[0].text.text === 'I couldn’t find a booking of yours called "theirs" from today on.' && r.blocks[1].elements[0].action_id === 'my_bookings',
     'someone else\'s -> not found, with My bookings');
  r = await reply(await offerOf('cancel my 2pm on saturday', { dates: '2027-10-16' }));
  ok(r.count === 1 && r.blocks[1].block_id === 'bk_ev1', 'by date and time');
  co = await offerOf('make it 3-5pm', { bf: { timeInNewest: true, timeStart: '15:00', timeEnd: '17:00' }, history: [bookedDM] });
  r = await reply(co);
  ok(r.count === 1 && r.blocks[0].text.text === 'Here it is - press *Change* to check the new time.'
     && r.blocks[1].text.text === '*ORANGE / Jem Lim / HL*\nNow: Sat, Oct 16 · 2:00 PM – 4:00 PM · Studio 7\nNew: Sat, Oct 16 · 3:00 PM – 5:00 PM · Studio 7', 'make it 3-5pm after Booked -> Now / New');
  const cv = JSON.parse(r.blocks[2].elements[0].value), xv = JSON.parse(r.blocks[2].elements[1].value);
  ok(cv.id === 'ev1' && JSON.stringify(cv.n) === '{"s":"15:00","e":"17:00"}' && !xv.n, 'Change carries the new times; Cancel does not');
  r = await reply(await offerOf('move it to friday 3pm', { dates: '2027-10-22', history: [bookedDM] }));
  ok(/New: Fri, Oct 22 · 3:00 PM – 5:00 PM · Studio 7/.test(r.blocks[1].text.text), 'a start alone keeps the length (2 hours)');
  r = await reply(await offerOf('change my booking', {}));
  ok(r.count === 3 && r.blocks[0].text.text === 'Which one?', 'nothing to go on, no recent booking -> all of theirs, which one');
  r = await reply(await offerOf('make it 3-5pm', { bf: { timeInNewest: true, timeStart: '15:00', timeEnd: '17:00' }, history: [bookedDM] }), { error: 'x' });
  ok(r.count === 1 && r.blocks[1].block_id === 'bk_ev1', 'calendar unreadable but the recent booking known -> still offered (Move checks)');
  r = await reply(await offerOf('cancel orange', {}), { error: 'x' });
  ok(/couldn’t be read/.test(r.blocks[0].text.text), 'calendar unreadable, nothing known -> said');

  // ---- Menu Check: everything else -> the menu
  const menuFor = async (text, o) => {
    o = o || {};
    return j1(main, 'Menu Check', [], { 'Slack Trigger': [{ json: { text, channel: 'D1', ts: '100.1' } }], 'Get Booker': [{ json: { fields: { Name: 'Howard Luistro' } } }],
      'Gate Context': [{ json: Object.assign({ datesInMessage: o.dates || '', gate: o.gate || {} }, o.g || {}) }], 'Get Recent Messages': (o.history || []).map(m => ({ json: m })) });
  };
  for (const t of ["what's up", 'whats up', 'how are you?', 'Sup Jessie'])
    ok((await menuFor(t)).menu === true, 'menu for ' + JSON.stringify(t));
  let mc = await menuFor('thanks!');
  ok(mc.menu && mc.blocks[0].text.text === 'Anytime! Anything else?', 'thanks -> "Anytime! Anything else?" + the menu');
  mc = await menuFor('test');
  ok(mc.menu && mc.why === 'not a booking or a question' && /I can help with bookings/.test(mc.blocks[0].text.text), 'a short message about nothing -> the menu');
  for (const [t, o] of [['what studios do we have?', {}], ['who is engineering orange', {}], ['book studio 7 tomorrow', {}], ['cancel orange', {}],
    ['make it 3pm', {}], ['jem lim', { history: [{ ts: '9', bot_id: 'B', text: 'Who’s the client?' }] }], ['client is jem lim', { history: [{ ts: '9', bot_id: 'B', text: 'Here’s what I have so far', blocks: [{ elements: [{ action_id: 'open_book', value: '{"d":"x"}' }] }] }] }],
    ['yes', { gate: { presentedCancel: true } }], ['tomorrow', {}], ['friday', { dates: '2027-10-22' }], ['reset', {}], ['ok', { g: { confirmed: true } }]])
    ok((await menuFor(t, o)).menu === false, 'no menu for ' + JSON.stringify(t) + (o.history ? ' (Jessie is waiting)' : ''));
  ok(/\$json\.blocks\[0\]\.text\.text/.test(main.nodes.find(n => n.name === 'Send Menu').parameters.jsonBody), 'Send Menu: the notification text is the menu\'s line');

  // ---- wiring + Turn Log
  const C = main.connections, nx = n => (C[n].main || []).map(o => o.map(c => c.node).join('+')).join(' | ');
  ok(nx('Form Offer?') === 'Send Form Offer | Change Offer' && nx('Change Offer?') === 'List Mine | Early Room Plan' && nx('List Mine') === 'Change Reply'
     && nx('Change Reply') === 'Send Change Reply' && nx('Send Change Reply') === 'Turn Log Row+Clear Ack', 'wiring: Form Offer? -> Change Offer -> Change Offer? (List Mine -> Change Reply -> Send; else Early Room Plan)');
  const tl = await j1(main, 'Turn Log Row', [{ json: {} }], { 'Slack Trigger': [{ json: { text: 'x', ts: '1' } }], 'Send Change Reply': [{ json: { ok: true } }] });
  ok(tl.Path === 'change offer', 'Turn Log: change offer');

  // ---- Slack Interactions v12: the Change form at the typed time
  const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: [
    { id: 'r7', fields: { 'Room Name': 'Studio 7' } }, { id: 'r8', fields: { 'Room Name': 'Studio 8' } }, { id: 'm4', fields: { 'Room Name': 'M4' } }], sessionTypes: [], bookers: [] }) } }];
  const build = async (val) => (await j1(si, 'Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T1' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { type: 'block_actions', actions: [{ action_id: 'bk_change', value: JSON.stringify(val) }], container: { channel_id: 'D1', message_ts: '5' } } } }] })).view;
  let V = await build(Object.assign({}, B, { n: { s: '15:00', e: '17:00' } }));
  const el = id => V.blocks.find(b => b.block_id === id).element;
  ok(el('start').initial_option.value === '15:00' && el('end').initial_option.value === '17:00' && el('date').initial_date === '2027-10-16' && el('room').initial_option.value === 'Studio 7',
     'the form starts at the typed times');
  ok(/Now: Sat, Oct 16 · 2:00 PM – 4:00 PM · Studio 7/.test(V.blocks[0].text.text) && !JSON.parse(V.private_metadata).b.n && JSON.parse(V.private_metadata).b.s === '14:00', '"Now:" and "Nothing changed" still use the booking as it is');
  V = await build(Object.assign({}, B, { n: { d: '2027-10-22', s: '09:30' } }));
  ok(el('date').initial_date === '2027-10-22' && el('start').initial_option.value === '09:30' && el('end').initial_option.value === '11:30', 'a new date and a start alone: the same length');
  V = await build(Object.assign({}, B, { n: { r: 'Studio 8' } }));
  ok(el('room').initial_option.value === 'Studio 8' && el('start').initial_option.value === '14:00', 'a new room typed -> chosen');
  V = await build(Object.assign({}, B, { n: { r: 'M4' } }));
  ok(el('room').initial_option.value === 'M4' && el('room').options[0].value === 'Studio 7', 'a typed room of another kind is offered too');
  V = await build(B);
  ok(el('start').initial_option.value === '14:00', 'no typed values: as v11');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
