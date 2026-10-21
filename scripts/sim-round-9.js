#!/usr/bin/env node
// Round 9 offline (Slack Interactions v26 + main v276 + Book Session v113, 19 Oct): the year on long dates, no "Not a usual
// room" lines, "Available rooms:" + why when no usual room is free, Studio E only for Post Processing, optional dropdowns that
// read "No booth / No engineer / No arranger" (no "No …" options), no "pick one or both", "Recommended rooms:" / "Choose a
// different room", at most 6 rooms in the list.
// Usage: node scripts/sim-round-9.js [slack-interactions v26] [main v276] [book-session v113]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v26.json', 'utf8'));
const V39 = JSON.stringify(si.nodes).indexOf('a phone shows no') !== -1;   // v39: "No booth / engineer / arranger" back, last (phones cannot clear a pick)
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/project-jessie-v276.json', 'utf8'));
const bs = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/book-session-v113.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
// v39 (22 Oct): the "No …" dropdowns became required with "No …" picked (no Slack "Clear selection"). The checks below were written
// for optional + empty, which means the same thing - so on v39+ a picked "No …" reads as empty and optional (sim-v39-dropdowns checks v39 itself)
const V39B = (wf => JSON.stringify(wf.nodes).indexOf('required (no Slack') !== -1);
function norm39(x, wf) { if (!V39B(wf)) return x; const walk = o => { if (Array.isArray(o)) return o.forEach(walk); if (!o || typeof o !== 'object') return;
    if (o.type === 'input' && o.element && o.element.type === 'static_select' && (o.element.options || []).some(p => p.value === 'none')) {
      o.optional = true; if (o.element.initial_option && o.element.initial_option.value === 'none') delete o.element.initial_option; }
    for (const k of Object.keys(o)) walk(o[k]); };
  walk(x); return x; }
async function runIn(wf, name, input, outs) {
  const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return norm39(await new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input), wf);
}
const j1 = async (...a) => (await runIn(si, ...a))[0].json;
const rooms = FX.rooms.concat([{ id: 'r4', fields: { 'Room Name': 'Studio 4', 'Room Type': ['Recording Control Room'] } },
  { id: 'sm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Van'] } }]);
const ST = (t, pri, roles, req) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': req || '' } });
const sessionTypes = FX.sessionTypes.concat([ST('Music Vocal Recording', ['rf', 'rc'], ['Music Engineer', 'Music Arranger']), ST('Event', ['lo', 'ka', 'lk', 'sa', 'rf', 'rc'], ['None']),
  ST('Van Recording', ['sm'], ['Post Engineer', 'Music Arranger'])]);
