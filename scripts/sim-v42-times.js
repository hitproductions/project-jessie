#!/usr/bin/env node
// Slack Interactions v42 + main v281 (22 Oct): the time lists open at 6:00 AM; the End list ends the day at 11:59 PM (in place
// of 12:00 AM - 12:00 AM to 11:59 PM is the whole day, and a 12:00 AM end from an old form is read as 11:59 PM); an Event can
// be all day (any of its rooms - Howard: "all day for all events, not just the lobby"); typed "all day / whole day / full day" fills the form (an M booth or the Lobby: All day ticked;
// anything else 12:00 AM to 11:59 PM).
// Usage: node scripts/sim-v42-times.js [slack-interactions v42] [main v281]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v42.json', 'utf8'));
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/project-jessie-v281.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
if (JSON.stringify(si.nodes).indexOf('(6 * 60 + i * 30)') === -1) { console.log('0 ok, 0 failed (an older build: v42 not in it)'); process.exit(0); }
async function runIn(wf, name, input, outs) {
  const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (wf, ...a) => (await runIn(wf, ...a))[0].json;
const rooms = FX.rooms.concat([{ id: 'lo', fields: { 'Room Name': 'Lobby', 'Room Type': ['Lobby'] } }]);
const ST = (t, pri) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': ['None'], 'Room Requirements': '' } });
const sessionTypes = FX.sessionTypes.concat([ST('Event', ['lo', 'lk']), ST('Meeting', [])]);
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers: [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer', Department: ['Audio Post'] } }] }) } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const step1 = async pre => (await j1(si, 'Build Step 1', [], { 'Check Signature': [chk], 'Read Cache': cacheRow,
  'Read Request': [{ json: { payload: { actions: [{ action_id: 'open_book', value: pre ? JSON.stringify(pre) : 'menu' }] } } }] })).view;
const blk = (v, id) => v.blocks.find(b => b.block_id === id);
const tv = v => ({ selected_option: { value: v } });
const read1 = async (vals) => j1(si, 'Read Step 1', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: vals } } } } }] });
const V1 = (p, s, e, ad) => Object.assign({ date: { date_pick: { selected_date: '2027-10-23' } }, purpose: { purpose_pick: tv(p) } },
  s ? { start: { start_pick: tv(s) } } : {}, e ? { end: { end_pick: tv(e) } } : {}, ad ? { allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } } } : {});

