#!/usr/bin/env node
// Round 8 offline (Slack Interactions v25 + main v275, 19 Oct, docs/design/round-8-plan.md): the room picker (either / or),
// booth and holding dropdowns, Atmos -> Studio C, Van Recording -> Studio M (and Studio M for nothing else), events / meetings in
// studios, the typed project code, the M booth name, capitals, placeholders, fewer words, the form's details on the message.
// Usage: node scripts/sim-round-8.js [slack-interactions v25] [main v275] [book-session v112]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v25.json', 'utf8'));
const V39 = JSON.stringify(si.nodes).indexOf('a phone shows no') !== -1;   // v39: "No booth / engineer / arranger" back, last (phones cannot clear a pick)
// v53 (28 Oct): the Vocal booth(s) is a multi-select - no "No booth" item; the picked booths read the same on either shape
const V53 = JSON.stringify(si.nodes).indexOf("label: pt('Vocal booths')") !== -1;
const bPick = bl => (bl && bl.element ? [].concat(bl.element.initial_options || (bl.element.initial_option ? [bl.element.initial_option] : [])) : []).map(o => o.value).filter(x => x !== 'none');
const main = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/project-jessie-v275.json', 'utf8'));
// v40 / v280 (22 Oct): the summary on separate lines - read back as the one " · " line these checks were written for
const one40 = s => String(s).replace(/🗓️ \*([^*\n]+)\*((?:\n\*[^*\n]+\*)+)/g, (m, a, b) => '🗓️ *' + [a].concat(b.split('\n').filter(Boolean).map(x => x.slice(1, -1))).join(' · ') + '*');
const V26 = /function roomAllowed\(/.test(JSON.stringify(si.nodes));   // round 9: labels, no descriptions / hints, no "No …" options (sim-round-9)
const V30 = /function pairBlocksC\(/.test(JSON.stringify(si.nodes));   // round 12: Booker dropdown, code without Enter (sim-round-12)
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
const m1 = async (...a) => (await runIn(main, ...a))[0].json;

// reference data: the 15 Oct rooms + Studio M (the van); Atmos Mixing, Van Recording, Event; people with departments
const rooms = FX.rooms.concat([{ id: 'sm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Van'], 'Recording Format': ['Stereo'] } }]);
const ST = (t, pri, roles, req) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': req || '' } });
const sessionTypes = FX.sessionTypes.filter(s => !/^Meeting$/.test(s.fields.Type)).concat([
  ST('Atmos Mixing', ['rc'], ['Loc Engineer', 'Post Engineer', 'Music Engineer'], 'Large'), ST('Localization Atmos Mixing', ['rc'], ['Loc Engineer'], 'Large'),
  ST('Van Recording', ['sm'], ['Post Engineer', 'Music Arranger']), ST('Meeting', ['lk', 'sa', 'ka'], ['None']), ST('Event', ['lo'], ['None'])]);
