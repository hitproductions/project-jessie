#!/usr/bin/env node
// Round 5 offline (Slack Interactions v22 + Move Booking v32), on the 15 Oct Airtable rooms (scripts/sim-fixture-rooms.js):
//   1 booths without "the engineer patches it"; 2 "Another room…" as the last room choice; 3 the working lines;
//   4 the Change form on an all-day booking; 5 No engineer (music); 6 rooms in order + the Change form's Studio / Booth / Holding.
// Usage: node scripts/sim-round-5.js [slack-interactions v22] [move-booking v32]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v22.json', 'utf8'));
const V39 = JSON.stringify(si.nodes).indexOf('a phone shows no') !== -1;   // v39: "No booth / engineer / arranger" back, last (phones cannot clear a pick)
// v53 (28 Oct): the Vocal booth(s) is a multi-select - no "No booth" item; the picked booths read the same on either shape
const V53 = JSON.stringify(si.nodes).indexOf("label: pt('Vocal booths')") !== -1;
const bPick = bl => (bl && bl.element ? [].concat(bl.element.initial_options || (bl.element.initial_option ? [bl.element.initial_option] : [])) : []).map(o => o.value).filter(x => x !== 'none');
const V26 = /function roomAllowed\(/.test(JSON.stringify(si.nodes));   // round 9: room labels, no descriptions, no "No …" options (sim-round-9)
const mv = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/move-booking-v32.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = n => si.nodes.find(x => x.name === n).parameters.jsCode;
// v39 (22 Oct): the "No …" dropdowns became required with "No …" picked (no Slack "Clear selection"). The checks below were written
// for optional + empty, which means the same thing - so on v39+ a picked "No …" reads as empty and optional (sim-v39-dropdowns checks v39 itself)
const V39B = (wf => JSON.stringify(wf.nodes).indexOf('required (no Slack') !== -1);
function norm39(x, wf) { if (!V39B(wf)) return x; const walk = o => { if (Array.isArray(o)) return o.forEach(walk); if (!o || typeof o !== 'object') return;
    if (o.type === 'input' && o.element && o.element.type === 'static_select' && (o.element.options || []).some(p => p.value === 'none')) {
      o.optional = true; if (o.element.initial_option && o.element.initial_option.value === 'none') delete o.element.initial_option; }
    for (const k of Object.keys(o)) walk(o[k]); };
  walk(x); return x; }
async function run(name, input, outs) {
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return norm39(await new Function('$', '$input', 'return (async function(){' + jsOf(name) + '\n}).call(this);').call({ helpers: {} }, $, $input), si);
}
const j1 = async (...a) => (await run(...a))[0].json;
const bookers = FX.bookers.concat([{ id: 'b9', fields: { Name: 'Joaquin Santos', Initials: 'JS', 'Slack User ID': 'U9', Info: 'Music Arranger, Goes by Joaquin.' } }]);
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-19', t0: '13:00', t1: '15:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow })).view;
const toggle = async (view, action, extra, state) => j1('Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
  actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow });
const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
const M = (purpose, kind, extra) => Object.assign(S(purpose, kind), { when: 'Tuesday, Oct 19 · 1:00 PM–3:00 PM', label: purpose }, extra || {});