(async () => {
  console.log('1. The lists open at 6:00 AM');
  let v = await step1();
  const so = blk(v, 'start').element.options, eo = blk(v, 'end').element.options;
  ok(so.length === 48 && so[0].text.text === '6:00 AM' && so[47].text.text === '5:30 AM' && so[36].value === '00:00' && so[36].text.text === '12:00 AM', 'Start: 6:00 AM first, round to 5:30 AM; 12:00 AM after 11:30 PM');
  ok(eo.length === 48 && eo[0].text.text === '6:00 AM' && eo[35].text.text === '11:30 PM' && eo[36].value === '23:59' && eo[36].text.text === '11:59 PM' && !eo.some(x => x.value === '00:00')
     && new Set(eo.map(x => x.value)).size === 48, 'End: 11:59 PM right after 11:30 PM, in place of 12:00 AM');
  console.log('2. 11:59 PM - the end of the day');
  v = await step1({ d: '2027-10-23', s: '00:00', e: '23:59', r: 'Studio 7', p: 'VO Recording' });
  ok(blk(v, 'start').element.initial_option.text.text === '12:00 AM' && blk(v, 'end').element.initial_option.value === '23:59' && blk(v, 'end').element.initial_option.text.text === '11:59 PM'
     && blk(v, 'end').element.options.some(o => o.value === '23:59' && o.text.text === '11:59 PM') && !blk(v, 'start').element.options.some(o => o.value === '23:59'),
     'a whole day filled in: Start 12:00 AM, End 11:59 PM (one of the End options; not added to Start)');
  let r = await read1(V1('VO Recording', '00:00', '23:59'));
  ok(r.valid && r.s.t0 === '00:00' && r.s.t1 === '23:59' && !r.s.allDay, '12:00 AM to 11:59 PM -> books the whole day (00:00-23:59, not all day)');
  r = await read1(V1('VO Recording', '00:00', '00:00'));
  ok(r.valid && r.s.t1 === '23:59', '12:00 AM to 12:00 AM (a form open from before) -> the end read as 11:59 PM, not refused', r.answer);
  r = await read1(V1('VO Recording', '18:00', '00:00'));
  ok(r.valid && r.s.t0 === '18:00' && r.s.t1 === '23:59', '6:00 PM to 12:00 AM -> to 11:59 PM (was "The end has to be after the start")');
  r = await read1(V1('VO Recording', '14:00', '10:00'));
  ok(!r.valid && /after the start/.test(r.answer.errors.end || ''), 'an end before the start is still refused');
  console.log('3. All day for an Event (any of its rooms)');
  r = await read1(V1('Event', '', '', true));
  ok(r.valid && r.s.allDay && r.s.t0 === '00:00' && r.s.t1 === '23:59' && r.s.kind === 'meeting', 'Event + All day -> all day', r.answer);
  r = await read1(V1('Meeting', '10:00', '11:00', true));
  ok(r.valid && !r.s.allDay && r.s.t0 === '10:00', 'a Meeting is never all day (no box for it)');
  v = await step1({ d: '2027-10-23', p: 'Event', ad: 1 });
  const ab = blk(v, 'allday_toggle');
  ok(ab && ab.elements[0].options[0].text.text === 'All day booking' && ab.elements[0].initial_options && !blk(v, 'start') && !blk(v, 'end'), 'typed Event all day: the box ticked, no Start / End', v.blocks.map(b => b.block_id));
  v = await step1({ d: '2027-10-23', p: 'Event' });
  ok(blk(v, 'allday_toggle') && !blk(v, 'allday_toggle').elements[0].initial_options && blk(v, 'start') && blk(v, 'end'), 'an Event: the box, unticked, with Start / End');
  v = await step1({ d: '2027-10-23', p: '__booth', ad: 1 });
  ok(blk(v, 'allday_toggle').elements[0].options[0].text.text === 'All day booking' && blk(v, 'allday_toggle').elements[0].initial_options && !blk(v, 'start'), 'an M booth typed all day: All day booking ticked');
  v = await step1({ d: '2027-10-23', p: 'Meeting' });
  ok(!blk(v, 'allday_toggle'), 'a Meeting: no All day box');
  // Note Toggle: picking Event in step 1 adds the box
  const s1 = await step1();
  const tog = async (val) => j1(si, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, s1, { state: { values: {} } }),
    actions: [{ action_id: 'purpose_pick', selected_option: { value: val } }] } } }], 'Read Cache 9': cacheRow });
  let t = await tog('Event'); let tv2 = t.view || (t.json && t.json.view) || t;
  ok(blk(tv2, 'allday_toggle') && blk(tv2, 'allday_toggle').elements[0].options[0].text.text === 'All day booking' && blk(tv2, 'start') && blk(tv2, 'end'), 'Event picked: "All day booking" appears, Start / End stay', tv2.blocks && tv2.blocks.map(b => b.block_id));
  t = await tog('Meeting'); tv2 = t.view || t;
  ok(!blk(tv2, 'allday_toggle') && blk(tv2, 'start'), 'Meeting picked: no box');
  t = await tog('__booth'); tv2 = t.view || t;
  ok(blk(tv2, 'allday_toggle').elements[0].options[0].text.text === 'All day booking', 'M booth picked: All day booking, as before');
  // step 2: an all-day Event - the rooms Room Availability has free all day, as for any Event
  const step2 = async (s, ra) => (await j1(si, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
  const S = { date: '2027-10-23', t0: '00:00', t1: '23:59', purpose: 'Event', kind: 'meeting', requester: 'U1', channel: 'D1', ext: 'x', allDay: true };
  let v2 = await step2(S, { free_priority: ['Lobby', 'Likha'], free_rooms: ['Lobby', 'Likha', 'Katha', 'Studio 7'] });
  const rb = v2.blocks.find(b => /^room(~\d+)?$/.test(b.block_id || '')), radio = rb && (rb.element || (rb.elements || [])[0]);
  ok(radio && radio.options.map(o => o.value).filter(x => x !== '__other').join() === 'Lobby,Likha', 'all-day Event: its usual rooms free all day (the Lobby, Likha), not the Lobby only', radio && radio.options.map(o => o.value));
  v2 = await step2(S, { free_priority: ['Likha'], free_rooms: ['Likha', 'Katha'], busy: ['Lobby'] });
  const rb3 = v2.blocks.find(b => /^room(~\d+)?$/.test(b.block_id || '')), r3 = rb3 && (rb3.element || (rb3.elements || [])[0]);
  ok(r3 && r3.options.map(o => o.value).filter(x => x !== '__other').join() === 'Likha' && /Not free then: Lobby/.test(JSON.stringify(v2.blocks)), 'the Lobby taken all day -> Likha, "Not free then: Lobby"', v2.blocks.map(b => b.block_id));
  v2 = await step2(Object.assign({}, S, { allDay: false, t0: '10:00', t1: '12:00' }), { free_priority: ['Lobby', 'Likha'] });
  const rb2 = v2.blocks.find(b => /^room(~\d+)?$/.test(b.block_id || '')), r2 = rb2 && (rb2.element || (rb2.elements || [])[0]);
  ok(r2 && r2.options.some(o => o.value === 'Likha'), 'an Event with times: the usual rooms, as before');
  console.log('4. The Change form');
  const B = { id: 'ev1', d: '2027-10-23', s: '21:00', e: '23:59', r: 'Studio 7', t: 'ORANGE / HL' };
  const bc = await j1(si, 'Build Change', [], { 'Check Signature': [chk], 'Read Cache 6': cacheRow, 'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify(B) }], container: { channel_id: 'D1', message_ts: '7.7' } } } }] });
  const cs = blk(bc.view, 'start').element, ce = blk(bc.view, 'end').element;
  ok(cs.options[0].text.text === '6:00 AM' && cs.initial_option.text.text === '9:00 PM' && ce.initial_option.value === '23:59' && ce.initial_option.text.text === '11:59 PM'
     && !cs.options.some(o => o.value === '23:59') && ce.options.filter(o => o.value === '23:59').length === 1 && !ce.options.some(o => o.value === '00:00'),
     'a booking to 11:59 PM: Start from 6:00 AM, End 11:59 PM picked (once, not in Start)', [cs.initial_option, ce.initial_option]);
  console.log('5. Typed "whole day" (main)');
  const offer = async (text, dates, bf) => (await j1(main, 'Form Offer', [{ json: {} }], {
    'All Rooms': ['Studio 7', 'Studio 8', 'Likha', 'Lobby', 'M4'].map(x => ({ json: { fields: Object.assign({ 'Room Name': x }, x === 'Lobby' ? { 'Room Type': ['Lobby'] } : x === 'Likha' ? { 'Room Type': ['Conference Room'] } : {}) } })),
    'All Session Types': ['VO Recording', 'Meeting', 'Event'].map(x => ({ json: { fields: { Type: x } } })), 'All Bookers': [],
    'Slack Trigger': [{ json: { text, channel: 'D1', ts: '200' } }], 'Gate Context': [{ json: { datesInMessage: dates || '', todayIso: '2027-10-22', gate: {} } }],
    'Booked For': [{ json: Object.assign({ requesterText: text }, bf || {}) }], 'Get Recent Messages': [{ json: { ts: '200', text, user: 'U1' } }, { json: { bot_id: 'B1', ts: '100', text: 'Hi', blocks: [] } }] })).formOffer;
  let F = await offer('book studio 7 for me the whole day');
  ok(F.offer && F.prefill.r === 'Studio 7' && F.prefill.s === '00:00' && F.prefill.e === '23:59' && !F.prefill.ad && /\*12:00 AM – 11:59 PM\*/.test(F.text), '"book studio 7 for me the whole day" (the 22 Oct test) -> 12:00 AM – 11:59 PM', F.text);
  for (const w of ['all day', 'full day', 'entire day', 'whole-day']) { F = await offer('book studio 8 tomorrow ' + w, '2027-10-23');
    ok(F.prefill.s === '00:00' && F.prefill.e === '23:59', '"' + w + '" -> the whole day'); }
  F = await offer('book m4 the whole day tomorrow', '2027-10-23');
  ok(F.prefill.p === '__booth' && F.prefill.ad === 1 && !F.prefill.s && /\*All day\*/.test(F.text), 'an M booth -> All day (ticked in the form)', F.prefill);
  F = await offer('book the lobby all day tomorrow', '2027-10-23');
  ok(F.prefill.r === 'Lobby' && F.prefill.p === 'Event' && F.prefill.ad === 1 && !F.prefill.s, 'the Lobby -> an Event, All day', F.prefill);
  F = await offer('book the lobby tomorrow 2-4pm', '2027-10-23', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' });
  ok(F.prefill.p === 'Meeting' && !F.prefill.ad && F.prefill.s === '14:00', 'the Lobby with times -> as before');
  F = await offer('book studio 7 tomorrow 2-4pm, all day prep after', '2027-10-23', { timeInNewest: true, timeStart: '14:00', timeEnd: '16:00' });
  ok(F.prefill.s === '14:00' && F.prefill.e === '16:00', 'times typed win over "all day"');
  F = await offer('book studio 7 tomorrow half day', '2027-10-23');
  ok(!F.prefill.s, '"half day" -> no times filled in');
  // Build Reply's Book a room under an answer
  const br = async (text, dates) => (await j1(main, 'Build Reply', [{ json: { output: 'Studio 7 is free all day.' } }], { 'Guard Probe': [{ json: {} }],
    'Gate Context': [{ json: { datesInMessage: dates || '' } }], 'Booked For': [{ json: {} }], 'Slack Trigger': [{ json: { text } }] }));
  let x = await br('is studio 7 free the whole day tomorrow?', '2027-10-23');
  const bv = x.reply.blocks[x.reply.blocks.length - 1].elements[0].value;
  ok(/"s":"00:00"/.test(bv) && /"e":"23:59"/.test(bv) && /"r":"Studio 7"/.test(bv), 'an answer about "the whole day": Book a room opens 12:00 AM – 11:59 PM', bv);
  x = await br('is m4 free all day tomorrow?', '2027-10-23');
  ok(!/"s":/.test(x.reply.blocks[x.reply.blocks.length - 1].elements[0].value), 'an M booth: no times (the form\'s All day box)');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + (e && e.stack || e)); process.exit(1); });