const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: dept } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.', ['Audio Post']), B('b2', 'Jetrho Ty', 'JT', 'U3', 'Loc Engineer, Goes by Jetrho.', ['Localization']),
  B('b3', 'Vianne Cruz', 'VC', 'U4', 'Loc Engineer, Goes by Via.', ['Localization']), B('b4', 'Joaquin Santos', 'JS', 'U9', 'Music Arranger, Goes by Joaquin.', ['Music']),
  B('b5', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer, Post Engineer. Goes by Daryl, Drey.', ['Music']), B('b7', 'Dylan Diaz', 'DD', 'U0BQ77XKWA3', 'Multimedia Specialist', ['Marketing'])];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const LOC = [{ json: { id: 'p1', 'Project Code': 'NET-MALAS', 'Project Title': 'BAD DAY', 'Client Name': 'NETFLIX', Recordist: ['Jetrho'], Mixer: ['Via'] } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-20', t0: '16:00', t1: '18:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }],
  { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': LOC })).view;
const blk = (v, id) => v.blocks.find(b => b.block_id === id);
const blkRe = (v, re) => v.blocks.find(b => re.test(b.block_id || ''));
const ids = v => v.blocks.map(b => b.block_id).filter(Boolean);
const radioOf = v => { const b = blkRe(v, /^room(~\d+)?$/); return b && (b.element || (b.elements || [])[0]); };
const toggle = async (view, action, extra, state) => j1('Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
  actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow, 'Loc Projects 9': LOC });
const read2 = async (vv, meta, blocks) => j1('Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission',
  view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: blocks || [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
const M = (purpose, kind, extra) => Object.assign(S(purpose, kind), { when: 'Wednesday, Oct 20 · 4:00 PM–6:00 PM', label: purpose }, extra || {});
const views = [];

(async () => {
  console.log('Step 1');
  const s1 = (await j1('Build Step 1', [], { 'Check Signature': [chk], 'Read Cache': cacheRow })).view;
  views.push(s1);
  const pur = blk(s1, 'purpose');
  ok(s1.blocks[0].elements[0].text === '*Step 1 of 2*', '5: "Step 1 of 2" alone');
  ok(pur.hint.text === 'You’ll get a recommendation based on the booking details.' && pur.element.placeholder.text === 'Select a booking type', '3 / 14: the hint and "Select a booking type"');
  ok(blk(s1, 'start').element.placeholder.text === 'Select a start time' && blk(s1, 'end').element.placeholder.text === 'Select an end time' && blk(s1, 'date').element.placeholder.text === 'Select a date', '15: Select a start time / an end time / a date');
  const rep = await toggle(s1, 'repeat_toggle', { selected_options: [{ value: 'rep' }] }, { date: { date_pick: { selected_date: '2027-10-20' } } });
  ok(!blk(rep.view, 'rep_days').hint && blk(rep.view, 'rep_note').elements[0].text === 'Up to 16 dates.' && blk(rep.view, 'rep_freq').element.placeholder.text === 'Select how often'
     && blk(rep.view, 'rep_count').element.placeholder.text === 'Select a number' && blk(rep.view, 'rep_until').hint.text === 'Only applies if "How many times" is empty.', '8a / 8b / 15: Repeats - no "For every week…", "Up to 16 dates.", Select … ; "Or until" keeps its hint');
  views.push(rep.view);

  console.log('Step 2 - the room picker (10)');
  let v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio 8'], busy: [] });
  views.push(v);
  ok(v.blocks[0].elements[0].text === '*Step 2 of 2*', '5: "Step 2 of 2" alone');
  ok(blk(v, 'room').type === 'actions' && blk(v, 'room_label').text.text === (V26 ? '*Recommended rooms:*' : '*Room*') && radioOf(v).options.map(o => o.value).join() === 'Studio 7,Studio 8' && radioOf(v).initial_option.value === 'Studio 7',
     '10: the recommended rooms (no "Another room…" choice), the first ticked');
  ok((V26 ? !radioOf(v).options[0].description : radioOf(v).options[0].description.text === 'Recommended') && !radioOf(v).options[1].description, '8: "Recommended" (was "Recommended · usual for VO Recording")');
  const ro = blk(v, 'room_other');
  ok(ro && ro.type === 'input' && ro.optional && ro.dispatch_action && ro.element.placeholder.text === 'Select a room' && (V26 ? !ro.hint && ro.label.text === 'Choose a different room' : ro.hint.text === 'Not a usual room for VO Recording.')
     && ids(v).indexOf('room_other') > ids(v).indexOf('room') && !ro.element.options.some(o => /^(Studio M|Studio [ABD]|M\d|Likha|Lobby)$/.test(o.value)), '10: Another room right under them, at once; studios only, never Studio M');
  // pick from Another room -> the ticked room is cleared; pick a room -> Another room is cleared
  let t = await toggle(v, 'room_other_pick', { selected_option: { value: 'Studio 5' } }, { room: { room_radio: tv('Studio 7') }, room_other: { room_other_pick: tv('Studio 5') } });
  const rb2 = blkRe(t.view, /^room~\d+$/);
  ok(rb2 && !rb2.elements[0].initial_option && !blk(t.view, 'room') && blk(t.view, 'room_other').element.initial_option.value === 'Studio 5', '10: Another room picked -> the ticked room cleared (a new block, so Slack forgets it)');
  views.push(t.view);
  t = await toggle(t.view, 'room_radio', { selected_option: { value: 'Studio 8' } }, { [rb2.block_id]: { room_radio: tv('Studio 8') }, room_other: { room_other_pick: tv('Studio 5') } });
  const ro2 = blkRe(t.view, /^room_other~\d+$/);
  ok(ro2 && !ro2.element.initial_option && radioOf(t.view).initial_option && radioOf(t.view).initial_option.value === 'Studio 8', '10: a room ticked again -> Another room cleared, the room kept');
  // the route
  const route = async (payload) => (await j1('Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  for (const a of ['room_other_pick', 'code_in', 'det_code_in', 'room_radio']) ok(await route({ type: 'block_actions', actions: [{ action_id: a }] }) === 8, 'route: ' + a + ' -> the redraw');
  // Read Step 2 finds the room under any block id
  const meta = JSON.parse(v.private_metadata);
  let r = await read2({ 'room~5': { room_radio: tv('Studio 8') }, project: { project_in: { value: 'orange' } }, engineer: { engineer_pick: tv('U1') } }, meta);
  ok(r.valid && r.room === 'Studio 8' && !r.prep.room_override, '10: the ticked room read under a new block id');
  r = await read2({ 'room~5': { room_radio: {} }, room_other: { room_other_pick: tv('Studio 5') }, project: { project_in: { value: 'orange' } }, engineer: { engineer_pick: tv('U1') } }, meta);
  ok(r.valid && r.room === 'Studio 5' && r.prep.room_override === true, '10: Another room -> booked as asked');
  r = await read2({ project: { project_in: { value: 'orange' } }, engineer: { engineer_pick: tv('U1') } }, meta, v.blocks);
  ok(!r.valid && r.answer.errors.room_other === 'Pick a room.', '10: neither -> "Pick a room." on Another room (the list is not an input)');

  console.log('Booth and holding rooms (21)');
  v = await step2(S('Celebrity Recording', 'studio'), { free_priority: ['Studio F', 'Likha', 'Katha', 'Salin', 'Studio C'], busy: ['Salin (TEAM)'] });
  views.push(v);
  let bt = blkRe(v, /^booth~\d+$/), hb = blk(v, 'holding');
  ok(bt && bt.label.text === (V53 ? 'Vocal booths' : 'Vocal booth') && bt.optional && bt.element.type === (V53 ? 'multi_static_select' : 'static_select') && (V26 ? (V39 && !V53 ? bt.element.options.slice(-1)[0].value === 'none' : !bt.element.options.some(o => o.value === 'none')) && bt.element.placeholder.text === 'No booth' : bt.element.options[0].value === 'none' && bt.element.placeholder.text === 'Select a booth') && !bPick(bt).length && !bt.hint, '21: Celebrity Recording (records in the room) - Vocal booth, optional, "No booth", nothing picked, no hint');
  ok(hb && hb.element.type === 'multi_static_select' && hb.optional && hb.element.options.map(o => o.value).join() === 'Katha,Likha' && hb.element.placeholder.text === 'Select holding rooms',
     '21: Holding rooms - a dropdown, several can be picked (Salin taken)');
  ok(!blk(v, 'add_booth') && !blk(v, 'add_holding'), '21: no tick boxes');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2', 'Studio A', 'Studio B'] });
  bt = blkRe(v, /^booth~\d+$/);
  ok(!bt.optional && bPick(bt).join() === 'Studio A' && bt.element.options[0].text.text === 'Studio A (usual)' && bt.element.options[0].value === 'Studio A'
     && !bt.element.options.some(o => o.value === 'none'), '21: Localization Dubbing (a booth is needed) - set to the usual one, "Studio A (usual)", required');
  t = await toggle(v, 'room_radio', { selected_option: { value: 'Studio 2' } }, { room: { room_radio: tv('Studio 2') } });
  bt = blkRe(t.view, /^booth~\d+$/);
  ok(bt && bPick(bt).join() === 'Studio B' && bt.element.options[0].text.text === 'Studio B (usual)', '21: Studio 2 ticked -> the booth follows (Studio B, its usual)');
  views.push(v, t.view);
  r = await read2({ room: { room_radio: tv('Studio F') }, 'booth~1': { booth_pick: tv('none') }, holding: { holding_pick: { selected_options: [{ value: 'Likha' }, { value: 'Katha' }] } },
    project: { project_in: { value: 'celeb' } }, engineer: { engineer_pick: tv('U1') } }, M('Celebrity Recording', 'studio'));
  ok(r.valid && r.prep.rooms === 'Studio F, Likha, Katha', '21: "No booth" -> no booth; the holding rooms on the booking - ' + r.prep.rooms);
  r = await read2({ room: { room_radio: tv('Studio F') }, 'booth~1': { booth_pick: tv('Studio A') }, project: { project_in: { value: 'celeb' } }, engineer: { engineer_pick: tv('U1') } }, M('Celebrity Recording', 'studio'));
  ok(r.valid && r.prep.rooms === 'Studio F, Studio A', '21: a booth picked -> on the booking');

  console.log('Meetings, events, M booths (9, 13, 20, 22)');
  v = await step2(S('Meeting', 'meeting'), { free_priority: ['Likha', 'Salin'] });
  views.push(v);
  ok(!blk(v, 'forwho_toggle') && blk(v, 'department') && !blk(v, 'department').hint && blk(v, 'department').element.placeholder.text === 'Select a department', '9 / 4: Meeting - no "for someone else", Department without a hint');
  const mo = blk(v, 'room_other').element.options.map(o => o.value);
  ok(mo.indexOf('Studio F') !== -1 && mo.indexOf('Studio C') !== -1 && mo.indexOf('Katha') !== -1 && mo.indexOf('Studio M') === -1 && mo.indexOf('M1') === -1 && mo.indexOf('Studio A') === -1
     && (V26 ? !blk(v, 'room_other').hint : blk(v, 'room_other').hint.text === 'Not a usual room for meetings.'), '22: a meeting\'s Another room lists the free studios too (never Studio M, booths) - "Not a usual room for meetings."');
  v = await step2(S('Event', 'meeting'), { free_priority: ['Lobby'] });
  views.push(v);
  ok(!blk(v, 'forwho_toggle') && !blk(v, 'department') && radioOf(v).initial_option.value === 'Lobby' && blk(v, 'room_other').element.options.some(o => o.value === 'Studio 7'), '9 / 22: Event - title only, Lobby recommended, studios under Another room');
  r = await read2({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'post weekly meeting' } }, department: { department_pick: tv('Audio Post') } }, M('Meeting', 'meeting'));
  ok(r.valid && r.calTitle === 'LIKHA - Post weekly meeting', '13: "post weekly meeting" -> "LIKHA - Post weekly meeting"');
  r = await read2({ room_other: { room_other_pick: tv('Studio F') }, title: { title_in: { value: 'launch party' } } }, Object.assign(M('Event', 'meeting'), { others: ['Studio F'] }));
  ok(r.valid && r.calTitle === 'STUDIO F - Launch party' && r.prep.room_override === true, '22: an event in Studio F -> "STUDIO F - Launch party", booked as asked');
  v = await step2(S('', 'booth'), { free_rooms: ['M1', 'M2'] });
  views.push(v);
  ok(blk(v, 'forname') && blk(v, 'forname').label.text === 'Who is it for?' && blk(v, 'forname').element.initial_value === 'Howard' && !blk(v, 'forwho_toggle'), '20: M booth - "Who is it for?" filled in with the booker\'s first name');
  const BM = M('', 'booth', { label: 'M booth' });
  r = await read2({ room: { room_radio: tv('M2') }, forname: { forname_in: { value: 'joaquin' } } }, BM);
  ok(r.valid && r.calTitle === 'M2 - Joaquin' && r.forId === 'U9' && /Booked by: Howard Luistro \(for Joaquin Santos\)/.test(r.prep.description) && r.team === 'U9', '20: "joaquin" -> "M2 - Joaquin", Joaquin on the booking and told');
  r = await read2({ room: { room_radio: tv('M2') }, forname: { forname_in: { value: 'Peemo' } } }, BM);
  ok(r.valid && r.calTitle === 'M2 - Peemo' && !r.forId && !/\(for /.test(r.prep.description), '20: a name not in Bookers -> the title only');
  r = await read2({ room: { room_radio: tv('M2') }, forname: { forname_in: { value: 'Howard' } } }, BM);
  ok(r.valid && r.calTitle === 'M2 - Howard' && !r.forId, '20: the booker\'s own name -> just theirs');
  r = await read2({ room: { room_radio: tv('M2') }, forname: { forname_in: { value: '' } } }, BM);
  ok(!r.valid && r.answer.errors.forname === 'Who is it for?', '20: empty -> "Who is it for?"');

  console.log('Atmos -> Studio C, Van Recording -> Studio M (18, 23)');
  v = await step2(S('Atmos Mixing', 'atmos'), { free_priority: ['Studio C'], busy: [] });
  views.push(v);
  ok(radioOf(v).options.map(o => o.value).join() === 'Studio C' && !blk(v, 'room_other') && blk(v, 'project').label.text === 'Project title or code' && blk(v, 'engineer') && !blk(v, 'client') && !blk(v, 'arranger')
     && !blkRe(v, /^booth/), '18: Atmos Mixing - Studio C only (no Another room); Project title or code + Engineer; no client, arranger, booth');
  v = await step2(S('Atmos Mixing', 'atmos'), { free_priority: [], busy: ['Studio C (X)'] });
  ok(!v.submit && /Studio C is taken then - pick another date or time\./.test(JSON.stringify(v.blocks)), '18: Studio C taken -> "Studio C is taken then - pick another date or time.", no Book');
  v = await step2(S('Localization Atmos Mixing', 'atmos'), { free_priority: ['Studio C'] });
  ok(radioOf(v).options.map(o => o.value).join() === 'Studio C' && blk(v, 'project'), '18: the old name (Localization Atmos Mixing) is Atmos too');
  r = await read2({ room: { room_radio: tv('Studio C') }, project: { project_in: { value: 'net-cam' } }, engineer: { engineer_pick: tv('U1') } }, M('Atmos Mixing', 'atmos'));
  ok(r.valid && r.calTitle === 'NET-CAM / HL' && r.prep.client === '' && /no client/.test(r.prep.requester_text) && r.prep.session_type === 'Atmos Mixing', '18: "net-cam" -> NET-CAM / HL, no client');
  v = await step2(S('Van Recording', 'studio'), { free_priority: ['Studio M'] });
  views.push(v);
  ok(radioOf(v).options.map(o => o.value).join() === 'Studio M' && !blk(v, 'room_other') && blk(v, 'project').label.text === 'Project title' && blk(v, 'client') && blk(v, 'client').optional
     && (V26 ? !blk(v, 'team_note') : /pick one or both/.test(blk(v, 'team_note').elements[0].text)) && blk(v, 'engineer').optional && blk(v, 'arranger').optional && !blkRe(v, /^booth/), '23: Van Recording - Studio M only; Project title, Client (optional), engineer and / or arranger');
  v = await step2(S('Van Recording', 'studio'), { free_priority: [], busy: ['Studio M (X)'] });
  ok(!v.submit && /Studio M is taken then - pick another date or time\./.test(JSON.stringify(v.blocks)), '23: Studio M taken -> "pick another date or time"');
  v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'], free_last_resort: ['Studio M'], busy: [] });
  ok(radioOf(v).options.every(o => o.value !== 'Studio M') && blk(v, 'room_other').element.options.every(o => o.value !== 'Studio M'), '23: Studio M never offered for anything else');
  r = await read2({ room: { room_radio: tv('Studio M') }, project: { project_in: { value: 'van shoot' } }, client: { client_in: { value: 'acme' } }, arranger: { arranger_pick: tv('U9') } }, M('Van Recording', 'studio'));
  ok(r.valid && r.calTitle === 'VAN SHOOT / Acme / JS' && /no engineer/.test(r.prep.requester_text), '23: Van Recording with an arranger only -> VAN SHOOT / Acme / JS');
  r = await read2({ room: { room_radio: tv('Studio M') }, project: { project_in: { value: 'van shoot' } }, engineer: { engineer_pick: tv('U1') } }, M('Van Recording', 'studio'));
  ok(r.valid && /no arranger/.test(r.prep.requester_text), '8: an arranger field left empty -> "no arranger" (Book Session never asks)');

  console.log('Localization project code (19)');
  v = await step2(S('Localization Dubbing', 'loc', { pre: { cd: 'net-malas' } }), { free_priority: ['Studio 1'] });
  const cb = blk(v, 'code');
  ok(cb.element.type === 'plain_text_input' && cb.element.action_id === 'code_in' && (V30 ? !cb.dispatch_action && !cb.element.dispatch_action_config : cb.dispatch_action && cb.element.dispatch_action_config.trigger_actions_on[0] === 'on_enter_pressed')
     && cb.element.initial_value === 'NET-MALAS' && !cb.hint, '19: a text box (Enter looks it up), the typed code in capitals, no hint');
  ok(/\*BAD DAY\* · NETFLIX/.test(blk(v, 'code_info').elements[0].text) && blk(v, 'engineer').element.initial_option.value === 'U3' && !blk(v, 'engineer').hint, '19: a known code -> the project, the Recordist set, no hint');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1'] });
  t = await toggle(v, 'code_in', { value: 'net-malas' }, { code: { code_in: { value: 'net-malas' } } });
  ok(/\*BAD DAY\*/.test(blk(t.view, 'code_info').elements[0].text) && blk(t.view, 'engineer').element.initial_option.value === 'U3' && blk(t.view, 'code').element.initial_value === 'net-malas', '19: Enter on a known code -> the project shown, the engineer set, the box kept');
  t = await toggle(t.view, 'code_in', { value: 'OLD-SHOW' }, { code: { code_in: { value: 'OLD-SHOW' } } });
  ok(!blk(t.view, 'code_info') && !/New project code/.test(JSON.stringify(t.view)), '19: a code not in Airtable -> nothing shown (it may be an old one)');
  r = await read2({ room: { room_radio: tv('Studio 1') }, 'booth~1': { booth_pick: tv('Studio A') }, code: { code_in: { value: 'old-show' } }, engineer: { engineer_pick: tv('U3') } }, M('Localization Dubbing', 'loc'));
  ok(r.valid && r.calTitle === 'OLD-SHOW / JT', '19: any code books as typed, in capitals - OLD-SHOW / JT');

  console.log('Text boxes, hints, placeholders (4, 8, 14, 15)');
  const allViews = views.concat([await step2(S('Music Mixing', 'studio'), { free_priority: ['Studio F'] })]);
  let selects = 0, badPh = [], inputs = 0, badIn = [], descs = 0;
  const walk = x => { if (!x || typeof x !== 'object') return;
    if (/^(static_select|multi_static_select|external_select)$/.test(x.type)) { selects++; if (!x.placeholder || !(V26 ? /^(Select|Type or select|No (?:booth|engineer|arranger)$)/ : /^(Select|Type or select)/).test(x.placeholder.text)) badPh.push(x.action_id + ':' + (x.placeholder && x.placeholder.text));
      for (const o of [].concat(x.options || [], ...((x.option_groups || []).map(g => g.options || [])))) if (o.description) descs++; }
    if (x.type === 'plain_text_input') { inputs++; if (!x.placeholder || x.placeholder.text !== '⠀') badIn.push(x.action_id); }
    for (const k of Object.keys(x)) walk(x[k]); };
  allViews.forEach(walk);
  ok(selects > 10 && !badPh.length, '14 / 15: every dropdown says "Select …" (' + selects + ')', badPh);
  ok(inputs > 5 && !badIn.length, '4: every text box blank (an invisible placeholder - no "Write something", no "Anything the session needs") (' + inputs + ')', badIn);
  ok(descs === 0, 'no dropdown option carries a description');
  const allText = JSON.stringify(allViews);
  ok(!/Leave empty if there|Set to you\.|As you typed it|Only engineers are listed|Set to yours|Which team is the meeting for|For every week|Each one is checked|From the project|Type to search|booked as asked|Anything the session needs/.test(allText),
     '4 / 8: none of the removed hints');

  console.log('Working lines and the message (2, 6, 17)');
  r = await read2({ room: { room_radio: tv('Studio 6') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } }, M('VO Recording', 'studio', { msg: { ch: 'D1', ts: '50.5' } }));
  ok(r.answer.view.blocks[0].text.text === '⏳ *Booking Studio 6…*\nWednesday, October 20' + (V26 ? ', 2027' : '') + '\n4:00 PM – 6:00 PM' && r.answer.view.blocks[1].elements[0].text.replace(/^Usually under \d+ (?:seconds|minutes?)\. /, '') === ('You can close this window – we’ll let you know ' + (/in your DM once/.test(JSON.stringify(si.nodes)) ? 'in your DM ' : '') + 'once it’s done.'),
     '6 / 2: Booking… - the date, then the time; the close line, no "being processed"');
  const menuMsg = { ts: '50.5', text: 'Hi', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Hi, I’m Jessie!' } }, { type: 'actions', elements: [{ action_id: 'open_book', value: 'menu' }, { action_id: 'my_bookings', value: 'menu' }] }] };
  const offerMsg = { ts: '50.5', text: 'so far', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Your booking details so far:\n🗓️ *Studio 7 · Wednesday, October 20 · 4:00 PM – 6:00 PM*' } },
    { type: 'actions', elements: [{ action_id: 'open_book', value: '{"r":"Studio 7"}' }, { action_id: 'my_bookings', value: 'menu' }] }] };
  let MS = await j1('Mark Source', [{ json: { ok: true, messages: [menuMsg] } }], { 'Read Step 2': [{ json: r }] });
  ok(MS.ok && one40(MS.blocks[0].text.text) === 'Your booking details:\n🗓️ *Studio 6 · Wednesday, October 20' + (V26 ? ', 2027' : '') + ' · 4:00 PM – 6:00 PM*' && MS.blocks[1].elements[0].text === '⏳ Booking…' && MS.blocks.length === 2,
     '17: opened from the menu -> "Your booking details:" and the form\'s room · date · time, "⏳ Booking…"');
  let SD = await runIn(si, 'Source Done', [], { 'Mark Source': [{ json: MS }], 'After Book': [{ json: { ok: true } }] });
  ok(SD[0].json.blocks === MS.original, '17: the menu gets its buttons back after booking (the Booked card is its own message)');
  MS = await j1('Mark Source', [{ json: { ok: true, messages: [offerMsg] } }], { 'Read Step 2': [{ json: r }] });
  SD = await runIn(si, 'Source Done', [], { 'Mark Source': [{ json: MS }], 'After Book': [{ json: { ok: true } }] });
  ok(/Studio 6 · Wednesday/.test(one40(MS.blocks[0].text.text)) && SD[0].json.blocks[0].text.text === MS.blocks[0].text.text && SD[0].json.blocks[1].elements[0].text === '✅ Booked.',
     '17: a typed offer changed on the form (Studio 7 -> 6) -> the form\'s details, then "✅ Booked."');
  const MSS = await j1('Mark Source Series', [{ json: { ok: true, messages: [menuMsg] } }], { 'Read Series Confirm': [{ json: { meta: { msg: { ch: 'D1', ts: '50.5' }, n: 3, time: '14:00-16:00', rooms: 'Studio 6, Studio A' } } }] });
  ok(one40(MSS.blocks[0].text.text) === 'Your booking details:\n🗓️ *Studio 6 + Studio A · 3 dates · 2:00 PM – 4:00 PM*' && MSS.blocks[1].elements[0].text === '⏳ Booking…', '17: a series - rooms · N dates · time, "⏳ Booking…"');
  const aps = await j1('After Prepare Series', [{ json: { status: 'PREPARED', card_text: '*X*', title: 'X', dates: ['2027-10-20', '2027-10-27'], prep_key: 'k', prep_stored: true } }],
    { 'Read Step 2': [{ json: Object.assign({}, r, { s: Object.assign({}, r.s, { series: { dates: ['2027-10-20', '2027-10-27'] } }) }) }], 'Read Request': [{ json: { payload: { view: {} } } }] });
  ok(JSON.parse(aps.view.private_metadata).rooms === 'Studio 6', '17: the series check screen carries the rooms');

  console.log('The booking call: the prepare run\'s lookups (speed)');
  const ap = await j1('After Prepare', [{ json: { status: 'PREPARED', prep_payload: JSON.stringify({ F: { Title: 'X / HL', Room: 'Studio 6', Date: 'Wednesday, October 20, 2027', Time: '4:00 PM – 6:00 PM' } }), client_cache: '{"v":1}' } }],
    { 'Read Step 2': [{ json: r }], 'To Prepare': [{ json: r.prep }], 'Read Request': [{ json: { payload: { view: {} } } }] });
  ok(ap.go && ap.book.client_cache === '{"v":1}' && ap.book.confirmed === true, 'the booking call carries client_cache from the prepare run (Book Session v112 skips the lookups)');

  console.log('Problems in fewer words (8)');
  const prob = async (res) => (await j1('After Book', [{ json: res }], { 'Read Step 2': [{ json: r }], 'After Prepare': [{ json: { book: {}, F: {} } }], 'Read Request': [{ json: { payload: { view: { blocks: [], state: { values: {} } } } } }] }));
  let pb = await prob({ status: 'REJECTED', reason: 'ROOM_UNSUITABLE', human: 'Atmos Mixing can only be booked in Studio C. Nothing was booked.' });
  ok(/⚠️ Atmos Mixing can only be booked in Studio C\./.test(JSON.stringify(pb)) && !/Nothing was booked/.test(JSON.stringify(pb)), '18: Book Session\'s single-room refusal, in its own words');
  pb = await prob({ status: 'ROOM_DECLINED', declined: ['KDC Plaza-Top Level-Studio 7 (7)'], removed: true });
  ok(/\*Studio 7\* is already taken then - nothing was booked\./.test(JSON.stringify(pb)), '8: the room declined -> "*Studio 7* is already taken then - nothing was booked."');
  pb = await prob({ status: 'REJECTED', reason: 'NEED_DEPARTMENT', options: ['Music', 'Advertising'] });
  ok(/Which department is this booking for\?/.test(JSON.stringify(pb)), '8: "booking", not "session"');

  console.log('The Change form');
  const buildChange = async (b) => (await j1('Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
  let cv = await buildChange({ id: 'ev1', d: '2027-10-20', s: '16:00', e: '18:00', r: 'Studio 8', t: 'PURPLE YAM / Jem Lim / HL', st: 'VO Recording' });
  ok(blk(cv, 'purpose_c').element.placeholder.text === 'Select a booking type' && !blk(cv, 'purpose_c').hint && blk(cv, 'det_notes').element.placeholder.text === '⠀', '8e / 14: Change - "Select a booking type", no hint; the Note blank');
  cv = await buildChange({ id: 'ev2', d: '2027-10-20', s: '16:00', e: '18:00', r: 'Likha (Big Room)', t: 'LIKHA - weekly sync', st: 'Meeting' });
  const rp = blk(cv, 'room').element.options.map(o => o.value);
  ok(rp[0] === 'Likha' && rp.indexOf('Studio F') !== -1 && rp.indexOf('Studio M') === -1 && rp.indexOf('M1') === -1, '22: a meeting can move to a studio - never Studio M');
  const rcv = async (m, vals) => j1('Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(m), state: { values: vals } } } } }], 'Read Cache 10': cacheRow });
  const base = { date: { date_pick: { selected_date: '2027-10-20' } }, start: { start_pick: tv('16:00') }, end: { end_pick: tv('18:00') } };
  let rc = await rcv(JSON.parse(cv.private_metadata), Object.assign({}, base, { room: { room_pick: tv('Likha') }, purpose_c: { purpose_c: tv('Meeting') }, det_title: { det_title_in: { value: 'weekly sync' } } }));
  ok(!rc.valid && rc.answer.errors.date === 'Nothing changed.', '13 / 8: an unchanged lowercase title is not a change; "Nothing changed."');
  rc = await rcv(JSON.parse(cv.private_metadata), Object.assign({}, base, { room: { room_pick: tv('Studio F') }, purpose_c: { purpose_c: tv('Meeting') }, det_title: { det_title_in: { value: 'weekly sync' } } }));
  ok(rc.valid && rc.newTitle === 'STUDIO F - weekly sync', '22: moved to Studio F -> the title follows the room');
  rc = await rcv(JSON.parse(cv.private_metadata), Object.assign({}, base, { room: { room_pick: tv('Likha') }, purpose_c: { purpose_c: tv('Meeting') }, det_title: { det_title_in: { value: 'monthly sync' } } }));
  ok(rc.valid && rc.newTitle === 'LIKHA - Monthly sync', '13: a new title starts with a capital');
  cv = await buildChange({ id: 'ev3', d: '2027-10-20', s: '00:00', e: '00:00', r: 'M5', t: 'M5 - Howard' });
  ok(blk(cv, 'det_forname') && blk(cv, 'det_forname').element.initial_value === 'Howard' && !blk(cv, 'det_none'), '20: Change an M booth - "Who is it for?" from the title');
  rc = await rcv(JSON.parse(cv.private_metadata), { date: { date_pick: { selected_date: '2027-10-20' } }, allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } }, room: { room_pick: tv('M5') },
    det_forname: { det_forname_in: { value: 'joaquin' } } });
  ok(rc.valid && rc.newTitle === 'M5 - Joaquin', '20: a new name -> "M5 - Joaquin"');
  rc = await rcv(JSON.parse(cv.private_metadata), { date: { date_pick: { selected_date: '2027-10-20' } }, allday_toggle: { allday_toggle: { selected_options: [{ value: 'allday' }] } }, room: { room_pick: tv('M7') },
    det_forname: { det_forname_in: { value: 'Howard' } } });
  ok(rc.valid && rc.newTitle === 'M7 - Howard', '20: a new booth -> the title follows ("M7 - Howard")');
  cv = await buildChange({ id: 'ev4', d: '2027-10-20', s: '16:00', e: '18:00', r: 'Studio C', t: 'NET-CAM / HL', st: 'Atmos Mixing' });
  ok(blk(cv, 'room').element.options.map(o => o.value).join() === 'Studio C' && blk(cv, 'det_project').label.text === 'Project title or code' && blk(cv, 'det_engineer') && !blk(cv, 'det_client'),
     '18: Change an Atmos booking - Studio C only; Project title or code + Engineer');
  cv = await buildChange({ id: 'ev5', d: '2027-10-16', s: '11:00', e: '14:00', r: 'Studio F, Studio D, Likha, Katha', t: 'CELEB / Jem Lim / HL', st: 'Celebrity Recording' });
  ok(blk(cv, 'holding_c').element.type === 'multi_static_select' && blk(cv, 'holding_c').element.initial_options.map(o => o.value).join() === 'Katha,Likha' && blk(cv, 'booth_c').label.text === (V53 ? 'Vocal booths' : 'Vocal booth'),
     '21: Change - Holding rooms a dropdown (Likha, Katha picked), Vocal booth');
  const MC = await j1('Mark Changing', [{ json: { messages: [{ ts: '7.7', text: 'x', blocks: [{ type: 'section', block_id: 'bk_ev1', text: { type: 'mrkdwn', text: '*OLD / HL*\nWed, Oct 20 · 4:00 PM – 6:00 PM · Studio 8' } },
    { type: 'actions', block_id: 'bka_ev1', elements: [] }] }] } }], { 'Read Change': [{ json: { b: { id: 'ev1', t: 'OLD / HL' }, n: { d: '2027-10-21', s: '10:00', e: '12:00' }, newTitle: 'NEW / HL', newRooms: 'Studio 7', meta: { ts: '7.7', ch: 'D1' } } }] });
  ok(MC.ok && MC.blocks[0].text.text === '*NEW / HL*\nThu, Oct 21 · 10:00 AM – 12:00 PM · Studio 7' && MC.blocks[1].elements[0].text === '⏳ Changing…', '17 / 2: changing -> the row shows what it becomes, "⏳ Changing…"');
  const MX = await j1('Mark Cancelling', [], { 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify({ id: 'ev1' }) }], message: { blocks: [{ type: 'section', block_id: 'bk_ev1', text: { type: 'mrkdwn', text: 'x' } }, { type: 'actions', block_id: 'bka_ev1', elements: [] }] }, container: { channel_id: 'D1', message_ts: '7.7' } } } }] });
  ok(MX.blocks.find(b => b.block_id === 'bkw_ev1').elements[0].text === '⏳ Cancelling…', '2: "⏳ Cancelling…"');

  console.log('main v275 - the chat');
  const menuFor = async (text, extra) => m1('Menu Check', [], Object.assign({ 'Slack Trigger': [{ json: { text, ts: '100', channel: 'D1' } }], 'Gate Context': [{ json: { gate: {} } }], 'Get Recent Messages': [],
    'Get Booker': [{ json: { fields: { Name: 'Howard Luistro' } } }] }, extra || {}));
  for (const t of ['hi', 'reset', 'what can you do?', 'help']) { const mc = await menuFor(t);
    ok(mc.menu && mc.blocks[0].text.text === 'Hi, I’m Jessie!' && mc.blocks.length === 2 && mc.blocks[1].elements.map(e => e.action_id).join() === 'open_book,my_bookings', '7: "' + t + '" -> "Hi, I’m Jessie!" and the two buttons, nothing else'); }
  let mc = await menuFor('thanks');
  ok(mc.menu && mc.blocks[0].text.text === 'Anytime!', '7: thanks -> "Anytime!"');
  mc = await menuFor('test');
  ok(mc.menu && mc.blocks[0].text.text === 'I can only help with bookings.', '7: something else -> "I can only help with bookings."');
  mc = await menuFor('client is jem lim', { 'Get Recent Messages': [{ json: { ts: '9', bot_id: 'B', text: 'x', blocks: [{ type: 'section', text: { type: 'mrkdwn', text: 'Your booking details so far:\n🗓️ *Studio 7*' } },
    { type: 'actions', elements: [{ action_id: 'open_book', value: '{"r":"Studio 7"}' }] }] } }] });
  ok(mc.menu === false, '8d: a new offer ("Your booking details so far:") still waits for its details');
  const fo = main.nodes.find(n => n.name === 'Form Offer').parameters.jsCode;
  ok(/\['Your booking details so far:'\]/.test(fo) && !/Opens the form with these filled in/.test(fo) && !/Pick the date, time and room in the form/.test(fo) && /Here’s what I have so far:\|Let’s book it/.test(fo),
     '8c / 8d: the offer says "Your booking details so far:", no line under the buttons; older offers still recognised');
  const cr = main.nodes.find(n => n.name === 'Change Reply').parameters.jsCode;
  ok(/'Your change so far:'/.test(cr) && /'Here’s the booking:'/.test(cr) && !/press \*Cancel\* to cancel it/.test(cr), '8: typed change / cancel - "Here’s the booking:", "Your change so far:"');
  ok(/'Use \*Book a room\* or \*My bookings\* below\.'/.test(main.nodes.find(n => n.name === 'Build Reply').parameters.jsCode), '8: a booking question -> "Use *Book a room* or *My bookings* below."');
  ok(/Still booking that series - I’ll post here when it’s done\./.test(JSON.stringify(main.nodes.find(n => n.name === 'Series Busy Reply').parameters)), '8: "Still booking that series - I’ll post here when it’s done."');
  ok(/Your change so far/.test(si.nodes.find(n => n.name === 'After Cancel').parameters.jsCode), 'the form drops "Your change so far:" once the booking is changed (like "Here’s the booking")');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
