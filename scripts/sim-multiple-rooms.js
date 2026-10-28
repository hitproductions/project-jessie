#!/usr/bin/env node
// Slack Interactions v53 + Reminders v8 (Howard, 28 Oct): one project in several studios is ONE booking - one calendar event with
// every studio on it as a room - and studios can be added or taken off on Change. Every booking type but Van Recording, Atmos and
// Post Processing; meetings and events get several rooms. Vocal booths: several too (a multi-select).
//   node scripts/sim-multiple-rooms.js [slack-interactions v53] [reminders v8] [slack-interactions v52]
const fs = require('fs');
const SI = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v53.json', 'utf8'));
const RM = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/reminders-v8.json', 'utf8'));
const OLD = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/imported/slack-interactions-v52-imported.json', 'utf8'));
if (!/more_rooms_pick/.test(JSON.stringify(SI.nodes))) { console.log('0 ok, 0 failed (an older build: v53 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const run = async (wf, name, input, outs) => {
  const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input); };
const j1 = async (...a) => (await run(...a))[0].json;
const ST = (t, req, pri, last, role) => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': req, Priority: pri, 'Last Resort': last || [], 'Engineer Role Required': role ? [role] : [] } });
const sessionTypes = FX.sessionTypes.concat([ST('Van Recording', '', ['sm'], [], 'Post Engineer'), ST('Atmos Mixing', 'Large', ['rc'], [], 'Post Engineer'), ST('Event', '', [])]);
const rooms = FX.rooms.concat([{ id: 'sm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Van'] } }]);
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers: FX.bookers }) } }];
const tv = v => ({ selected_option: { value: v } }), ms = a => ({ selected_options: a.map(value => ({ value })) });
const blk = (v, id) => v.blocks.find(b => b.block_id === id), blkRe = (v, re) => v.blocks.find(b => re.test(b.block_id || ''));
const ids = v => v.blocks.map(b => b.block_id).filter(Boolean);
const vals = bl => bl ? (bl.element.options || []).map(o => o.value) : null, picked = bl => bl ? [].concat(bl.element.initial_options || []).map(o => o.value) : null;
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-29', t0: '13:00', t1: '16:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const step2 = async (s, ra) => (await j1(SI, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
const read2 = async (vv, s, extra) => j1(SI, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1', channel: 'D1' } }], 'Read Cache 3': cacheRow, 'Timings 2': [],
  'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', blocks: [], private_metadata: JSON.stringify(Object.assign({ when: 'x', label: s.purpose }, s, extra || {})), state: { values: vv } } } } }] });
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const buildChange = async b => (await j1(SI, 'Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
const rcv = async (cv, v) => j1(SI, 'Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata, state: { values: v } } } } }], 'Read Cache 10': cacheRow });
const toggle = async (view, action, extra, state) => (await run(SI, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
  actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow, 'Loc Projects 9': [] }))[0].json.view;
const BK = (st, r, t) => ({ id: 'e1', d: '2027-10-29', s: '13:00', e: '16:00', r, t, st });
const FREE = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio F', 'Studio C', 'Studio E', 'Studio A', 'Studio B', 'Studio D', 'Likha', 'Katha', 'Salin', 'Lobby', 'M1', 'M2', 'Studio M'];

(async () => {
  console.log('Book a room, step 2: + Multiple studios / rooms');
  let v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio 8', 'Studio F', 'Studio C'], free_last_resort: ['Studio 5', 'Studio 6'], free_rooms: FREE, busy: ['Studio 3 (X)'] });
  let mr = blk(v, 'more_rooms');
  ok(mr && mr.optional && mr.label.text === '+ Multiple studios' && mr.element.type === 'multi_static_select' && mr.element.placeholder.text === 'Select more studios' && !mr.element.initial_options,
     'VO Recording: "+ Multiple studios", optional, nothing picked', mr);
  ok(vals(mr).join() === 'Studio 1,Studio 2,Studio 5,Studio 6,Studio 7,Studio 8,Studio C,Studio F', 'every free studio - not Studio 3 (taken), Studio E / M, booths or meeting rooms', vals(mr));
  ok(ids(v).indexOf('more_rooms') > ids(v).findIndex(x => /^booth~/.test(x)) && ids(v).indexOf('more_rooms') < ids(v).indexOf('project'), 'after the booth, before the details');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2', 'Studio 6', 'Studio A', 'Studio B', 'Studio D'], free_rooms: FREE });
  ok(blk(v, 'more_rooms') && vals(blk(v, 'more_rooms')).indexOf('Studio 2') !== -1 && vals(blk(v, 'more_rooms')).indexOf('Studio A') === -1, 'Localization Dubbing: studios offered (booths stay in Vocal booths)');
  v = await step2(S('Meeting', 'meeting'), { free_priority: ['Likha', 'Salin', 'Katha'], free_rooms: FREE });
  mr = blk(v, 'more_rooms');
  ok(mr && mr.label.text === '+ Multiple rooms' && mr.element.placeholder.text === 'Select more rooms' && vals(mr).slice(0, 4).join() === 'Katha,Likha,Lobby,Salin' && vals(mr).indexOf('Studio 7') !== -1
     && vals(mr).indexOf('Studio M') === -1 && vals(mr).indexOf('M1') === -1 && vals(mr).indexOf('Studio A') === -1, 'Meeting: "+ Multiple rooms" - meeting rooms first, then studios (no van, M booths or vocal booths)', vals(mr));
  v = await step2(S('Event', 'meeting'), { free_priority: [], free_rooms: FREE });
  ok(blk(v, 'more_rooms') && blk(v, 'more_rooms').label.text === '+ Multiple rooms', 'Event: "+ Multiple rooms" too');
  for (const [p, k, fr] of [['Van Recording', 'studio', ['Studio M']], ['Atmos Mixing', 'atmos', ['Studio C']], ['Post Processing', 'post', ['Studio E']], ['M booth', 'booth', ['M1', 'M2']]]) {
    v = await step2(S(p, k), { free_priority: fr, free_rooms: FREE });
    ok(!blk(v, 'more_rooms'), p + ': no "+ Multiple" (one room)');
  }
  v = await step2(S('VO Recording', 'studio', { series: { dates: ['2027-10-29', '2027-11-05'] } }), { free_priority: ['Studio 7', 'Studio 8'], free_rooms: FREE, busy: ['Studio F (X)'] });
  ok(blk(v, 'more_rooms') && vals(blk(v, 'more_rooms')).indexOf('Studio F') === -1, 'a series: a studio taken on any date is not offered');

  console.log('Vocal booths: several, a multi-select');
  v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'], free_rooms: FREE });
  let bt = blkRe(v, /^booth~/);
  ok(bt && bt.label.text === 'Vocal booths' && bt.optional && bt.element.type === 'multi_static_select' && !bt.element.initial_options && !vals(bt).includes('none') && bt.element.placeholder.text === 'No booth',
     'VO Recording: Vocal booths optional, nothing picked, empty reads "No booth"', bt);
  ok(bt.element.options[0].text.text === 'Studio A (usual)', 'the usual booth first, "(usual)"');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio A', 'Studio B'], free_rooms: FREE });
  bt = blkRe(v, /^booth~/);
  ok(bt && !bt.optional && picked(bt).join() === 'Studio A' && bt.element.placeholder.text === 'Select a booth', 'Localization Dubbing: required, the usual booth picked', bt);
  let t = await toggle(v, 'room_radio', { selected_option: { value: 'Studio 6' } }, { room: { room_radio: tv('Studio 6') } });
  ok(picked(blkRe(t, /^booth~/)).join() === 'Studio D' && blk(t, 'more_rooms'), 'another studio ticked -> its usual booth (Studio D); + Multiple studios kept');

  console.log('Read Step 2: one booking, every room on it');
  const base = { room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'kuba' } }, engineer: { engineer_pick: tv('U1') } };
  let r = await read2(Object.assign({}, base, { more_rooms: { more_rooms_pick: ms(['Studio 8']) } }), S('VO Recording', 'studio'));
  ok(r.valid && r.prep.rooms === 'Studio 7, Studio 8' && /Rooms: Studio 7, Studio 8/.test(r.prep.description) && r.calTitle === 'KUBA / HL' && r.prep.room_override === false,
     'Studio 7 + Studio 8 -> rooms "Studio 7, Studio 8" on one booking, the Rooms line, the title as before, both usual (no override)', { rooms: r.prep.rooms, t: r.calTitle, o: r.prep.room_override, e: r.answer });
  r = await read2(Object.assign({}, base, { more_rooms: { more_rooms_pick: ms(['Studio 5']) } }), S('VO Recording', 'studio'));
  ok(r.prep.rooms === 'Studio 7, Studio 5' && r.prep.room_override === true, 'a studio that is not a usual VO room -> booked as asked (room_override), like Choose a different room');
  r = await read2(Object.assign({}, base, { more_rooms: { more_rooms_pick: ms(['Studio 7', 'Studio 8']) } }), S('VO Recording', 'studio'));
  ok(r.prep.rooms === 'Studio 7, Studio 8', 'the first room picked again in + Multiple -> once');
  r = await read2(Object.assign({}, base, { more_rooms: { more_rooms_pick: ms(['Studio 8']) }, 'booth~1': { booth_pick: ms(['Studio A', 'Studio B']) } }), S('VO Recording', 'studio'));
  ok(r.prep.rooms === 'Studio 7, Studio 8, Studio A, Studio B', 'two studios and two booths -> all four, studios first');
  r = await read2(Object.assign({}, base, { 'booth~1': { booth_pick: tv('Studio A') } }), S('VO Recording', 'studio'));
  ok(r.prep.rooms === 'Studio 7, Studio A', 'an older form still open (one booth) -> still read');
  r = await read2(Object.assign({}, base, { 'booth~1': { booth_pick: tv('none') } }), S('VO Recording', 'studio'));
  ok(r.prep.rooms === 'Studio 7', 'an older form\'s "No booth" -> no booth');
  r = await read2(Object.assign({}, base), S('VO Recording', 'studio'));
  ok(r.valid && r.prep.rooms === 'Studio 7' && !/Rooms:/.test(r.prep.description), 'nothing added -> one room, as before');
  r = await read2({ room_other: { room_other_pick: tv('ask:P|Studio F') }, project: { project_in: { value: 'kuba' } }, engineer: { engineer_pick: tv('U1') }, more_rooms: { more_rooms_pick: ms(['Studio 8']) } }, S('VO Recording', 'studio'));
  ok(!r.valid && /A request is for one room/.test(r.answer.errors.more_rooms || ''), 'a room request + more studios -> said on the form', r.answer);
  r = await read2({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'all hands' } }, more_rooms: { more_rooms_pick: ms(['Katha']) } }, S('Meeting', 'meeting'));
  ok(r.valid && r.prep.rooms === 'Likha, Katha' && r.calTitle === 'LIKHA - All hands' && r.prep.room_override === false, 'a meeting in Likha + Katha -> one booking, titled by the first room', { rooms: r.prep.rooms, t: r.calTitle, o: r.prep.room_override });
  r = await read2({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'all hands' } }, more_rooms: { more_rooms_pick: ms(['Studio F']) } }, S('Meeting', 'meeting'));
  ok(r.prep.rooms === 'Likha, Studio F' && r.prep.room_override === true, 'a meeting in Likha + Studio F -> Studio F is not a usual meeting room, booked as asked');

  console.log('Change: add or take off studios / rooms');
  let cv = await buildChange(BK('VO Recording', 'Studio 7, Studio 8', 'KUBA / HL'));
  let sc = blk(cv, 'studios_c');
  ok(sc && sc.label.text === '+ Multiple studios' && sc.optional && picked(sc).join() === 'Studio 8' && vals(sc).indexOf('Studio 7') === -1 && vals(sc).indexOf('Studio A') === -1 && vals(sc).indexOf('Studio E') === -1,
     'a booking in Studio 7 + Studio 8 -> + Multiple studios with Studio 8 picked (not Studio 7 itself, booths or Studio E)', sc);
  ok(blk(cv, 'room').element.initial_option.value === 'Studio 7' && blk(cv, 'room').label.text === 'Studio', 'Studio = Studio 7 (the label as before - a VO booking has Vocal booths)');
  const base2 = { date: { date_pick: { selected_date: '2027-10-29' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 7') } };
  let rc = await rcv(cv, Object.assign({}, base2, { studios_c: { more_c_pick: ms([]) } }));
  ok(rc.valid && rc.roomChanged && rc.newRooms === 'Studio 7', 'Studio 8 taken off -> "Studio 7"', { v: rc.valid, r: rc.newRooms });
  let tm = await j1(SI, 'To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(tm.new_rooms === 'Studio 7' && JSON.parse(tm.new_details).Rooms === '', 'Move gets "Studio 7" and the Rooms line goes');
  rc = await rcv(cv, Object.assign({}, base2, { studios_c: { more_c_pick: ms(['Studio 8', 'Studio F']) } }));
  tm = await j1(SI, 'To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(rc.valid && rc.newRooms === 'Studio 7, Studio 8, Studio F' && tm.new_rooms === 'Studio 7, Studio 8, Studio F' && JSON.parse(tm.new_details).Rooms === 'Studio 7, Studio 8, Studio F', 'Studio F added -> all three, one booking');
  rc = await rcv(cv, Object.assign({}, base2, { studios_c: { more_c_pick: ms(['Studio 8']) } }));
  ok(!rc.valid && rc.answer.errors.date === 'Nothing changed.', 'the same studios -> "Nothing changed."');
  rc = await rcv(cv, Object.assign({}, base2, { start: { start_pick: tv('14:00') }, end: { end_pick: tv('17:00') } }));
  tm = await j1(SI, 'To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(rc.valid && !rc.roomChanged && tm.new_rooms === '', 'a time change on an older form (no + Multiple field) keeps both studios');
  cv = await buildChange(BK('VO Recording', 'Studio 7', 'SPOT / HL'));
  ok(blk(cv, 'studios_c') && !picked(blk(cv, 'studios_c')).length, 'a one-studio booking -> + Multiple studios offered, empty');
  rc = await rcv(cv, Object.assign({}, base2, { studios_c: { more_c_pick: ms(['Studio 8']) } }));
  ok(rc.valid && rc.newRooms === 'Studio 7, Studio 8', '...Studio 8 added -> "Studio 7, Studio 8"');
  // the bug this fixes: a second studio was counted as a holding room, so Holding rooms on the form dropped it
  cv = await buildChange(BK('Celebrity Recording', 'Studio F, Studio 8, Studio A, Likha', 'CELEB / Jem Lim / HL'));
  ok(picked(blk(cv, 'studios_c')).join() === 'Studio 8' && picked(blk(cv, 'booth_c')).join() === 'Studio A' && picked(blk(cv, 'holding_c')).join() === 'Likha', 'Celebrity: Studio 8 / Studio A / Likha each in its own field');
  rc = await rcv(cv, Object.assign({}, base2, { room: { room_pick: tv('Studio F') }, holding_c: { holding_c_pick: ms(['Likha', 'Katha']) } }));
  ok(rc.valid && rc.newRooms === 'Studio F, Studio 8, Studio A, Likha, Katha', 'Katha added -> Studio 8 kept (v52 dropped it)', rc.newRooms);
  rc = await (async () => { const a = await j1(OLD, 'Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata,
    state: { values: Object.assign({}, base2, { room: { room_pick: tv('Studio F') }, holding_c: { holding_c_pick: ms(['Likha', 'Katha']) } }) } } } } }], 'Read Cache 10': cacheRow }); return a; })();
  ok(rc.newRooms.indexOf('Studio 8') === -1, '(v52 on the same form: Studio 8 dropped - the bug)', rc.newRooms);
  cv = await buildChange(BK('Celebrity Recording', 'Studio F, Studio A', 'CELEB / Jem Lim / HL'));
  rc = await rcv(cv, Object.assign({}, base2, { room: { room_pick: tv('Studio F') }, booth_c: { booth_c_pick: ms(['Studio A', 'Studio B']) } }));
  ok(rc.valid && rc.newRooms === 'Studio F, Studio A, Studio B', 'Change: a second booth added');
  rc = await rcv(cv, Object.assign({}, base2, { room: { room_pick: tv('Studio F') }, booth_c: { booth_c_pick: ms([]) } }));
  ok(rc.valid && rc.newRooms === 'Studio F', 'Change: every booth taken off -> no booth');
  rc = await rcv(cv, Object.assign({}, base2, { room: { room_pick: tv('Studio F') }, booth_c: { booth_c_pick: tv('none') } }));
  ok(rc.valid && rc.newRooms === 'Studio F', 'an older Change form still open ("No booth") -> no booth');

  console.log('Change: meetings and events');
  cv = await buildChange(BK('Meeting', 'Likha, Katha', 'LIKHA - All hands'));
  let rcb = blk(cv, 'rooms_c');
  ok(rcb && rcb.label.text === '+ Multiple rooms' && picked(rcb).join() === 'Katha' && !blk(cv, 'holding_c') && !blk(cv, 'booth_c') && blk(cv, 'room').element.initial_option.value === 'Likha' && blk(cv, 'room').label.text === 'Room',
     'a meeting in Likha + Katha -> Room: Likha, + Multiple rooms: Katha (no Holding rooms)', ids(cv));
  ok(/Now: .* · Likha \+ Katha/.test(cv.blocks[0].text.text), 'the Now line: "Likha + Katha"', cv.blocks[0].text.text);
  const base3 = Object.assign({}, base2, { room: { room_pick: tv('Likha') } });
  rc = await rcv(cv, Object.assign({}, base3, { rooms_c: { more_c_pick: ms([]) } }));
  ok(rc.valid && rc.newRooms === 'Likha', 'Katha taken off -> "Likha"', rc.newRooms);
  rc = await rcv(cv, Object.assign({}, base3, { rooms_c: { more_c_pick: ms(['Katha', 'Salin']) } }));
  ok(rc.valid && rc.newRooms === 'Likha, Katha, Salin', 'Salin added');
  cv = await buildChange(BK('Meeting', 'Studio F, Likha', 'STUDIO F - Review'));
  ok(blk(cv, 'room').element.initial_option.value === 'Studio F' && picked(blk(cv, 'rooms_c')).join() === 'Likha', 'a meeting in Studio F + Likha keeps Studio F as its room');
  cv = await buildChange(BK('Meeting', 'Likha', 'LIKHA - Sync'));
  ok(blk(cv, 'rooms_c') && !picked(blk(cv, 'rooms_c')).length && blk(cv, 'room').label.text === 'Room', 'a one-room meeting -> + Multiple rooms offered, empty; Room as before');
  for (const [st, r0, tt] of [['Van Recording', 'Studio M', 'VAN / HL'], ['Atmos Mixing', 'Studio C', 'ATMOS / HL'], ['Post Processing', 'Studio E', 'POST PROCESSING - TRAILER / Dilan']]) {
    cv = await buildChange(BK(st, r0, tt));
    ok(!blk(cv, 'studios_c') && !blk(cv, 'rooms_c'), st + ': no + Multiple on Change');
  }
  // the type changed on the form: the picks kept, no duplicate fields
  cv = await buildChange(BK('VO Recording', 'Studio 7, Studio 8', 'KUBA / HL'));
  t = await toggle({ blocks: cv.blocks, private_metadata: cv.private_metadata, callback_id: 'change_booking' }, 'purpose_c', { selected_option: { value: 'Music Mixing' } }, { studios_c: { more_c_pick: ms(['Studio 8', 'Studio F']) } });
  ok(picked(blk(t, 'studios_c')).join() === 'Studio 8,Studio F' && ids(t).filter(x => x === 'studios_c').length === 1, 'type changed -> + Multiple studios kept as picked, once', ids(t));
  t = await toggle({ blocks: cv.blocks, private_metadata: cv.private_metadata, callback_id: 'change_booking' }, 'purpose_c', { selected_option: { value: 'Atmos Mixing' } }, {});
  ok(picked(blk(t, 'studios_c')).join() === 'Studio 8', 'type changed to a one-room type -> the booking\'s other studio still shown, so it can be taken off');

  console.log('Cards');
  const fnOf = (js, n) => js.match(new RegExp('function ' + n + '\\(r\\) \\{[^\\n]*(?:\\n  [^\\n]*)?'))[0] + '\n';
  const abJs = SI.nodes.find(n => n.name === 'After Book').parameters.jsCode;
  const fns = new Function(['roomList', 'roomMain', 'roomHold'].map(n => fnOf(abJs, n)).join('') + 'return { roomMain, roomHold };')();
  ok(fns.roomMain('Studio 7, Studio 8') === 'Studio 7 + Studio 8' && fns.roomHold('Studio 7, Studio 8') === '', 'Studio 7 + Studio 8');
  ok(fns.roomMain('Likha, Katha') === 'Likha + Katha' && fns.roomHold('Likha, Katha') === '', 'a meeting: "Likha + Katha" (was "Likha" + Holding room: Katha)');
  ok(fns.roomMain('Studio F, Studio A, Likha') === 'Studio F + Studio A' && fns.roomHold('Studio F, Studio A, Likha') === 'Likha', 'a session with a booth and a holding room - as before');
  ok(fns.roomMain('M4') === 'M4' && fns.roomMain('Likha') === 'Likha' && fns.roomHold('Likha') === '', 'one room - as before');
  const rmJs = RM.nodes.find(n => /function roomMain/.test(n.parameters.jsCode || '')).parameters.jsCode;
  const rf = new Function(['roomList', 'roomMain', 'roomHold'].map(n => fnOf(rmJs, n)).join('') + 'return { roomMain, roomHold };')();
  ok(rf.roomMain('Likha, Katha') === 'Likha + Katha' && rf.roomHold('Likha, Katha') === '' && rf.roomHold('Studio F, Likha') === 'Likha', 'Reminders v8: the same');

  console.log('Book Session v124 (unchanged) takes what the form sends - To Prepare, then the whole Check Conflicts');
  const BS = JSON.parse(fs.readFileSync(process.argv[5] || 'workflows/imported/book-session-v124-imported.json', 'utf8'));
  const CC = BS.nodes.find(n => n.name === 'Check Conflicts').parameters.jsCode;
  const STAFF = FX.bookers.map(b => Object.assign({ Department: ['Audio Post'] }, b.fields));
  const toBook = async (vv, s) => { const r2 = await read2(vv, s); const prep = await j1(SI, 'To Prepare', [], { 'Read Step 2': [{ json: r2 }], 'Read Cache 3': cacheRow }); return { r2, prep }; };
  const cc = (REQ, evs) => { const items = (evs || []).map(([t, room, a, b]) => ({ id: t, summary: t, location: room, start: { dateTime: '2027-10-29T' + a + ':00+08:00' }, end: { dateTime: '2027-10-29T' + b + ':00+08:00' }, description: 'ref: U9' }));
    const outs = { 'When Executed by Another Workflow': [Object.assign({}, REQ, { staff_data: JSON.stringify(STAFF) })], 'Get Events In Window': [{ items }], 'All Bookers': STAFF.map(f => ({ fields: f })),
      'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
    const $ = n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) });
    return new Function('$', '$input', CC)($, { first: () => ({ json: { items } }), all: () => [{ json: { items } }] })[0].json; };
  let bk = await toBook(Object.assign({}, base, { more_rooms: { more_rooms_pick: ms(['Studio 8']) } }), S('VO Recording', 'studio'));
  let cr = cc(bk.prep);
  ok(cr.verdict === 'CLEAR' && /Studio 7/.test(String(cr.final_rooms || bk.prep.rooms)) && bk.prep.rooms === 'Studio 7, Studio 8', 'Studio 7 + Studio 8 -> CLEAR (both usual VO rooms)', { v: cr.verdict, why: cr.reason, h: cr.human });
  cr = cc(bk.prep, [['OTHER / X', 'Studio 8', '14:00', '15:00']]);
  ok(cr.verdict === 'REJECTED' && /OCCUPIED/.test(cr.reason || ''), 'Studio 8 taken at that time -> refused (ROOM_OCCUPIED), nothing booked', { v: cr.verdict, why: cr.reason });
  bk = await toBook(Object.assign({}, base, { more_rooms: { more_rooms_pick: ms(['Studio 5']) } }), S('VO Recording', 'studio'));
  cr = cc(bk.prep);
  ok(cr.verdict === 'CLEAR', 'Studio 7 + Studio 5 (not a usual VO room) -> CLEAR, booked as asked (room_override)', { v: cr.verdict, why: cr.reason, h: cr.human });
  cr = cc(Object.assign({}, bk.prep, { room_override: false }));
  ok(cr.verdict === 'REJECTED', '(the same without room_override is refused - why the form sets it)', { v: cr.verdict, why: cr.reason });
  bk = await toBook({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'all hands' } }, more_rooms: { more_rooms_pick: ms(['Katha']) } }, S('Meeting', 'meeting'));
  cr = cc(bk.prep);
  ok(cr.verdict === 'CLEAR', 'a meeting in Likha + Katha -> CLEAR', { v: cr.verdict, why: cr.reason, h: cr.human });
  bk = await toBook(Object.assign({}, base, { 'booth~1': { booth_pick: ms(['Studio A', 'Studio B']) } }), S('VO Recording', 'studio'));
  cr = cc(bk.prep);
  ok(cr.verdict === 'CLEAR' && bk.prep.rooms === 'Studio 7, Studio A, Studio B', 'Studio 7 + two vocal booths -> CLEAR', { v: cr.verdict, why: cr.reason, h: cr.human });
  bk = await toBook({ room: { room_radio: tv('Studio 1') }, code: { code_in: { value: 'NET-KUBA' } }, engineer: { engineer_pick: tv('U3') }, 'booth~1': { booth_pick: ms(['Studio A']) }, more_rooms: { more_rooms_pick: ms(['Studio 2']) } }, S('Localization Dubbing', 'loc'));
  cr = cc(bk.prep);
  ok(cr.verdict === 'CLEAR' && bk.prep.rooms === 'Studio 1, Studio 2, Studio A', 'Localization Dubbing in Studio 1 + Studio 2 with Studio A -> CLEAR', { v: cr.verdict, why: cr.reason, h: cr.human, r: bk.prep.rooms });

  console.log('What changed');
  const A = Object.fromEntries(OLD.nodes.map(n => [n.name, n])), B = Object.fromEntries(SI.nodes.map(n => [n.name, n]));
  const changed = Object.keys(B).filter(k => !A[k] || JSON.stringify(A[k].parameters) !== JSON.stringify(B[k].parameters)).sort();
  const V53N = ['After Book', 'After Book Series', 'After Cancel', 'After Move', 'Booked Notices', 'Build Change', 'Build Change C', 'Build Step 1', 'Build Step 2', 'Change Notices',
    'Fix Message', 'My Window', 'Note Toggle', 'Read Change', 'Read Step 2', 'Render My Bookings', 'Series Notices', 'To Move'];
  const V54N = ['After Prepare', 'After Prepare Series', 'Ask DM', 'Question DM', 'Result DM', 'Series DM', 'After Book Series', 'Mark Source Series', 'To Prepare Series', 'Read Step 1'];   // v56: all day repeats (sim-allday-series)   // v55: the note on the DM's button   // v54: picks kept when a form comes back (sim-picks-kept)
  ok(V53N.every(n => changed.indexOf(n) !== -1) && changed.every(n => V53N.indexOf(n) !== -1 || V54N.indexOf(n) !== -1), 'only the form, Change and card nodes changed (since v52)', changed);
  ok(JSON.stringify(SI.connections) === JSON.stringify(OLD.connections) && SI.nodes.length === OLD.nodes.length, 'wiring unchanged, no node added or removed');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + e.stack); process.exit(1); });