const V24 = JSON.stringify(si).indexOf('function typeRoles(') !== -1;   // v24: No engineer superseded by "pick one or both" (sim-round-7)
const V25 = JSON.stringify(si).indexOf('function onlyRoom(') !== -1;   // v25: booth / Another room as dropdowns, shorter working lines (sim-round-8)
(async () => {
  // ---- 1: booths
  let v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2', 'Studio A', 'Studio B', 'Studio D'] });
  let bt = v.blocks.find(b => /^booth(~\d+)?$/.test(b.block_id || ''));
  if (V25) ok(bt.element.type === (V53 ? 'multi_static_select' : 'static_select') && bt.element.options[0].text.text === 'Studio A (usual)' && bPick(bt).join() === 'Studio A' && !bt.hint && !/engineer patches/.test(JSON.stringify(v)),
    '1 (v25): the booth a dropdown, the usual one first and set, "(usual)", no hint - ' + bt.element.options[0].text.text);
  else {
  ok(bt.element.options[0].description.text === 'Studio 1’s usual booth' && bt.element.options.slice(1).every(o => !o.description) && !/engineer patches/.test(JSON.stringify(v)),
     '1: booths - only the usual one has a line; no "the engineer patches it (Dante)" anywhere (Slack 18:50)');
  ok(bt.hint.text === 'Set to Studio 1’s usual booth. Any free booth works.', '1: hint - ' + bt.hint.text);
  }

  // ---- 2: Another room…
  v = await step2(S('Music Mixing', 'studio'), { free_priority: ['Studio F'] });
  const rb = v.blocks.find(b => b.block_id === 'room');
  let t;
  if (!V25) {
  ok(!v.blocks.some(b => b.block_id === 'room_toggle') && rb.element.options.slice(-1)[0].value === '__other' && rb.element.options.slice(-1)[0].text.text === '_Another room…_'
     && rb.dispatch_action === true, '2: "Another room…" is the last choice; no "Use another room" row');
  t = await toggle(v, 'room_radio', { selected_option: { value: '__other' } }, { room: { room_radio: tv('__other') } });
  let ix = t.view.blocks.map(b => b.block_id);
  const ro = t.view.blocks.find(b => b.block_id === 'room_other');
  ok(ix.indexOf('room_other') === ix.indexOf('room') + 1 && ro.element.options.length > 3 && ro.element.options.every(o => !o.description), '2: picking it opens the dropdown right under the list');
  t = await toggle(t.view, 'room_radio', { selected_option: { value: 'Studio F' } }, { room: { room_radio: tv('Studio F') } });
  ok(!t.view.blocks.some(b => b.block_id === 'room_other'), '2: back to a listed room -> the dropdown goes');
  }
  const meta2 = JSON.parse(v.private_metadata);
  let r2 = await read2({ room: { room_radio: tv('__other') }, room_other: { room_other_pick: tv('Studio 2') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } }, meta2);
  ok(r2.valid && r2.prep.rooms === 'Studio 2' && r2.prep.room_override === true, '2: Another room -> Studio 2, booked as asked');
  r2 = await read2({ room: { room_radio: tv('__other') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } }, meta2);
  ok(!r2.valid && r2.answer.errors.room, '2: Another room with nothing picked -> "Pick a room."');

  // ---- 3: the working lines
  const allCode = si.nodes.map(n => n.parameters.jsCode || '').join('\n');
  ok(!/This takes a few seconds/.test(allCode) && !/You’ll be notified when it’s done/.test(allCode), '3: no "This takes a few seconds." / old close line anywhere');
  if (V25) ok(/You can close this window – we’ll let you know (?:in your DM )?once it’s done\./.test(jsOf('Read Step 2')) && !/Your booking is being processed/.test(jsOf('Read Step 2'))
     && /'(?: \+ ')?\s?You can close this window – we’ll let you know (?:in your DM )?once it’s done\.'/.test(jsOf('Read Change'))
     && /(?:Multiple bookings may take longer to process\. |_wait \+ ' )You can close this window – we’ll let you know (?:in your DM )?once it’s done\./.test(jsOf('Read Series Confirm'))
     && /'Checking availability for each date\.(?: You can close this window – we’ll let you know in your DM\.| ' \+ _wait \+ ' You can close this window – we’ll let you know in your DM\.)?'/.test(jsOf('Read Step 2')), '3 (v25): the working lines in fewer words');
  else ok(/Your booking is being processed\. You may close this window – we’ll notify you once it’s done\./.test(jsOf('Read Step 2'))
     && /'You may close this window – we’ll notify you once it’s done\.'/.test(jsOf('Read Change'))
     && /This may take a while\. You may close this window – we’ll notify you once it’s done\./.test(jsOf('Read Series Confirm'))
     && /'Checking availability for each date\.(?: You can close this window – we’ll let you know in your DM\.| ' \+ _wait \+ ' You can close this window – we’ll let you know in your DM\.)?'/.test(jsOf('Read Step 2')), '3: the four working lines');

  // ---- 4: Change on an all-day booking
  const buildChange = async (b) => j1('Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow });
  const m5 = { id: 'ev5', d: '2027-10-15', s: '00:00', e: '00:00', r: 'M5', t: 'M5 - Howard' };
  let cv = (await buildChange(m5)).view;
  ix = cv.blocks.map(b => b.block_id);
  ok(ix.indexOf('allday_toggle') === ix.indexOf('date') + 1 && cv.blocks.find(b => b.block_id === 'allday_toggle').elements[0].initial_options && ix.indexOf('start') === -1 && ix.indexOf('end') === -1,
     '4: an all-day M5 -> All day booking ticked, no Start / End (Slack 18:55: 12:00 AM – 12:00 AM, "end has to be after the start")');
  ok(/Now: Fri, Oct 15 · all day · M5/.test(cv.blocks[0].text.text), '4: "Now: … all day" - ' + cv.blocks[0].text.text.split('\n')[1]);
  const readChange = async (meta, vals) => j1('Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(meta), state: { values: vals } } } } }], 'Read Cache 10': cacheRow });
  const cm = JSON.parse(cv.private_metadata);
  let rc = await readChange(cm, { date: { date_pick: { selected_date: '2027-10-15' } }, allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } }, room: { room_pick: tv('M7') } });
  ok(rc.valid && rc.roomChanged && rc.n.allDay && rc.n.s === '00:00', '4: room only -> valid, still all day');
  let tm = await j1('To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(tm.go && tm.new_start_iso === '2027-10-15T00:00:00+08:00' && tm.new_end_iso === '2027-10-16T00:00:00+08:00' && tm.new_rooms === 'M7', '4: Move gets 12:00 AM to 12:00 AM the next day, in M7');
  rc = await readChange(cm, { date: { date_pick: { selected_date: '2027-10-15' } }, allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } }, room: { room_pick: tv('M5') } });
  ok(!rc.valid && /Nothing changed/.test(rc.answer.errors.date), '4: nothing changed -> said');
  t = await toggle(cv, 'allday_toggle', { selected_options: [] }, {});
  ix = t.view.blocks.map(b => b.block_id);
  ok(ix.indexOf('start') === ix.indexOf('date') + 1 && ix.indexOf('end') === ix.indexOf('start') + 1, '4: unticked -> Start / End back');
  cv = (await buildChange({ id: 'ev1', d: '2027-10-19', s: '13:00', e: '15:00', r: 'Studio 7', t: 'X / HL' })).view;
  ok(!cv.blocks.some(b => b.block_id === 'allday_toggle') && cv.blocks.some(b => b.block_id === 'start'), '4: a timed booking unchanged');

  // ---- 5: No engineer
  v = await step2(S('Music Mixing', 'studio'), { free_priority: ['Studio F'] });
  if (!V24) ok(v.blocks.find(b => b.block_id === 'engineer').element.options[0].value === 'none', '5: Music Mixing - "No engineer" first');
  if (!V24) ok((await step2(S('Music Vocal Recording', 'studio'), { free_priority: ['Studio F'] })).blocks.find(b => b.block_id === 'engineer').element.options[0].value === 'none', '5: Music Vocal Recording too');
  ok((await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'] })).blocks.find(b => b.block_id === 'engineer').element.options[0].value !== 'none', '5: not for VO Recording');
  const mm = Object.assign(M('Music Mixing', 'studio'), {});
  r2 = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'musicmixtest' } }, engineer: { engineer_pick: tv('none') }, arranger: { arranger_pick: tv('U9') } }, mm);
  if (!V24) ok(r2.valid && r2.calTitle === 'MUSICMIXTEST / JS' && /no engineer/.test(r2.prep.requester_text) && r2.prep.engineer === '' && r2.team === 'U9' && !/Engineer:/.test(r2.prep.description),
     '5: No engineer + Joaquin -> MUSICMIXTEST / JS, Book Session told "no engineer"');
  r2 = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') }, arranger: { arranger_pick: tv('none') } }, mm);
  ok(r2.valid && r2.calTitle === 'X / HL', '5: an engineer and no arranger -> as before');
  r2 = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') }, arranger: { arranger_pick: tv('U9') } }, mm);
  ok(r2.valid && r2.calTitle === 'X / HL x JS', '5: both -> HL x JS');
  r2 = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('none') }, arranger: { arranger_pick: tv('none') } }, mm);
  if (!V24) ok(!r2.valid && r2.answer.errors.engineer === 'Pick an engineer or an arranger.', '5: neither -> "Pick an engineer or an arranger."');

  // ---- 6: rooms in order, and the Change form like Book
  r2 = await read2({ room: { room_radio: tv('Studio F') }, booth: { booth_pick: tv('Studio D') }, holding: { holding_pick: { selected_options: [{ value: 'Likha' }, { value: 'Katha' }] } },
    project: { project_in: { value: 'celebtest' } }, client: { client_in: { value: 'Jem Lim' } }, engineer: { engineer_pick: tv('U1') } }, M('Celebrity Recording', 'studio'));
  ok(/\| Rooms: Studio F, Studio D, Likha, Katha \|/.test(' | ' + r2.prep.description + ' | '), '6: the booking keeps its rooms in order - ' + r2.prep.description);
  // Google's order, with and without the Rooms line
  const evRoomSrc = jsOf('Render My Bookings');
  const evRoom = new Function(evRoomSrc.slice(evRoomSrc.indexOf('function roomName'), evRoomSrc.indexOf('function evBooking')) + '; return evRoom;')();
  const att = ['KDC Plaza-Top Level-Studio D (5)', 'KDC Plaza-Top Level-Studio F (12)', 'KDC Plaza-Top Level-Likha (Big Room) (12)', 'KDC Plaza-Top Level-Katha (Small Conference) (6)']
    .map(d => ({ resource: true, email: 'x@resource.calendar.google.com', displayName: d }));
  ok(evRoom({ attendees: att, description: 'Engineer: Howard Luistro | Rooms: Studio F, Studio D, Likha, Katha | ref: U1' }) === 'Studio F, Studio D, Likha, Katha', '6: Rooms line -> studio, booth, holding (Google: D, F, Likha, Katha)');
  ok(evRoom({ attendees: att, description: 'ref: U1' }) === 'Studio D, Studio F, Likha, Katha', '6: no Rooms line -> Google\'s order, names cleaned ("Likha (Big Room)" -> Likha)');
  // the CELEBTEST booking from the 15 Oct test (no Rooms line)
  const celeb = { id: 'evc', d: '2027-10-16', s: '11:00', e: '14:00', r: 'Studio D, Studio F, Likha (Big Room), Katha (Small Conference)', t: 'CELEBTEST / Jem Lim / HL' };
  cv = (await buildChange(celeb)).view;
  const sel = id => cv.blocks.find(b => b.block_id === id);
  ok(/Now: Sat, Oct 16 · 11:00 AM – 2:00 PM · Studio F \+ Studio D \+ Likha, Katha/.test(cv.blocks[0].text.text), '6: Now: Studio F + Studio D + Likha, Katha - ' + cv.blocks[0].text.text.split('\n')[1]);
  ok(sel('room').label.text === 'Studio' && sel('room').element.initial_option.value === 'Studio F' && sel('room').element.options.every(o => ['Studio A', 'Studio B', 'Studio D', 'Likha', 'Katha', 'Salin'].indexOf(o.value) === -1),
     '6: Studio = Studio F (was "Room: Studio D"), studios only');
  ok(bPick(sel('booth_c')).join() === 'Studio D' && (V26 ? sel('booth_c').optional && sel('booth_c').element.placeholder.text === 'No booth' && (V39 && !V53 ? sel('booth_c').element.options.slice(-1)[0].value === 'none' : !sel('booth_c').element.options.some(o => o.value === 'none')) : sel('booth_c').element.options[0].value === 'none'), '6: Booth = Studio D, or No booth (v26: empty = No booth)');
  ok(sel('holding_c').element.initial_options.map(o => o.value).join() === 'Katha,Likha' && sel('holding_c').element.options.map(o => o.value).join() === 'Katha,Likha,Salin', '6: Holding rooms - Likha, Katha ticked, Salin offered');
  const ccm = JSON.parse(cv.private_metadata);
  ok(ccm.b.r === 'Studio F, Studio D, Likha, Katha', '6: the form works on the rooms in order');
  const base = { date: { date_pick: { selected_date: '2027-10-16' } }, start: { start_pick: tv('11:00') }, end: { end_pick: tv('14:00') }, room: { room_pick: tv('Studio F') },
    booth_c: { booth_c_pick: tv('Studio D') }, holding_c: { holding_c_pick: { selected_options: [{ value: 'Likha' }, { value: 'Katha' }] } } };
  rc = await readChange(ccm, base);
  ok(!rc.valid && /Nothing changed/.test(rc.answer.errors.date), '6: nothing changed -> said');
  rc = await readChange(ccm, Object.assign({}, base, { start: { start_pick: tv('08:00') }, end: { end_pick: tv('11:00') } }));
  tm = await j1('To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(rc.valid && !rc.roomChanged && tm.new_rooms === '' && tm.new_details === '', '6: a time change keeps every room (Move keeps them)');
  rc = await readChange(ccm, Object.assign({}, base, { booth_c: { booth_c_pick: tv('none') }, holding_c: { holding_c_pick: { selected_options: [{ value: 'Likha' }] } } }));
  tm = await j1('To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(rc.valid && rc.roomChanged && tm.new_rooms === 'Studio F, Likha' && JSON.parse(tm.new_details).Rooms === 'Studio F, Likha', '6: No booth, Likha only -> Studio F, Likha (and its Rooms line)');
  ok(/\*Room:\* Studio F\\n\*Holding room:\* Likha/.test(JSON.stringify(rc.answer)), '6: the Changing… card');
  rc = await readChange(ccm, Object.assign({}, base, { booth_c: { booth_c_pick: tv('none') }, holding_c: { holding_c_pick: { selected_options: [] } } }));
  tm = await j1('To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(tm.new_rooms === 'Studio F' && JSON.parse(tm.new_details).Rooms === '', '6: down to one room -> the Rooms line goes');
  // a plain one-room booking: no booth / holding fields
  cv = (await buildChange({ id: 'ev1', d: '2027-10-19', s: '13:00', e: '15:00', r: 'Studio 7', t: 'X / HL' })).view;
  ok(!cv.blocks.some(b => b.block_id === 'booth_c' || b.block_id === 'holding_c') && cv.blocks.find(b => b.block_id === 'room').label.text === 'Room', '6: a one-room booking unchanged');
  // Change details: No engineer
  const dt = V24 ? { view: cv } : await toggle(cv, 'details_toggle', { selected_options: [{ value: 'det' }] }, {});
  if (!V24) ok(dt.view.blocks.find(b => b.block_id === 'det_engineer').element.options[0].value === 'none', '5: the Change form\'s details offer No engineer');
  // Move Booking v32 keeps the Rooms line
  const rbm = mv.nodes.find(n => n.name === 'Resolve Booking').parameters.jsCode;
  ok(/if \('Rooms' in nd\) put\('Rooms', nd\.Rooms, false\);/.test(rbm), '6: Move Booking v32 writes the Rooms line');

  // no dropdown option with a description, in any view drawn here
  let bad = 0;
  const walk = x => { if (!x || typeof x !== 'object') return; if (x.type === 'static_select') for (const o of [].concat(x.options || [])) if (o.description) bad++; for (const k of Object.keys(x)) walk(x[k]); };
  [v, t.view, cv, dt.view].forEach(walk);
  ok(bad === 0, 'no dropdown option carries a description');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
