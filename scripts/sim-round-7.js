#!/usr/bin/env node
// Round 7 offline (Slack Interactions v24, Move Booking v33, main v274): fields by session type on Book and Change, the project
// search (block_suggestion), "Booking this for someone else?", a meeting's department, notes shown, the session type on rows.
// Usage: node scripts/sim-round-7.js [slack-interactions v24] [move-booking v33] [main v274]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v24.json', 'utf8'));
const V39 = JSON.stringify(si.nodes).indexOf('a phone shows no') !== -1;   // v39: "No booth / engineer / arranger" back, last (phones cannot clear a pick)
const V26 = /function roomAllowed\(/.test(JSON.stringify(si.nodes));   // round 9: no "No …" options, no "pick one or both", room labels (sim-round-9)
const mv = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/move-booking-v33.json', 'utf8'));
const main = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/project-jessie-v274.json', 'utf8'));
const V29 = !si.nodes.some(n => n.name === 'Suggest Codes');   // v29: the project-code search route removed (a text box since v25)
const FX = require('./sim-fixture-rooms.js');
const V25 = /function onlyRoom\(/.test(JSON.stringify(si.nodes));   // round 8: no "for someone else", a typed project code, an M booth name
const V30 = /function pairBlocksC\(/.test(JSON.stringify(si.nodes));   // round 12: Booker dropdown, code without Enter (sim-round-12)
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.log('FAIL', m); } };
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

// the reference data: the 15 Oct rooms, session types with their Airtable roles, bookers with departments
const ST = (t, roles, pri) => ({ id: 'st-' + t, fields: { Type: t, 'Engineer Role Required': roles, Priority: pri || [], 'Last Resort': [], 'Room Requirements': '' } });
const sessionTypes = [ST('VO Recording', ['Post Engineer'], ['r7', 'r8']), ST('Music Mixing', ['Music Engineer', 'Music Arranger'], ['rf']),
  ST('Music Vocal Recording', ['Music Engineer', 'Music Arranger'], ['rf']), ST('Localization Dubbing', ['Loc Engineer'], ['r1', 'r2']),
  ST('QC', ['Loc Engineer'], ['r3']), ST('Post Processing', ['Multimedia Specialist'], ['re']), ST('Meeting', ['None'], ['lk']), ST('Event', ['None'], ['lo'])];
const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: dept } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer, Goes by Howard.', ['Audio Post']), B('b2', 'Jetrho Ty', 'JT', 'U3', 'Loc Engineer, Goes by Jetrho.', ['Localization']),
  B('b3', 'Vianne Cruz', 'VC', 'U4', 'Loc Engineer, Goes by Via.', ['Localization']), B('b4', 'Joaquin Santos', 'JS', 'U9', 'Music Arranger, Goes by Joaquin.', ['Music']),
  B('b5', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer, Post Engineer. Goes by Daryl.', ['Music']), B('b6', 'Letty Ramos', 'LR', 'U7', 'Coordinator, Goes by Letty.', ['Music']),
  B('b7', 'Dylan Diaz', 'DD', 'U0BQ77XKWA3', 'Multimedia Specialist, Goes by Dilan.', ['Marketing'])];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes, bookers }) } }];
