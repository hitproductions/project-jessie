#!/usr/bin/env node
// Round 4 offline (Slack Interactions v21), on the real Airtable rooms and session types (15 Oct):
//   1 "Use another room" routed and drawn without option descriptions; 2 holding rooms and vocal booths on top of the studio;
//   3 studio + booth pairing (Paired with, the usual one first, reset on a studio change); 4 QC = Localization details;
//   5 Post Processing: Booker Dylan Diaz, a project title, no client; 6 M booth all day.
// Usage: node scripts/sim-round-4.js [slack-interactions v21]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v21.json', 'utf8'));
const V39 = JSON.stringify(si.nodes).indexOf('a phone shows no') !== -1;   // v39: "No booth / engineer / arranger" back, last (phones cannot clear a pick)
const V26 = /function roomAllowed\(/.test(JSON.stringify(si.nodes));   // round 9: room labels, no descriptions, no "No …" options (sim-round-9)
const V33P = /v33 \(Howard, 20 Oct\): "Who is it for\?"/.test((si.nodes.find(n => n.name === 'Build Step 2') || { parameters: {} }).parameters.jsCode || '');   // v33: Post Processing asks Who is it for?
const V30 = /function pairBlocksC\(/.test(JSON.stringify(si.nodes));   // round 12: Booker dropdown, code without Enter (sim-round-12)
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
const jsOf = n => si.nodes.find(x => x.name === n).parameters.jsCode;
async function run(name, input, outs) {
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] });
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + jsOf(name) + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;