const B = (id, name, ini, slack, info) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: ['Audio Post'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.'), B('b4', 'Joaquin Santos', 'JS', 'U9', 'Music Arranger, Goes by Joaquin.'),
  B('b5', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer'), B('b7', 'Dylan Diaz', 'DD', 'U0BQ77XKWA3', 'Multimedia Specialist')];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-19', t0: '08:00', t1: '10:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
const blk = (v, id) => v.blocks.find(b => b.block_id === id);
const blkRe = (v, re) => v.blocks.find(b => re.test(b.block_id || ''));
const radioOf = v => { const b = blkRe(v, /^room(~\d+)?$/); return b && (b.element || (b.elements || [])[0]); };
const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
const M = (purpose, kind, extra) => Object.assign(S(purpose, kind), { label: purpose }, extra || {});
const views = [];

(async () => {
  console.log('1: the year on long dates');
  let v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio 8'] });
  views.push(v);
  ok(/🗓️ \*Tuesday, Oct 19, 2027 · 8:00 AM–10:00 AM · VO Recording\*/.test(JSON.stringify(v.blocks[1])), 'step 2\'s header - "Tuesday, Oct 19, 2027"');
  let r = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } }, M('VO Recording', 'studio', { msg: { ch: 'D1', ts: '5.5' } }));
  ok(r.answer.view.blocks[0].text.text === '⏳ *Booking Studio 7…*\nTuesday, October 19, 2027\n8:00 AM – 10:00 AM', 'the Booking… window - "Tuesday, October 19, 2027"');
  const MS = await j1('Mark Source', [{ json: { ok: true, messages: [{ ts: '5.5', text: 'x', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Hi, I’m Jessie!' } }] }] } }], { 'Read Step 2': [{ json: r }] });
  ok(MS.blocks[0].text.text === 'Your booking details:\n🗓️ *Studio 7 · Tuesday, October 19, 2027 · 8:00 AM – 10:00 AM*', '"Your booking details:" - with the year');
  const fo = main.nodes.find(n => n.name === 'Form Offer').parameters.jsCode;
  ok((fo.match(/year: 'numeric'/g) || []).length === 2, 'main: the offer\'s date and a series\' "until" carry the year');
  const allDay = await read2({ room: { room_radio: tv('M2') }, forname: { forname_in: { value: 'Howard' } } }, M('', 'booth', { allDay: true, t0: '00:00', t1: '23:59', label: 'M booth' }));
  ok(allDay.answer.view.blocks[0].text.text === '⏳ *Booking M2…*\nTuesday, October 19, 2027\nAll day', 'an all-day M booth - the year, then "All day" (the screenshot)');

  console.log('7 / 2: the labels, no "Recommended", no "Not a usual room"');
  ok(blk(v, 'room_label').text.text === '*Recommended rooms:*' && !radioOf(v).options.some(o => o.description) && radioOf(v).initial_option.value === 'Studio 7', '"Recommended rooms:", no line under any room, the top one ticked');
  const ro = blk(v, 'room_other');
  ok(ro.label.text === 'Choose a different room' && !ro.hint && ro.element.placeholder.text === 'Select a room', '"Choose a different room", no hint');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2', 'Studio A'] });
  ok(blk(v, 'room_label').text.text === '*Recommended studios:*', 'Localization Dubbing - "Recommended studios:"');
  views.push(v);

  console.log('3: no usual room free');
  v = await step2(S('VO Recording', 'studio'), { free_priority: [], free_last_resort: ['Studio 5', 'Studio 6'], busy: ['Studio 7 (X)', 'Studio 8 (Y)'] });
  views.push(v);
  const ids = v.blocks.map(b => b.block_id);
  ok(blk(v, 'room_label').text.text === '*Available rooms:*' && blk(v, 'room_why').elements[0].text === 'The usual rooms for this type of booking are not available in your chosen schedule'
     && ids.indexOf('room_why') === ids.indexOf('room_label') + 1 && ids.indexOf('room') === ids.indexOf('room_why') + 1, '"Available rooms:" and the line right under it, above the options');
  ok(!radioOf(v).options.some(o => o.description), 'no line on any option');
  r = await read2({ room: { room_radio: tv('Studio 5') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } }, JSON.parse(v.private_metadata));
  ok(r.valid && r.prep.room_override === true, 'still booked as asked (remembered as not usual)');
  v = await step2(S('VO Recording', 'studio', { pre: { r: 'Studio 5' } }), { free_priority: ['Studio 7'], free_last_resort: ['Studio 5'] });
  ok(radioOf(v).initial_option.value === 'Studio 5' && !radioOf(v).initial_option.description && blk(v, 'room_label').text.text === '*Recommended rooms:*', 'a typed room that is not usual - chosen, no line');
  const allText = JSON.stringify(views.concat([v]));
  ok(!/not a usual room/i.test(allText), 'no "Not a usual room" anywhere');

  console.log('8: at most 6 in the list');
  v = await step2(S('Event', 'meeting'), { free_priority: ['Lobby', 'Katha', 'Likha', 'Salin', 'Studio F', 'Studio C', 'Studio 7', 'Studio 8'] });
  const opts = radioOf(v).options.map(o => o.value), other = blk(v, 'room_other').element.options.map(o => o.value);
  ok(opts.length === 6 && opts[0] === 'Lobby', 'an Event with 8 free usual rooms -> 6 in the list - ' + opts.join());
  ok(other.indexOf('Studio 7') !== -1 && other.indexOf('Studio 8') !== -1, 'the other free ones under "Choose a different room"');

  console.log('4: Studio E only for Post Processing');
  v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'] });
  ok(blk(v, 'room_other').element.options.every(o => o.value !== 'Studio E' && o.value !== 'Studio M'), 'VO Recording - neither Studio E nor Studio M under "Choose a different room"');
  v = await step2(S('Meeting', 'meeting'), { free_priority: ['Likha'] });
  ok(blk(v, 'room_other').element.options.every(o => o.value !== 'Studio E'), 'a meeting - no Studio E (the screenshot)');
  v = await step2(S('Post Processing', 'post'), { free_priority: ['Studio E'] });
  ok(radioOf(v).options.map(o => o.value).join() === 'Studio E', 'Post Processing - Studio E');
  const buildChange = async (b) => (await j1('Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
  let cv = await buildChange({ id: 'e1', d: '2027-10-19', s: '08:00', e: '10:00', r: 'Studio 7', t: 'X / HL', st: 'VO Recording' });
  ok(blk(cv, 'room').element.options.every(o => o.value !== 'Studio E' && o.value !== 'Studio M'), 'the Change form - no Studio E / Studio M for a VO Recording');
  const cc = bs.nodes.find(n => n.name === 'Check Conflicts').parameters.jsCode;
  const i = cc.indexOf('// v112 (round 8): single-room'), j = cc.indexOf('const keys = Object.keys(ROOMS);', i);
  const rule = new Function('REQ', 'wantedNames', cc.slice(i, j) + '\nreturn null;');
  const x = rule({ session_type: 'VO Recording' }, ['Studio E']);
  ok(x && x[0].json.human === 'Studio E is only for Post Processing. Nothing was booked.', 'Book Session: Studio E refused for anything else');
  ok(rule({ session_type: 'Post Processing' }, ['Studio E']) === null, 'Book Session: Post Processing in Studio E -> on');

  console.log('5 / 6: optional dropdowns that read "No …"; no "pick one or both"');
  v = await step2(S('Music Vocal Recording', 'studio'), { free_priority: ['Studio F', 'Studio C'] });
  views.push(v);
  const eng = blk(v, 'engineer'), arr = blk(v, 'arranger'), bt = blkRe(v, /^booth~\d+$/);
  ok(eng.optional && eng.element.placeholder.text === 'No engineer' && (V39 ? eng.element.options.slice(-1)[0].value === 'none' : !eng.element.options.some(o => o.value === 'none')), 'Engineer (an arranger also counts) - optional, empty reads "No engineer", no "No engineer" option');
  ok(arr.optional && arr.element.placeholder.text === 'No arranger' && (V39 ? arr.element.options.slice(-1)[0].value === 'none' : !arr.element.options.some(o => o.value === 'none')) && !arr.element.initial_option, 'Arranger - empty reads "No arranger"');
  ok(bt.optional && bt.element.placeholder.text === 'No booth' && (V39 ? bt.element.options.slice(-1)[0].value === 'none' : !bt.element.options.some(o => o.value === 'none')), 'Vocal booth - empty reads "No booth"');
  ok(!blk(v, 'team_note') && !/pick one or both/.test(JSON.stringify(v)), 'no "Engineer and arranger: pick one or both."');
  v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'] });
  ok(!blk(v, 'engineer').optional && blk(v, 'engineer').element.placeholder.text === 'Select an engineer', 'VO Recording - the engineer still required, "Select an engineer"');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio A'] });
  ok(!blkRe(v, /^booth~\d+$/).optional && blkRe(v, /^booth~\d+$/).element.placeholder.text === 'Select a booth', 'a booth the session needs - still required, set to the usual one');
  const mv = M('Music Vocal Recording', 'studio');
  r = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'song' } }, arranger: { arranger_pick: tv('U9') } }, mv);
  ok(r.valid && r.calTitle === 'SONG / JS' && /no engineer/.test(r.prep.requester_text), 'engineer left empty + an arranger -> SONG / JS, "no engineer"');
  r = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'song' } }, engineer: { engineer_pick: tv('U2') } }, mv);
  ok(r.valid && r.calTitle === 'SONG / DR' && /no arranger/.test(r.prep.requester_text), 'arranger left empty -> "no arranger" (never asked)');
  r = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'song' } } }, mv);
  ok(!r.valid && r.answer.errors.engineer === 'Pick an engineer or an arranger.', 'both empty -> "Pick an engineer or an arranger."');
  r = await read2({ room: { room_radio: tv('Studio F') }, 'booth~1': { booth_pick: {} }, project: { project_in: { value: 'song' } }, engineer: { engineer_pick: tv('U2') } }, mv);
  ok(r.valid && r.prep.rooms === 'Studio F', 'booth left empty -> no booth');
  // the Change form
  cv = await buildChange({ id: 'e2', d: '2027-10-19', s: '08:00', e: '10:00', r: 'Studio F, Studio A', t: 'SONG / DR', st: 'Music Vocal Recording' });
  const de = blk(cv, 'det_engineer'), da = blk(cv, 'det_arranger'), bc = blk(cv, 'booth_c');
  ok(de.optional && de.element.placeholder.text === 'No engineer' && de.element.initial_option.value === 'U2' && (V39 ? de.element.options.slice(-1)[0].value === 'none' : !de.element.options.some(o => o.value === 'none')), 'Change: Engineer - the booking\'s, empty reads "No engineer"');
  ok(da.element.placeholder.text === 'No arranger' && (V39 ? (!da.element.initial_option || da.element.initial_option.value === 'none') : !da.element.initial_option) && (V39 ? da.element.options.slice(-1)[0].value === 'none' : !da.element.options.some(o => o.value === 'none')), 'Change: Arranger - none on the booking -> empty, "No arranger"');
  ok(bc.optional && bc.element.placeholder.text === 'No booth' && bc.element.initial_option.value === 'Studio A' && (V39 ? bc.element.options.slice(-1)[0].value === 'none' : !bc.element.options.some(o => o.value === 'none')), 'Change: Vocal booth - Studio A, can be emptied');
  ok(!blk(cv, 'team_note'), 'Change: no "pick one or both"');
  const rcv = async (m, vals) => j1('Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(m), state: { values: vals } } } } }], 'Read Cache 10': cacheRow });
  const base = { date: { date_pick: { selected_date: '2027-10-19' } }, start: { start_pick: tv('08:00') }, end: { end_pick: tv('10:00') }, room: { room_pick: tv('Studio F') },
    purpose_c: { purpose_c: tv('Music Vocal Recording') }, det_project: { det_project_in: { value: 'SONG' } }, det_client: { det_client_in: { value: '' } }, det_engineer: { det_engineer_pick: tv('U2') } };
  let rc = await rcv(JSON.parse(cv.private_metadata), Object.assign({}, base, { booth_c: { booth_c_pick: {} } }));
  ok(rc.valid && rc.newRooms === 'Studio F' && rc.roomChanged, 'Change: booth emptied -> Studio F alone');
  rc = await rcv(JSON.parse(cv.private_metadata), Object.assign({}, base, { booth_c: { booth_c_pick: tv('Studio A') }, det_arranger: { det_arranger_pick: tv('U9') } }));
  ok(rc.valid && rc.newTitle === 'SONG / DR x JS', 'Change: an arranger added -> SONG / DR x JS');
  rc = await rcv(JSON.parse(cv.private_metadata), Object.assign({}, base, { booth_c: { booth_c_pick: tv('Studio A') } }));
  ok(!rc.valid && rc.answer.errors.date === 'Nothing changed.', 'Change: nothing changed (empty arranger = none, as before)');

  console.log('every rendered view');
  let descs = 0, noneOpts = 0;
  const walk = x => { if (!x || typeof x !== 'object') return;
    if (/^(static_select|multi_static_select|radio_buttons)$/.test(x.type)) for (const o of [].concat(x.options || [])) { if (o.value === 'none') noneOpts++; if (x.type !== 'radio_buttons' && o.description) descs++; }
    for (const k of Object.keys(x)) walk(x[k]); };
  views.concat([cv]).forEach(walk);
  if (!V39) ok(noneOpts === 0, 'no "No …" option in any dropdown (' + noneOpts + ')');   // v39: they are back (phones cannot clear a pick)
  ok(descs === 0, 'no dropdown option carries a description');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