const LOC = [{ json: { id: 'p1', 'Project Code': 'NET-MALAS', 'Project Title': 'BAD DAY', 'Client Name': 'NETFLIX', Recordist: ['Jetrho'], Mixer: ['Via'] } },
  { json: { id: 'p2', 'Project Code': 'NET-CAM', 'Project Title': 'CAMPIONI', 'Client Name': 'NETFLIX', Recordist: ['Via'], Editor: ['Josiah'], Mixer: ['Via'] } },
  { json: { id: 'p3', fields: { 'Project Code': 'LOPH S2', 'Project Title': 'LAUGH OUT LOUD PH SEASON 2', Recordist: ['John '] } } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind, extra) => Object.assign({ date: '2027-10-19', t0: '13:00', t1: '15:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra || { free_priority: ['Studio 7'] }) }],
  { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': LOC })).view;
const ids = v => v.blocks.map(b => b.block_id).filter(Boolean);
const blk = (v, id) => v.blocks.find(b => b.block_id === id);

(async () => {
  // ---- 1: What's it for? first
  const s1 = (await j1('Build Step 1', [], { 'Check Signature': [chk], 'Read Cache': cacheRow })).view;
  ok(s1.blocks[1].block_id === 'purpose' && s1.blocks[2].block_id === 'date', '1: step 1 - What\'s it for? first, then the date - ' + ids(s1).join());

  // ---- 5-6, 9: step 2 by session type
  let v = await step2(S('VO Recording', 'studio'));
  ok(ids(v).indexOf('arranger') === -1 && !blk(v, 'engineer').optional && blk(v, 'engineer').element.initial_option.value === 'U1' && !blk(v, 'team_note'),
     '5: VO Recording - Engineer (required, set to you), no Arranger (Airtable: Post Engineer only)');
  ok(blk(v, 'notes') && blk(v, 'notes').type === 'input' && blk(v, 'notes').optional && !blk(v, 'note_toggle'), '9: the Note is shown - no "Add a note" box');
  v = await step2(S('Music Mixing', 'studio'), { free_priority: ['Studio F'] });
  ok((V26 ? !blk(v, 'team_note') : blk(v, 'team_note') && ids(v).indexOf('team_note') < ids(v).indexOf('engineer') && /pick one or both/.test(blk(v, 'team_note').elements[0].text))
     && blk(v, 'engineer').optional && blk(v, 'arranger').optional, '6: Music Mixing - "Engineer and arranger: pick one or both.", both optional');
  ok(V26 ? (V39 ? blk(v, 'engineer').element.options.slice(-1)[0].value === 'none' : !blk(v, 'engineer').element.options.some(o => o.value === 'none')) && (V39 ? blk(v, 'arranger').element.options.slice(-1)[0].value === 'none' : !blk(v, 'arranger').element.options.some(o => o.value === 'none')) && blk(v, 'engineer').element.placeholder.text === 'No engineer' && blk(v, 'arranger').element.placeholder.text === 'No arranger'
     : blk(v, 'engineer').element.options[0].value === 'none' && blk(v, 'arranger').element.options[0].value === 'none', '6: "No engineer" / "No arranger" first - a picked Slack dropdown cannot be emptied otherwise');
  ok(!(await step2(S('VO Recording', 'studio'))).blocks.find(b => b.block_id === 'engineer').element.options.some(o => o.value === 'none'), '5: VO Recording - no "No engineer"');
  v = await step2(S('Music Mixing', 'studio', { requester: 'U9' }), { free_priority: ['Studio F'] });
  ok(!blk(v, 'engineer').element.initial_option && blk(v, 'arranger').element.initial_option.value === 'U9', '6: an arranger booking - Arranger set to them, Engineer empty');

  // ---- 7-8: meetings, events, M booths
  v = await step2(S('Meeting', 'meeting'), { free_priority: ['Likha'] });
  ok(blk(v, 'title').label.text === 'Meeting title' && blk(v, 'department').element.initial_option.value === 'Audio Post' && (V25 ? !blk(v, 'forwho_toggle') : blk(v, 'forwho_toggle')) && blk(v, 'notes'),
     '8: Meeting - title, Department set to yours (Audio Post), "Booking this for someone else?", Note');
  v = await step2(S('Event', 'meeting'), { free_priority: ['Lobby'] });
  ok(blk(v, 'title').label.text === 'Event title' && !blk(v, 'department') && (V25 ? !blk(v, 'forwho_toggle') : blk(v, 'forwho_toggle')), '8: Event - no department');
  v = await step2(S('', 'booth'), { free_rooms: ['M1', 'M2'] });
  ok((V25 ? blk(v, 'forname') && blk(v, 'forname').element.initial_value === 'Howard' : blk(v, 'forwho_toggle')) && blk(v, 'notes') && !blk(v, 'engineer'), '7: M booth - "for someone else" (v25: "Who is it for?" typed) and a note');

  // ---- 11: Localization - the project code search
  v = await step2(S('Localization Dubbing', 'loc', { pre: { cd: 'net-malas' } }), { free_priority: ['Studio 1'] });
  const code = blk(v, 'code');
  ok(V25 ? (code.element.type === 'plain_text_input' && code.element.action_id === 'code_in' && (V30 ? !code.dispatch_action : code.dispatch_action === true) && code.element.initial_value === 'NET-MALAS')
     : (code.element.type === 'external_select' && code.element.action_id === 'code_pick' && code.dispatch_action === true && code.element.min_query_length === 0
     && code.element.initial_option.value === 'NET-MALAS'), '11: Project code - a type-to-search list, the typed code picked (v25: typed)');
  ok(/\*BAD DAY\* · NETFLIX\nRecordist: Jetrho · Editor: - · Mixer: Via/.test(blk(v, 'code_info').elements[0].text), '11: the project shown under it - ' + JSON.stringify(blk(v, 'code_info').elements[0].text));
  ok(blk(v, 'engineer').element.initial_option.value === 'U3' && blk(v, 'engineer').element.options[0].value === 'U3' && (V25 ? !blk(v, 'engineer').hint : /From the project/.test(blk(v, 'engineer').hint.text)),
     '11: Dubbing - the Recordist (Jetrho) set as the engineer, first in the list');
  v = await step2(S('QC', 'loc', { pre: { cd: 'NET-MALAS' } }), { free_priority: ['Studio 3'] });
  ok(blk(v, 'engineer').element.initial_option.value === 'U1', '11: QC - nobody from the project preset (anyone; you as before)');
  v = await step2(S('Localization Dubbing', 'loc', { pre: { cd: 'NET-NEWSHOW' } }), { free_priority: ['Studio 1'] });
  ok(V25 ? (blk(v, 'code').element.initial_value === 'NET-NEWSHOW' && !blk(v, 'code_info'))
     : (blk(v, 'code').element.initial_option.value === 'new:NET-NEWSHOW' && /New project code/.test(blk(v, 'code_info').elements[0].text)), '11: a code not in Airtable - kept, "New project code" (v25: nothing shown)');

  if (!V29) {
  const suggest = async (q) => (await j1('Suggest Codes', LOC, { 'Read Request': [{ json: { payload: { type: 'block_suggestion', action_id: 'code_pick', value: q } } }] })).answer.options;
  let o = await suggest('net');
  ok(o.map(x => x.value).join() === 'NET-CAM,NET-MALAS,new:NET' && o[0].text.text === 'NET-CAM · CAMPIONI' && o[2].text.text === 'Use “NET” as a new code', '11: typing "net" - the matches, then "Use “NET” as a new code"');
  o = await suggest('net-malas');
  ok(o.map(x => x.value).join() === 'NET-MALAS', '11: an exact code - no "new code" line');
  o = await suggest('');
  ok(o.length === 3 && !o.some(x => /^new:/.test(x.value)), '11: nothing typed - every project');
  o = await suggest('laugh');
  ok(o[0].value === 'LOPH S2', '11: a title matches too');
  ok(o.every(x => !x.description), 'no dropdown option carries a description');
  }
  // routes
  const route = async (payload) => (await j1('Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_suggestion', action_id: 'code_pick', value: 'n' }) === (V29 ? 3 : 14), 'route: block_suggestion -> the project search (v29: "other")');
  for (const a of ['code_pick', 'forwho_toggle', 'purpose_c']) ok(await route({ type: 'block_actions', actions: [{ action_id: a }] }) === 8, 'route: ' + a + ' -> the redraw');
  const C = si.connections, nx = n => (C[n].main || []).map(x => x.map(c => c.node).join('+')).join(' | ');
  ok(V29 ? nx('Read Cache 2') === 'Loc Needed?' && nx('Loc Needed?') === 'Loc Projects 2 | To Room Availability' && nx('Loc Projects 2') === 'To Room Availability'
       && nx('Read Cache 9') === 'Code Typed?' && nx('Code Typed?') === 'Loc Projects 9 | Note Toggle' && nx('Loc Projects 9') === 'Note Toggle'
     : C.Route.main[14][0].node === 'Loc Projects S' && nx('Loc Projects S') === 'Suggest Codes' && nx('Suggest Codes') === 'Answer Suggest'
     && nx('Read Cache 2') === 'Loc Projects 2' && nx('Loc Projects 2') === 'To Room Availability' && nx('Read Cache 9') === 'Loc Projects 9' && nx('Loc Projects 9') === 'Note Toggle', 'wiring');
  const air = si.nodes.filter(n => /^Loc Projects/.test(n.name));
  ok(air.length === (V29 ? 2 : 3) && air.every(n => n.executeOnce && n.alwaysOutputData && n.parameters.table.value === 'tbljkG6z7odPUtTIf'), 'the three project reads: Localization Projects, once, never empty-handed');

  // ---- the redraws
  const toggle = async (view, action, extra, state) => j1('Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
    actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow, 'Loc Projects 9': LOC });
  v = await step2(S('Localization Mixing', 'loc'), { free_priority: ['Studio 3'] });
  let t = V25 ? await toggle(v, 'code_in', { value: 'net-cam' }, { code: { code_in: { value: 'net-cam' } } }) : await toggle(v, 'code_pick', { selected_option: { value: 'NET-CAM' } }, { code: { code_pick: tv('NET-CAM') } });
  ok((V25 ? blk(t.view, 'code').element.initial_value === 'net-cam' : blk(t.view, 'code').element.initial_option.value === 'NET-CAM') && /\*CAMPIONI\*/.test(blk(t.view, 'code_info').elements[0].text)
     && blk(t.view, 'engineer').element.initial_option.value === 'U4', '11: a code picked (Mixing) - the project shown, the Mixer (Via) set, the pick kept');
  v = await step2(S('Meeting', 'meeting'), { free_priority: ['Likha'] });
  if (V25) v = { blocks: v.blocks.concat([{ type: 'actions', block_id: 'forwho_toggle', elements: [{ type: 'checkboxes', action_id: 'forwho_toggle', options: [{ text: { type: 'plain_text', text: 'x' }, value: 'for' }] }] }]) };   // a v24 form still open
  t = await toggle(v, 'forwho_toggle', { selected_options: [{ value: 'for' }] });
  ok(ids(t.view).indexOf('forwho') === ids(t.view).indexOf('forwho_toggle') + 1 && blk(t.view, 'forwho').element.options.length === 7
     && blk(t.view, 'forwho').element.options.some(o => o.value === 'U7'), '7: ticked -> "Who is it for?" with everyone in Bookers (Letty too)');
  t = await toggle(t.view, 'forwho_toggle', { selected_options: [] });
  ok(!blk(t.view, 'forwho'), '7: unticked -> gone');

  // ---- step 2's answers
  const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
  const M = (purpose, kind, extra) => Object.assign(S(purpose, kind), { when: 'Tuesday, Oct 19 · 1:00 PM–3:00 PM', label: purpose }, extra || {});
  let r = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'x' } }, arranger: { arranger_pick: tv('U9') } }, M('Music Mixing', 'studio'));
  ok(r.valid && r.calTitle === 'X / JS' && /no engineer/.test(r.prep.requester_text), '6: Music Mixing with only an arranger -> books, "X / JS"');
  r = await read2({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'x' } } }, M('Music Mixing', 'studio'));
  ok(!r.valid && r.answer.errors.engineer === 'Pick an engineer or an arranger.', '6: neither -> "Pick an engineer or an arranger."');
  r = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'x' } } }, M('VO Recording', 'studio'));
  ok(!r.valid && r.answer.errors.engineer === 'Pick the engineer.', '5: VO Recording without an engineer -> "Pick the engineer."');
  r = await read2(V25 ? { room: { room_radio: tv('M2') }, forname: { forname_in: { value: 'Daryl' } }, notes: { notes_in: { value: 'warm-up' } } }
    : { room: { room_radio: tv('M2') }, forwho: { forwho_pick: tv('U2') }, notes: { notes_in: { value: 'warm-up' } } }, M('', 'booth', { label: 'M booth' }));
  ok(r.valid && r.calTitle === 'M2 - Daryl' && /Booked by: Howard Luistro \(for Daryl Reyes\)/.test(r.prep.description) && r.team === 'U2' && r.forId === 'U2' && /Notes: warm-up/.test(r.prep.description),
     '7: an M booth for Daryl - "M2 - Daryl", "Booked by: Howard Luistro (for Daryl Reyes)", Daryl on the booking');
  r = await read2({ room: { room_radio: tv('Likha') }, title: { title_in: { value: 'Sync' } }, department: { department_pick: tv('Music') } }, M('Meeting', 'meeting'));
  ok(r.valid && r.prep.department === 'Music', '8: the meeting\'s department goes to Book Session ("Dept: Music")');
  r = await read2({ room: { room_radio: tv('Studio 1') }, code: { code_pick: tv('new:NET-NEWSHOW') }, engineer: { engineer_pick: tv('U3') } }, M('Localization Dubbing', 'loc'));
  ok(r.valid && r.calTitle === 'NET-NEWSHOW / JT', '11: a new code books as typed - NET-NEWSHOW / JT');
  const bn = await runIn(si, 'Booked Notices', [{ json: {} }], { 'Read Step 2': [{ json: { forId: 'U2', s: S('', 'booth'), engineerId: '', arrangerId: '' } }], 'Read Cache 3': cacheRow,
    'After Book': [{ json: { ok: true, text: '✅ *Booked.*', blocks: [] } }], 'Check Signature': [chk], 'Read Request': [{ json: { payload: { user: { id: 'U1' } } } }] }).catch(e => ({ err: String(e) }));
  ok(/booked this for you/.test(JSON.stringify(bn)), '7: the person it is for is told - ' + JSON.stringify(bn).slice(0, 160));

  // ---- 2-4: the Change form
  const buildChange = async (b) => (await j1('Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(b) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
  const yam = { id: 'ev1', d: '2027-10-19', s: '13:00', e: '19:00', r: 'Studio 8', t: 'PURPLE YAM / Jem Lim / AEG', st: 'VO Recording' };
  let cv = await buildChange(yam);
  ok(cv.blocks[1].block_id === 'purpose_c' && blk(cv, 'purpose_c').element.initial_option.value === 'VO Recording' && blk(cv, 'purpose_c').dispatch_action, '3: Change - What\'s it for? first, set to VO Recording');
  ok(blk(cv, 'det_anchor') && blk(cv, 'det_project') && blk(cv, 'det_engineer') && !blk(cv, 'det_arranger') && !blk(cv, 'details_toggle') && blk(cv, 'det_notes'),
     '2/4: the VO Recording details shown at once - no Arranger (Slack 16 Oct showed one), no tick box, a Note');
  const meta = JSON.parse(cv.private_metadata);
  t = await toggle(cv, 'purpose_c', { selected_option: { value: 'Music Mixing' } }, { purpose_c: { purpose_c: tv('Music Mixing') }, det_project: { det_project_in: { value: 'PURPLE YAM' } } });
  ok((V26 || blk(t.view, 'team_note')) && blk(t.view, 'det_arranger') && blk(t.view, 'det_project').element.initial_value === 'PURPLE YAM', '3: changed to Music Mixing - the details follow (arranger, pick one or both), the project kept');
  t = await toggle(cv, 'purpose_c', { selected_option: { value: 'QC' } }, { purpose_c: { purpose_c: tv('QC') } });
  ok(blk(t.view, 'det_code') && blk(t.view, 'det_code').element.type === (V25 ? 'plain_text_input' : 'external_select') && !blk(t.view, 'det_client'), '3: changed to QC - a project code instead of project / client');
  cv = await buildChange(Object.assign({}, yam, { st: '' }));
  ok(blk(cv, 'purpose_c').optional && !blk(cv, 'purpose_c').element.initial_option && blk(cv, 'det_project'), '2: an older booking (no SType) - What\'s it for? optional, the details from its title');
  cv = await buildChange({ id: 'ev5', d: '2027-10-15', s: '00:00', e: '00:00', r: 'M5', t: 'M5 - Howard' });
  ok(!blk(cv, 'purpose_c') && blk(cv, 'allday_toggle'), 'an M booth - no session type to pick; All day as before');

  const readChange = async (m, vals) => j1('Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(m), state: { values: vals } } } } }], 'Read Cache 10': cacheRow });
  const base = { date: { date_pick: { selected_date: '2027-10-19' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('19:00') }, room: { room_pick: tv('Studio 8') },
    purpose_c: { purpose_c: tv('VO Recording') }, det_project: { det_project_in: { value: 'PURPLE YAM' } }, det_client: { det_client_in: { value: 'Jem Lim' } }, det_engineer: { det_engineer_pick: tv('U2') } };
  const metaX = Object.assign({}, meta, { b: Object.assign({}, meta.b, { t: 'PURPLE YAM / Jem Lim / DR' }) });
  let rc = await readChange(metaX, base);
  ok(!rc.valid && /Nothing changed/.test(rc.answer.errors.date), 'nothing changed -> said (the details shown count as unchanged)');
  rc = await readChange(metaX, Object.assign({}, base, { purpose_c: { purpose_c: tv('Music Mixing') }, det_engineer: { det_engineer_pick: tv('U2') }, det_arranger: { det_arranger_pick: tv('U9') } }));
  let tm = await j1('To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  const nd = JSON.parse(tm.new_details || '{}');
  ok(rc.valid && rc.newTitle === 'PURPLE YAM / Jem Lim / DR x JS' && nd.SType === 'Music Mixing' && nd.team === 'U2 U9', '3: VO -> Music Mixing + an arranger: title DR x JS, SType and team go to Move - ' + tm.new_details);
  rc = await readChange(metaX, Object.assign({}, base, { det_notes: { det_notes_in: { value: 'bring the | script' } } }));
  tm = await j1('To Move', [], { 'Read Change': [{ json: rc }], 'Read Cache 7': cacheRow, 'Client Names': [] });
  ok(rc.valid && JSON.parse(tm.new_details).Notes === 'bring the / script' && !('SType' in JSON.parse(tm.new_details)), '9: a new note alone is a change (Move writes it)');
  rc = await readChange(metaX, Object.assign({}, base, { det_engineer: { det_engineer_pick: { selected_option: null } } }));
  ok(!rc.valid && rc.answer.errors.det_engineer === 'Pick the engineer.', '5: VO Recording without an engineer -> "Pick the engineer."');

  // ---- Move Booking v33: the note and the session type on the replacement
  const rb = mv.nodes.find(n => n.name === 'Resolve Booking').parameters.jsCode;
  const k1 = rb.indexOf('let __title = title, __desc = desc'), k2 = rb.indexOf('} catch (e) { __title = title; __desc = desc;', k1);   // v39: + __teamChanged
  const runDesc = (desc, nd) => new Function('desc', 'title', 'REQ', 'const team = [];\n' + rb.slice(k1, k2) + '} catch (e) { __title = title; __desc = desc; }\nreturn __desc;')(desc, 'T', { new_details: JSON.stringify(nd) });
  const desc0 = 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | team: U2 | Notes: old\nSType: VO Recording';
  const NB = /v37 \(26 Oct\)/.test(rb);   // Move v37: the note in its own block under the SType line
  ok(runDesc(desc0, { SType: 'Music Mixing', Arranger: 'Joaquin Santos', team: 'U2 U9' }) === (NB ? 'Arranger: Joaquin Santos | Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | team: U2 U9\nSType: Music Mixing\n\nNotes:\nold'
       : 'Arranger: Joaquin Santos | Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | Notes: old | team: U2 U9\nSType: Music Mixing'),
     'Move v33: a new session type - the SType line rewritten, kept last - ' + JSON.stringify(runDesc(desc0, { SType: 'Music Mixing', Arranger: 'Joaquin Santos', team: 'U2 U9' })));
  ok(runDesc(desc0, { Notes: 'new note' }) === (NB ? 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | team: U2\nSType: VO Recording\n\nNotes:\nnew note'
       : 'Engineer: Daryl Reyes | Booked by: Howard Luistro | ref: U1 | team: U2 | Notes: new note\nSType: VO Recording'), 'Move v33: a new note - replaced, SType kept (v37: in its own block)');
  ok(NB ? /Rooms: Studio F, Studio A\nSType: VO Recording\n\nNotes:\nold$/.test(runDesc(desc0, { Rooms: 'Studio F, Studio A' })) : runDesc(desc0, { Rooms: 'Studio F, Studio A' }).endsWith('Rooms: Studio F, Studio A\nSType: VO Recording'),
     'Move v33: other changes keep the SType line after the technical line (v32 put Rooms after it; v37: the note below)');

  // ---- rows: the session type rides on Change; main v274's chat lists
  const mr = main.nodes.find(n => n.name === 'Mine Reply').parameters.jsCode;
  const helpers = new Function(mr.slice(mr.indexOf('const _DS'), mr.indexOf('// Mine Reply')) + '; return { evBooking, whenLine, bkValue };');
  let H; try { H = helpers(); } catch (e) { H = null; console.log(e); }
  const att = ['KDC Plaza-Top Level-Studio D (5)', 'KDC Plaza-Top Level-Studio F (12)', 'KDC Plaza-Top Level-Likha (Big Room) (12)'].map(d => ({ resource: true, email: 'x@resource.calendar.google.com', displayName: d }));
  const ev = { id: 'e1', summary: 'CELEB / HL', start: { dateTime: '2027-10-16T11:00:00+08:00' }, end: { dateTime: '2027-10-16T14:00:00+08:00' }, attendees: att,
    description: 'Engineer: Howard Luistro | Rooms: Studio F, Studio D, Likha | ref: U1\nSType: Celebrity Recording' };
  const bk = H && H.evBooking(ev);
  ok(bk && bk.r === 'Studio F, Studio D, Likha' && bk.st === 'Celebrity Recording' && /Sat, Oct 16 · 11:00 AM – 2:00 PM · Studio F \+ Studio D \+ Likha/.test(H.whenLine(bk)) && JSON.parse(H.bkValue(bk)).st === 'Celebrity Recording',
     'main v274: a chat row - rooms in order, "Studio F + Studio D + Likha", the session type on Change - ' + (bk && H.whenLine(bk)));
  const allDay = H && H.evBooking({ id: 'e2', summary: 'M5 - Howard', start: { dateTime: '2027-10-15T00:00:00+08:00' }, end: { dateTime: '2027-10-16T00:00:00+08:00' }, attendees: [] });
  ok(allDay && /· all day/.test(H.whenLine(allDay)), 'main v274: an all-day M booth reads "all day" (was 12:00 AM – 12:00 AM)');

  // ---- no dropdown option with a description anywhere drawn here
  let bad = 0; const walk = x => { if (!x || typeof x !== 'object') return; if (x.type === 'static_select' || x.type === 'external_select') for (const o of [].concat(x.options || [])) if (o.description) bad++; for (const k of Object.keys(x)) walk(x[k]); };
  [s1, v, t.view, cv].forEach(walk);
  ok(bad === 0, 'no dropdown option carries a description');

  console.log(pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