// ---- the reference cache: Rooms & Studios and Session Types as Airtable has them (15 Oct)
const R = (id, name, f) => ({ id, fields: Object.assign({ 'Room Name': name }, f || {}) });
const CR = { 'Room Type': ['Recording Control Room'] };
const rooms = [
  R('r1', 'Studio 1', Object.assign({ 'Paired with': 'Studio A, Can change using Dante' }, CR)),
  R('r2', 'Studio 2', Object.assign({ 'Paired with': 'Studio B, Can change using Dante' }, CR)),
  R('r3', 'Studio 3', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante' }, CR)),
  R('r5', 'Studio 5', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante' }, CR)),
  R('r6', 'Studio 6', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante' }, CR)),
  R('r7', 'Studio 7', Object.assign({ 'Paired with': 'Studio A, B, or D, Can change using Dante', 'Records Vocals In-Room': true }, CR)),
  R('r8', 'Studio 8', Object.assign({ 'Records Vocals In-Room': true }, CR)),
  R('rf', 'Studio F', Object.assign({ 'Records Vocals In-Room': true }, CR)),
  R('rc', 'Studio C', Object.assign({ 'Records Vocals In-Room': true }, CR)),
  R('re', 'Studio E', { 'Room Type': ['Editing', 'Color Grading', 'Video Editing'], 'Paired with': 'Studio 7, Can change using Dante' }),
  R('ra', 'Studio A', { 'Room Type': ['Recording Booth'], 'Vocal Booth': true }),
  R('rb', 'Studio B', { 'Room Type': ['Recording Booth'], 'Vocal Booth': true }),
  R('rd', 'Studio D', { 'Room Type': ['Recording Booth', 'Editing'], 'Vocal Booth': true, 'Paired with': 'Studio 6, Can change using Dante', 'Records Vocals In-Room': true }),
  R('lk', 'Likha', { 'Room Type': ['Conference Room'] }), R('ka', 'Katha', { 'Room Type': ['Conference Room'] }), R('sa', 'Salin', { 'Room Type': ['Conference Room'] }),
  R('lo', 'Lobby', { 'Room Type': ['Lobby'] }), R('m1', 'M1', { 'Room Type': ['M Booth'] }), R('m2', 'M2', { 'Room Type': ['M Booth'] })];
const ST = (t, req, pri, last, role) => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': req, Priority: pri, 'Last Resort': last || [], 'Engineer Role Required': role ? [role] : [] } });
const sessionTypes = [
  ST('Celebrity Recording', 'Large, pair with one or more conference room as holding areas', ['rf', 'lk', 'ka', 'sa', 'rc'], ['r7', 'r8'], 'Music Engineer'),
  ST('Localization Dubbing', 'Separate vocal booth', ['r1', 'ra', 'rb', 'r2', 'rd', 'r6'], ['re', 'r7'], 'Loc Engineer'),
  ST('QC', 'Medium to large', ['r3', 'r5', 'r7', 'm1'], ['r6'], 'Loc Engineer'),
  ST('Post Processing', 'Medium to large', ['re'], [], 'Multimedia Specialist'),
  ST('VO Recording', 'Stereo Mixing', ['r7', 'r8', 'rf', 'rc'], ['r5', 'r6'], 'Post Engineer'),
  ST('Music Mixing', 'Small to medium', ['rf'], ['rc', 'r7', 'r8'], 'Music Engineer'), ST('Meeting', 'Small to large', ['lk', 'sa', 'ka'])];
const bookers = [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer, Goes by Howard.' } },
  { id: 'b2', fields: { Name: 'Jetrho Ty', Initials: 'JT', 'Slack User ID': 'U3', Info: 'Loc Engineer, Goes by Jetrho.' } },
  { id: 'b3', fields: { Name: 'Dylan Diaz', Initials: 'DD', 'Slack User ID': 'U0BQ77XKWA3', Info: 'Multimedia Specialist, Goes by Dilan, Dylan, DD.' } }];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });

(async () => {
  // ---- 1: the routes
  const route = async (action) => (await j1('Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)),
    payload: { type: 'block_actions', actions: [{ action_id: action }] } } }] })).route;
  for (const a of ['room_toggle', 'add_booth', 'add_holding', 'allday_toggle', 'purpose_pick', 'room_radio', 'note_toggle', 'repeat_toggle'])
    ok(await route(a) === 8, '1: ' + a + ' -> Note Toggle (room_toggle went to "other" on v19 / v20)');

  // ---- step 1 and its read
  const s1 = await j1('Build Step 1', [], { 'Check Signature': [chk], 'Read Cache': cacheRow });
  ok(s1.view.blocks.find(b => b.block_id === 'purpose').dispatch_action === true && !s1.view.blocks.some(b => b.block_id === 'allday_toggle'), '6: What\'s it for? redraws; no All day box yet');
  const s1b = await j1('Build Step 1', [], { 'Check Signature': [chk], 'Read Cache': cacheRow, 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify({ p: '__booth' }) }] } } }] });
  ok(s1b.view.blocks.findIndex(b => b.block_id === 'allday_toggle') === s1b.view.blocks.findIndex(b => b.block_id === 'purpose') + 1, '6: M booth already picked (typed) -> All day under it');
  const read1 = async (vals) => j1('Read Step 1', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }), state: { values: vals } } } } }] });
  const vals = (p, a, b, extra) => Object.assign({ date: { date_pick: { selected_date: '2027-10-19' } }, start: { start_pick: tv(a) }, end: { end_pick: tv(b) }, purpose: { purpose_pick: tv(p) } }, extra || {});
  let r1 = await read1(vals('QC', '13:00', '15:00'));
  ok(r1.s.kind === 'loc', '4: QC -> the Localization details');
  r1 = await read1(vals('Post Processing', '13:00', '15:00'));
  ok(r1.s.kind === 'post', '5: Post Processing -> its own kind');
  r1 = await read1({ date: { date_pick: { selected_date: '2027-10-19' } }, purpose: { purpose_pick: tv('__booth') }, allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } } });
  ok(r1.valid && r1.s.allDay === true && r1.s.t0 === '00:00' && r1.s.t1 === '23:59', '6: M booth all day -> valid with no Start / End');
  r1 = await read1({ date: { date_pick: { selected_date: '2027-10-19' } }, purpose: { purpose_pick: tv('VO Recording') }, allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } } });
  ok(!r1.valid && r1.answer.errors.start, '6: All day counts only for M booth (a stale tick with another purpose still needs times)');

  // ---- step 2 (Room Availability answers as RA v22 does: free_priority / free_last_resort / free_rooms / busy)
  const step2 = async (s, ra) => j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow });
  const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-19', t0: '13:00', t1: '15:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
  const V25 = JSON.stringify(si.nodes).indexOf('function onlyRoom(') !== -1;   // v25: the room list an actions block; booth / holding dropdowns
  const radio = v => { const b = v.blocks.find(b => b.block_id === 'room') || {}; return b.element || (b.elements || [])[0]; };
  const boothOf = v => v.blocks.find(b => /^booth(~\d+)?$/.test(b.block_id || ''));
  const metaOf = v => JSON.parse(v.private_metadata);

  // Celebrity Recording: studios only, + Holding room, + Vocal booth
  let v = (await step2(S('Celebrity Recording', 'studio'), { free_priority: ['Studio F', 'Likha', 'Katha', 'Salin', 'Studio C'], free_last_resort: ['Studio 7'], busy: ['Salin (TEAM SYNC)'] })).view;
  ok(radio(v).options.map(o => o.value).filter(x => x !== '__other').join() === 'Studio F,Studio C', '2: Celebrity Recording - the Room list is studios only (live: Likha, Katha, Salin as choices) - ' + radio(v).options.map(o => o.value));
  const ids = v.blocks.map(b => b.block_id).filter(Boolean);
  if (V25) { const hb = v.blocks.find(b => b.block_id === 'holding'), bb = boothOf(v);
    ok(ids.indexOf('add_holding') === -1 && ids.indexOf('add_booth') === -1 && hb && hb.element.type === 'multi_static_select' && hb.element.options.map(o => o.value).join() === 'Katha,Likha'
       && bb && bb.optional && bb.element.options.map(o => o.value).join() === (V39 ? 'Studio A,Studio B,Studio D,none' : V26 ? 'Studio A,Studio B,Studio D' : 'none,Studio A,Studio B,Studio D') && !bb.element.initial_option, '2 (v25): Holding rooms (Katha, Likha - Salin taken) and the Vocal booth as dropdowns, shown at once');
    ok(v.blocks.find(b => b.block_id === 'room').type === 'actions', '3 (v25): the list is an actions block - every pick redraws');
  } else {
  ok(ids.indexOf('add_holding') !== -1 && ids.indexOf('add_booth') > ids.indexOf('add_holding') && ids.indexOf('booth') === -1, '2: + Holding room, then + Vocal booth (unticked)');
  ok(metaOf(v).holds.join() === 'Katha,Likha' && metaOf(v).bx.pair['Studio F'].list.join() === 'Studio A,Studio B,Studio D', '2: free holding rooms (Salin taken) and booths in the form');
  ok(v.blocks.find(b => b.block_id === 'room').dispatch_action === true, '3: a studio change redraws (booth reset)'); }

  // Localization Dubbing: Studio + Booth, the usual pair first
  v = (await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio A', 'Studio B', 'Studio 2', 'Studio D', 'Studio 6'] })).view;
  const rb = v.blocks.find(b => b.block_id === 'room');
  ok((V25 ? v.blocks.find(b => b.block_id === 'room_label').text.text === (V26 ? '*Recommended studios:*' : '*Studio*') : rb.label.text === 'Studio') && radio(v).options.map(o => o.value).filter(x => x !== '__other').join() === 'Studio 1,Studio 2,Studio 6', '3: Localization Dubbing - Studio lists control rooms only (live: Studio A, B, D mixed in) - ' + radio(v).options.map(o => o.value));
  let bt = boothOf(v);
  if (V25) ok(bt && bt.element.initial_option.value === 'Studio A' && bt.element.options[0].text.text === 'Studio A (usual)' && !bt.hint && !bt.optional, '3 (v25): Vocal booth set to Studio 1\'s usual (Studio A), "(usual)", required');
  else ok(bt && bt.element.initial_option.value === 'Studio A' && /Studio 1’s usual booth/.test(bt.element.options[0].description.text) && /^Set to Studio 1’s usual booth/.test(bt.hint.text)
     && bt.element.options.slice(1).every(o => !o.description || /engineer patches it \(Dante\)/.test(o.description.text))   /* v22: no line */, '3: Booth set to Studio 1\'s usual (Studio A), the others "the engineer patches it (Dante)"');
  ok(!v.blocks.some(b => b.block_id === 'add_booth' || b.block_id === 'add_holding'), '3: no + Vocal booth when the booth is part of the session');
  // the usual booth taken
  v = (await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio B', 'Studio 2'], busy: ['Studio A (X)', 'Studio D (Y)'] })).view;
  bt = boothOf(v);
  ok(bt.element.options.map(o => o.value).join() === 'Studio B' && (V25 || /Studio 1’s usual booth \(Studio A\) is taken then/.test(bt.hint.text)), '3: usual booth taken -> said, the free one offered (v25: just the free one)');

  // QC: Localization details, M1 (an M booth in its ranking) never a Room choice
  v = (await step2(S('QC', 'loc'), { free_priority: ['Studio 3', 'Studio 5', 'Studio 7', 'M1'] })).view;
  ok(radio(v).options.map(o => o.value).filter(x => x !== '__other').join() === 'Studio 3,Studio 5,Studio 7' && v.blocks.some(b => b.block_id === 'code') && !v.blocks.some(b => b.block_id === 'client' || b.block_id === 'booth'),
     '4: QC - Project code + Engineer, no client, no booth');

  // Post Processing
  v = (await step2(S('Post Processing', 'post'), { free_priority: ['Studio E'] })).view;
  ok(radio(v).options.map(o => o.value).filter(x => x !== '__other').join() === 'Studio E' && (V33P ? !!v.blocks.find(b => b.block_id === 'forname') : V30 ? v.blocks.find(b => b.block_id === 'booker').element.action_id === 'booker_pick' : /\*Booker\*\nDylan Diaz/.test(v.blocks.find(b => b.block_id === 'booker').text.text))
     && v.blocks.find(b => b.block_id === 'project').label.text === 'Project title' && !v.blocks.some(b => ['client', 'engineer', 'arranger'].indexOf(b.block_id) !== -1),
     '5: Post Processing - Booker Dylan Diaz, Project title, no client / engineer');

  // VO Recording: + Vocal booth; Music Mixing: neither
  v = (await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio F'] })).view;
  ok((V25 ? !!boothOf(v) && boothOf(v).optional : v.blocks.some(b => b.block_id === 'add_booth')) && !v.blocks.some(b => b.block_id === 'add_holding' || b.block_id === 'holding'), '2: VO Recording - + Vocal booth only');
  const voMeta = v.private_metadata;
  v = (await step2(S('Music Mixing', 'studio'), { free_priority: ['Studio F'] })).view;
  ok(!v.blocks.some(b => b.block_id === 'add_booth' || b.block_id === 'add_holding' || b.block_id === 'holding' || /^booth/.test(b.block_id || '')) && (V25 || v.blocks.find(b => b.block_id === 'room').dispatch_action === undefined || radio(v).options.slice(-1)[0].value === '__other'), '2: Music Mixing - no extras (v22: the list redraws only for Another room…)');
  // M booth all day
  v = (await step2(S('', 'booth', { allDay: true, t0: '00:00', t1: '23:59' }), { free_rooms: ['M1', 'M2'] })).view;
  ok(/All day · M booth/.test(v.blocks[1].text.text), '6: step 2 says All day');

  // ---- Note Toggle: the redraws
  const toggle = async (view, action, extra, state) => j1('Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
    actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow });
  const celeb = (await step2(S('Celebrity Recording', 'studio'), { free_priority: ['Studio F', 'Likha', 'Katha', 'Salin', 'Studio C'] })).view;
  let t;
  if (!V25) {   // v25: no + Vocal booth / + Holding room boxes (sim-round-8)
  t = await toggle(celeb, 'add_booth', { selected_options: [{ value: 'booth' }] });
  let ix = t.view.blocks.map(b => b.block_id);
  bt = t.view.blocks.find(b => b.block_id === 'booth');
  ok(ix.indexOf('booth') === ix.indexOf('add_booth') + 1 && bt.element.initial_option.value === 'Studio A' && /Studio F records vocals in the room - add a booth only if the session needs one\./.test(bt.hint.text),
     '2: + Vocal booth ticked -> Booth under it, the in-room note for Studio F');
  t = await toggle(celeb, 'add_holding', { selected_options: [{ value: 'hold' }] });
  const hb = t.view.blocks.find(b => b.block_id === 'holding');
  ok(hb && hb.optional && hb.element.type === 'checkboxes' && hb.element.options.map(o => o.value).join() === 'Katha,Likha,Salin', '2: + Holding room ticked -> Holding rooms checklist (one or more)');
  t = await toggle(t.view, 'add_holding', { selected_options: [] });
  ok(!t.view.blocks.some(b => b.block_id === 'holding'), '2: unticked -> gone');
  }
  // a studio change resets the booth (Localization)
  const loc = (await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2', 'Studio 6', 'Studio A', 'Studio B', 'Studio D'] })).view;
  t = await toggle(loc, 'room_radio', { selected_option: { value: 'Studio 6' } }, { room: { room_radio: tv('Studio 6') }, booth: { booth_pick: tv('Studio A') } });
  bt = boothOf(t.view);
  ok(bt.element.initial_option.value === 'Studio D' && (V25 ? bt.element.options[0].text.text === 'Studio D (usual)' : /Set to Studio 6’s usual booth/.test(bt.hint.text)), '3: Studio 6 picked -> the booth resets to Studio D (D is paired with Studio 6)');
  t = await toggle(loc, 'room_radio', { selected_option: { value: 'Studio 2' } }, { room: { room_radio: tv('Studio 2') } });
  ok(boothOf(t.view).element.initial_option.value === 'Studio B', '3: Studio 2 -> Studio B');
  // Use another room: a dropdown with no option descriptions
  const mm = (await step2(S('Music Mixing', 'studio'), { free_priority: ['Studio F'] })).view;
  const V22 = !mm.blocks.some(b => b.block_id === 'room_toggle');   // v22: Another room… is a room choice
  t = V25 ? { view: mm } : V22 ? await toggle(mm, 'room_radio', { selected_option: { value: '__other' } }, { room: { room_radio: tv('__other') } }) : await toggle(mm, 'room_toggle', { selected_options: [{ value: 'room' }] });
  const ro = t.view.blocks.find(b => b.block_id === 'room_other');
  ok(ro && ro.element.type === 'static_select' && ro.element.options.length > 0 && ro.element.options.every(o => !o.description) && (V26 ? !ro.hint : /Not a usual room for Music Mixing/.test(ro.hint.text)) && (!V25 || ro.optional),
     '1: Use another room -> a dropdown Slack accepts (no option descriptions; v19 had them on every option)');
  // M booth all day in step 1
  t = await toggle(s1.view, 'purpose_pick', { selected_option: { value: '__booth' } }, { purpose: { purpose_pick: tv('__booth') } });
  ix = t.view.blocks.map(b => b.block_id);
  ok(ix.indexOf('allday_toggle') === ix.indexOf('purpose') + 1 && t.view.blocks.find(b => b.block_id === 'purpose').element.initial_option.value === '__booth', '6: M booth picked -> All day booking appears under it');
  const ad = await toggle(t.view, 'allday_toggle', { selected_options: [{ value: 'allday' }] }, { purpose: { purpose_pick: tv('__booth') } });
  ok(!ad.view.blocks.some(b => b.block_id === 'start' || b.block_id === 'end') && ad.view.blocks.find(b => b.block_id === 'allday_toggle').elements[0].initial_options, '6: All day ticked -> Start and End go');
  let un = await toggle(ad.view, 'allday_toggle', { selected_options: [] }, { purpose: { purpose_pick: tv('__booth') } });
  ix = un.view.blocks.map(b => b.block_id);
  ok(ix.indexOf('start') === ix.indexOf('date') + 1 && ix.indexOf('end') === ix.indexOf('start') + 1, '6: unticked -> Start and End back under the date');
  un = await toggle(ad.view, 'purpose_pick', { selected_option: { value: 'VO Recording' } }, { purpose: { purpose_pick: tv('VO Recording') } });
  ok(!un.view.blocks.some(b => b.block_id === 'allday_toggle') && un.view.blocks.some(b => b.block_id === 'start'), '6: another purpose -> the box goes, the times come back');

  // ---- Read Step 2: every room on the booking
  const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
  const M = (purpose, kind, extra) => Object.assign(S(purpose, kind), { when: 'Tuesday, Oct 19 · 1:00 PM–3:00 PM', label: purpose }, extra || {});
  let r2 = await read2({ room: { room_radio: tv('Studio F') }, booth: { booth_pick: tv('Studio A') }, holding: { holding_pick: { selected_options: [{ value: 'Likha' }, { value: 'Katha' }] } },
    project: { project_in: { value: 'celeb vo' } }, engineer: { engineer_pick: tv('U1') } }, M('Celebrity Recording', 'studio'));
  ok(r2.valid && r2.prep.rooms === 'Studio F, Studio A, Likha, Katha' && /^⏳ \*Booking Studio F \+ Studio A \+ Likha \+ Katha…\*/.test(r2.answer.view.blocks[0].text.text), '2: Studio F + booth + holding rooms on one booking - ' + r2.prep.rooms);
  r2 = await read2({ room: { room_radio: tv('Studio 1') }, booth: { booth_pick: tv('Studio B') }, code: { code_in: { value: 'NET-KUBA' } }, engineer: { engineer_pick: tv('U3') } }, M('Localization Dubbing', 'loc'));
  ok(r2.valid && r2.prep.rooms === 'Studio 1, Studio B' && r2.calTitle === 'NET-KUBA / JT', '3: Localization Dubbing -> Studio 1, Studio B · NET-KUBA / JT');
  r2 = await read2({ room: { room_radio: tv('Studio 3') }, code: { code_in: { value: 'NET-KUBA' } }, engineer: { engineer_pick: tv('U3') } }, M('QC', 'loc'));
  ok(r2.valid && r2.calTitle === 'NET-KUBA / JT' && r2.prep.client === '', '4: QC -> NET-KUBA / JT, no client');
  r2 = await read2({ room: { room_radio: tv('Studio E') }, project: { project_in: { value: 'brand reel' } } }, M('Post Processing', 'post'));
  ok(r2.valid && r2.calTitle === 'BRAND REEL / DD' && r2.prep.engineer === 'Dylan Diaz' && r2.team === '' && /no client/.test(r2.prep.requester_text), '5: Post Processing -> BRAND REEL / DD, booked under Dylan Diaz, no notice - ' + r2.calTitle);
  r2 = await read2({ room: { room_radio: tv('M2') }, forname: { forname_in: { value: 'Howard' } } }, M('', 'booth', { allDay: true, t0: '00:00', t1: '23:59', when: 'Tuesday, Oct 19 · All day', label: 'M booth' }));
  ok(r2.valid && r2.prep.all_day === true && r2.prep.start_iso === '2027-10-19T00:00:00+08:00' && r2.prep.end_iso === '2027-10-20T00:00:00+08:00' && /all day/.test(r2.prep.requester_text), '6: M2 all day -> 00:00 to the next 00:00, all_day');
  r2 = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } }, M('VO Recording', 'studio'));
  ok(r2.prep.rooms === 'Studio 7' && r2.prep.all_day === false, 'a plain booking unchanged');

  // ---- the cards and the rows
  const ab = await j1('After Book', [{ json: { status: 'CREATED', event_id: 'ev1', title: 'CELEB VO / HL' } }], { 'Read Step 2': [{ json: { s: S('Celebrity Recording', 'studio', { when: 'Tuesday, Oct 19 · 1:00 PM–3:00 PM' }), room: 'Studio F', rooms: 'Studio F, Studio A, Likha', viewId: 'V1', channel: 'D1' } }],
    'After Prepare': [{ json: { F: { Room: 'Studio F, Studio A, Likha', Date: 'Tuesday, October 19', Time: '1:00 PM – 3:00 PM' }, book: { start_iso: '2027-10-19T13:00:00+08:00', end_iso: '2027-10-19T15:00:00+08:00' } } }] });
  const txt = JSON.stringify(ab);
  ok(/\*Room:\* Studio F \+ Studio A\\n\*Holding room:\* Likha/.test(txt), '2: the Booked card - Room: Studio F + Studio A, Holding room: Likha (prototype 76)');
  // a row in My bookings and the Change form keep every room
  const mw = jsOf('Render My Bookings');
  ok(/function roomMain/.test(mw) && /roomMain\(b\.r\)/.test(mw), 'rows show Studio F + Studio A + Likha');
  const tm = jsOf('To Move');
  ok(/\[R\.n\.r\]\.concat\(roomExtras\(R\.b\.r\)\)/.test(tm), '3: Change to another studio keeps the booth and holding rooms');
  ok(/roomName\(String\(x \|\| ''\)\.split\(','\)\[0\]\)/.test(jsOf('Build Change')), '3: the Change form reads the studio of a multi-room booking (it offered no rooms)');

  // ---- every rendered view: no option description in a dropdown (gotcha: Slack refuses the whole view)
  const views = [s1.view, s1b.view, celeb, loc, mm, voMeta && (await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'] })).view];
  let bad = 0;
  const walk = x => { if (!x || typeof x !== 'object') return; if (x.type === 'static_select' || x.type === 'overflow') for (const o of [].concat(x.options || [], ...((x.option_groups || []).map(g => g.options || [])))) if (o.description) bad++;
    for (const k of Object.keys(x)) walk(x[k]); };
  views.concat([t.view, ad.view, un.view]).forEach(walk);
  ok(bad === 0, 'no dropdown option carries a description (' + bad + ')');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
