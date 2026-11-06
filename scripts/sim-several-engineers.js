#!/usr/bin/env node
// Howard, 6 Nov: engineers and arrangers are multi-selects (not Localization), the title lists their initials with spaces and the
// arranger(s) after " x " ("HL AEG x MV"), and everyone on it is told. Through the real nodes: Slack Interactions v70 (step 2, Read
// Step 2, Booked Notices, Change form, Read Change, Change Notices, My bookings), Book Session v128 (Check Conflicts), Reminders v10,
// Request Messages v7.
//   node scripts/sim-several-engineers.js [slack-interactions v70] [book-session v128] [reminders v10] [request-messages v7]
const fs = require('fs');
const load = (p, d) => JSON.parse(fs.readFileSync(p || d, 'utf8'));
const SI = load(process.argv[2], 'workflows/slack-interactions-v70.json'), BS = load(process.argv[3], 'workflows/book-session-v128.json');
const RM = load(process.argv[4], 'workflows/reminders-v10.json'), RQ = load(process.argv[5], 'workflows/request-messages-v7.json');
if (!/v70 \(Howard, 6 Nov\)/.test(JSON.stringify(SI.nodes))) { console.log('0 ok, 0 failed (an older build: v70 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const run = async (wf, name, input, outs) => { const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }), { first: () => input[0], all: () => input }); };
const j1 = async (...a) => ((await run(...a))[0] || {}).json;
const B = (Name, Initials, id, Info, dep) => ({ id: 'b' + id, fields: { Name, Initials, 'Slack User ID': id, Info, Department: [dep] } });
const bookers = FX.bookers.concat([B('Elijah Gan', 'AEG', 'U5', 'Post Engineer, Goes by Eli.', 'Audio Post'), B('Daryl Reyes', 'DR', 'U7', 'Post Engineer, Goes by Drey.', 'Audio Post'),
  B('Mike Villegas', 'MV', 'U6', 'Music Arranger, Goes by Mike.', 'Music'), B('Ana Cruz', 'AC', 'U8', 'Music Engineer, Goes by Ana.', 'Music')]);
const ST = (t, role) => ({ id: 'st-' + t, fields: { Type: t, 'Room Requirements': '', Priority: ['r7'], 'Last Resort': [], 'Engineer Role Required': [].concat(role) } });
const sessionTypes = FX.sessionTypes.concat([ST('Music Recording', ['Music Engineer', 'Music Arranger'])]);
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes, bookers }) } }];
const tv = v => ({ selected_option: { value: v } }), ms = a => ({ selected_options: a.map(value => ({ value })) });
const S = (purpose, kind, extra) => Object.assign({ date: '2026-11-12', t0: '13:00', t1: '16:00', purpose, kind, requester: 'U1', channel: 'D1', ext: 'x' }, extra || {});
const blk = (v, id) => (v.blocks || []).find(b => b.block_id === id);

(async () => {
  console.log('Book a room, step 2: the people fields');
  const step2 = async (s, ra) => (await j1(SI, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [], free_priority: ['Studio 7'] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': [] })).view;
  const V71 = /v71 \(Howard, 6 Nov\)/.test(JSON.stringify(SI.nodes));   // one engineer + "Add more engineers"
  let v, e;
  if (!V71) {
    v = await step2(S('VO Recording', 'studio'));
    e = blk(v, 'engineer');
    ok(e && e.element.type === 'multi_static_select' && e.dispatch_action === true && (e.element.initial_options || []).map(o => o.value).join() === 'U1' && !e.element.options.some(o => o.value === 'none'),
      'VO Recording: Engineer is a multi-select, you picked (as before), no "No engineer" option (a phone can clear it)', e && e.element);
    v = await step2(S('VO Recording', 'studio', { pre: { en: 'U1,U5' } }));
    ok((blk(v, 'engineer').element.initial_options || []).map(o => o.value).sort().join() === 'U1,U5' && /Picked: Elijah Gan, Howard Luistro/.test(JSON.stringify(v.blocks)), 'saved answers "U1,U5" -> both picked, "Picked: Elijah Gan, Howard Luistro"');
  } else {
    v = await step2(S('VO Recording', 'studio')); e = blk(v, 'engineer');
    const tk = blk(v, 'more_eng_toggle');
    ok(e.element.type === 'static_select' && e.element.initial_option.value === 'U1' && tk && /^(?:Add more|Multiple) engineers$/.test(tk.elements[0].options[0].text.text) && !tk.elements[0].initial_options && !blk(v, 'more_eng')
       && v.blocks.indexOf(tk) === v.blocks.indexOf(e) + 1, 'v71 VO Recording: one Engineer dropdown (its name shows on a phone), "Add more engineers" under it, unticked', v.blocks.map(b => b.block_id));
    v = await step2(S('VO Recording', 'studio', { pre: { en: 'U1,U5' } }));
    const me = blk(v, 'more_eng');
    ok(blk(v, 'engineer').element.initial_option.value === 'U1' && (blk(v, 'more_eng_toggle').elements[0].initial_options || []).length === 1 && me && (me.element.initial_options || []).map(o => o.value).join() === 'U5'
       && !me.element.options.some(o => o.value === 'U1'), 'v71 saved "U1,U5": Howard the engineer, the box ticked, Elijah under More engineers', v.blocks.map(b => b.block_id));
    v = await step2(S('Music Recording', 'studio', { pre: { ar: 'U6' } }));
    ok(blk(v, 'engineer').element.type === 'static_select' && !blk(v, 'more_eng_toggle') && blk(v, 'arranger').element.type === 'multi_static_select' && blk(v, 'arranger_picked')
       && blk(v, 'arranger_picked').elements[0].text === 'Picked: Mike Villegas', 'v71 Music: one engineer, no tick; Arranger a multi-select with "Picked: Mike Villegas" from one pick', v.blocks.map(b => b.block_id));
    const NT = await run(SI, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { actions: [{ action_id: 'more_eng_toggle', type: 'checkboxes', selected_options: [{ value: 'more' }] }],
      view: { id: 'V1', hash: 'h', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' }, blocks: (await step2(S('VO Recording', 'studio'))).blocks, state: { values: { engineer: { engineer_pick: tv('U1') } } } } } } }] });
    const nv = NT[0].json.view, nm = blk(nv, 'more_eng');
    ok(NT[0].json.ok && nm && nm.element.type === 'multi_static_select' && nv.blocks.indexOf(nm) === nv.blocks.findIndex(b => b.block_id === 'more_eng_toggle') + 1 && !nm.element.options.some(o => o.value === 'U1' || o.value === 'none'),
      'v71: ticking opens "More engineers" under it (everyone but the engineer picked)', nv.blocks.map(b => b.block_id));
    const NT2 = await run(SI, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { actions: [{ action_id: 'more_eng_toggle', type: 'checkboxes', selected_options: [] }],
      view: { id: 'V1', hash: 'h', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' }, blocks: nv.blocks, state: { values: {} } } } } }] });
    ok(!blk(NT2[0].json.view, 'more_eng'), 'v71: unticked -> More engineers goes');
  }
  v = await step2(S('Localization Dubbing', 'loc'));
  ok(blk(v, 'engineer').element.type === 'static_select', 'Localization: one engineer, the dropdown as before');

  console.log('Book a room, Read Step 2: two engineers and an arranger');
  const read2 = async (vv, s) => j1(SI, 'Read Step 2', [], { 'Check Signature': [{ json: { user: 'U1', channel: 'D1' } }], 'Read Cache 3': cacheRow, 'Timings 2': [],
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', blocks: [], private_metadata: JSON.stringify(Object.assign({ when: 'x', label: s.purpose }, s)), state: { values: vv } } } } }] });
  let r = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'kuba' } }, client: { client_in: { value: 'Jem Lim' } },
    engineer: { engineer_pick: ms(['U1', 'U5']) }, arranger: { arranger_pick: ms(['U6']) } }, S('Music Recording', 'studio'));
  ok(r.valid && r.calTitle === 'KUBA / Jem Lim / HL AEG x MV', 'the title: "KUBA / Jem Lim / HL AEG x MV"', { v: r.valid, t: r.calTitle, e: r.answer && r.answer.errors });
  ok(/^Engineer: Howard Luistro, Elijah Gan \| Arranger: Mike Villegas/.test(r.prep.description) && r.prep.engineer === 'Howard Luistro, Elijah Gan', 'the event: "Engineer: Howard Luistro, Elijah Gan | Arranger: Mike Villegas"', r.prep.description);
  ok(r.team.split(' ').sort().join() === 'U1,U5,U6' && r.engineerId === 'U1,U5' && r.again.en === 'U1,U5', 'team: all three; the saved answers keep both engineers', { team: r.team, en: r.engineerId });
  const r1 = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'kuba' } }, engineer: { engineer_pick: ms(['U1']) } }, S('VO Recording', 'studio'));
  ok(r1.valid && r1.calTitle === 'KUBA / HL' && /^Engineer: Howard Luistro/.test(r1.prep.description) && r1.team === 'U1', 'one engineer -> "KUBA / HL", as before', { t: r1.calTitle, d: r1.prep.description });
  if (V71) { const r2 = await read2({ room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'kuba' } }, engineer: { engineer_pick: tv('U1') }, more_eng: { more_eng_pick: ms(['U5']) } }, S('VO Recording', 'studio'));
    ok(r2.valid && r2.calTitle === 'KUBA / HL AEG' && r2.engineerId === 'U1,U5' && r2.team.split(' ').sort().join() === 'U1,U5' && /^Engineer: Howard Luistro, Elijah Gan/.test(r2.prep.description),
      'v71: Engineer Howard + More engineers Elijah -> "KUBA / HL AEG", both on the event and the team', { t: r2.calTitle, en: r2.engineerId, d: r2.prep.description }); }
  const rl = await read2({ room: { room_radio: tv('Studio 1') }, code: { code_in: { value: 'NET-KUBA' } }, engineer: { engineer_pick: tv('U3') } }, S('Localization Dubbing', 'loc'));
  ok(rl.calTitle === 'NET-KUBA / JT', 'Localization (one dropdown) -> "NET-KUBA / JT", as before', rl.calTitle);

  console.log('Book Session v128: every name checked, the title rewritten');
  const CC = BS.nodes.find(n => n.name === 'Check Conflicts').parameters.jsCode, STAFF = bookers.map(b => b.fields);
  const refRooms = FX.rooms.map(x => ({ id: x.id, name: x.fields['Room Name'], vocalBooth: x.fields['Vocal Booth'] === true, booth: x.fields['Vocal Booth'] === true, common: /Likha|Katha|Salin|Lobby/.test(x.fields['Room Name']) }));
  const refTypes = sessionTypes.map(t => ({ type: t.fields.Type, priority: [].concat(t.fields.Priority || []), last: [], roles: [].concat(t.fields['Engineer Role Required'] || []) }));
  const cc = REQ => { const outs = { 'When Executed by Another Workflow': [Object.assign({ staff_data: JSON.stringify(STAFF) }, REQ)], 'Get Events In Window': [{ items: [] }], 'All Bookers': STAFF.map(f => ({ fields: f })),
      'Client Cache': [{ use: true, gc: [], al: [], an: [], none: true }] };
    const $ = n => ({ first: () => ({ json: (outs[n] || [{}])[0] }), all: () => (outs[n] || []).map(j => ({ json: j })) });
    return new Function('$', '$input', CC)($, { first: () => ({ json: { items: [] } }), all: () => [{ json: { items: [] } }] })[0].json; };
  const REQ = (summary, engineer, desc, st) => ({ confirmed: true, mode: 'book', session_type: st || 'VO Recording', rooms: 'Studio 7', summary, engineer, description: desc + ' | Booked by: Howard Luistro | ref: U1',
    start_iso: '2026-11-12T13:00:00+08:00', end_iso: '2026-11-12T16:00:00+08:00', department: 'Audio Post', room_override: true, client: '', reference_data: JSON.stringify({ rooms: refRooms, types: refTypes }) });
  let c = cc(REQ('KUBA / HL AEG', 'Howard Luistro, Elijah Gan', 'Engineer: Howard Luistro, Elijah Gan'));
  ok(c.verdict === 'CLEAR' && c.final_summary === 'KUBA / HL AEG' && /^Engineer: Howard Luistro, Elijah Gan/.test(c.final_description), 'two engineers -> CLEAR, "KUBA / HL AEG", both on the event', { v: c.verdict, r: c.reason, h: c.human, t: c.final_summary, d: c.final_description });
  c = cc(REQ('KUBA / HL x MV', 'Howard, Eli', 'Engineer: Howard, Eli | Arranger: Mike', 'Music Recording'));
  ok(c.verdict === 'CLEAR' && c.final_summary === 'KUBA / HL AEG x MV' && /Engineer: Howard Luistro, Elijah Gan \| Arranger: Mike Villegas/.test(c.final_description), 'nicknames -> the full names, the initials rewritten: "KUBA / HL AEG x MV"', { v: c.verdict, r: c.reason, h: c.human, t: c.final_summary, d: c.final_description });
  c = cc(REQ('KUBA / HL XX', 'Howard Luistro, Nobody Here', 'Engineer: Howard Luistro, Nobody Here'));
  ok(c.verdict === 'REJECTED' && c.reason === 'ENGINEER_UNKNOWN' && c.given === 'Nobody Here', 'one name not on the staff list -> refused (ENGINEER_UNKNOWN), as for one engineer', { v: c.verdict, r: c.reason, g: c.given });
  c = cc(REQ('KUBA / HL', 'Howard Luistro', 'Engineer: Howard Luistro'));
  ok(c.verdict === 'CLEAR' && c.final_summary === 'KUBA / HL', 'one engineer -> as before');
  c = cc(Object.assign(REQ('KUBA / Howard and Eli', '', ''), { engineer: '' }));
  ok(c.reason === 'TITLE_INITIALS', 'a name in the initials place is still refused (TITLE_INITIALS)', c.reason);

  console.log('Notices: each engineer and arranger');
  const nb = (await run(SI, 'Booked Notices', [{ json: {} }], { 'Read Step 2': [{ json: Object.assign({}, r, { s: Object.assign({}, r.s, { kind: 'studio' }) }) }], 'Check Signature': [{ json: { user: 'U9', channel: 'D1' } }],
    'Read Cache 4': cacheRow, 'Read Cache 3': cacheRow, 'Read Cache': cacheRow, 'After Book': [{ json: { ok: true, card: '✅ *Booked.*\n\n*KUBA*', blocks: [] } }], 'Show Booked': [{ json: { ok: true } }],
    'Post Book Result': [{ json: { ok: true } }] }).catch(e => ({ err: String(e) }))) || [];
  const to = [].concat(nb).map(x => (x && x.json && x.json.channel) || '').filter(Boolean);
  ok(!nb.err && to.slice().sort().join() === 'U5,U6', 'Booked by Howard: a notice to Elijah (the other engineer) and Mike (the arranger) - not to Howard himself', { to, err: nb.err });

  console.log('Change: the people kept, changed, told');
  const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
  let rc;
  if (!V71) {
    const bk = { id: 'e1', d: '2026-11-12', s: '13:00', e: '16:00', r: 'Studio 7', t: 'KUBA / Jem Lim / HL AEG x MV', st: 'Music Recording' };
    const cv = (await j1(SI, 'Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(bk) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
    const de = blk(cv, 'det_engineer'), da = blk(cv, 'det_arranger');
    ok(de && de.element.type === 'multi_static_select' && (de.element.initial_options || []).map(o => o.value).sort().join() === 'U1,U5' && da && (da.element.initial_options || []).map(o => o.value).join() === 'U6',
      'Change opens with Howard + Elijah as engineers, Mike as arranger (from "HL AEG x MV")', { de: de && de.element, da: da && da.element.initial_options });
    rc = await j1(SI, 'Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata,
      state: { values: { date: { date_pick: { selected_date: '2026-11-12' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 7') },
        det_project: { det_project_in: { value: 'KUBA' } }, det_client: { det_client_in: { value: 'Jem Lim' } }, det_engineer: { det_engineer_pick: ms(['U1', 'U7']) }, det_arranger: { det_arranger_pick: ms(['U6']) } } } } } } }], 'Read Cache 10': cacheRow });
    ok(rc.newTitle === 'KUBA / Jem Lim / HL DR x MV' && rc.newDetails && rc.newDetails.Engineer === 'Howard Luistro, Daryl Reyes' && rc.newDetails.team.split(' ').sort().join() === 'U1,U6,U7',
      'Elijah swapped for Daryl -> "KUBA / Jem Lim / HL DR x MV", Engineer: Howard Luistro, Daryl Reyes, team: all three', { t: rc.newTitle, nd: rc.newDetails, e: rc.answer && rc.answer.errors });
    ok(rc.oldTeam.sort().join() === 'U1,U5,U6', 'who was on it before: Howard, Elijah, Mike (each one id)', rc.oldTeam);
  } else {
    const bk = { id: 'e1', d: '2026-11-12', s: '13:00', e: '16:00', r: 'Studio 7', t: 'KUBA / Jem Lim / HL AEG', st: 'VO Recording' };
    const cv = (await j1(SI, 'Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(bk) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
    const de = blk(cv, 'det_engineer'), dm = blk(cv, 'det_more_eng'), dt = blk(cv, 'more_eng_c_toggle');
    ok(de && de.element.type === 'static_select' && de.element.initial_option.value === 'U1' && dt && (dt.elements[0].initial_options || []).length === 1 && dm && (dm.element.initial_options || []).map(o => o.value).join() === 'U5',
      'v71 Change opens with Howard as the engineer, the box ticked, Elijah under More engineers (from "HL AEG")', cv.blocks.map(b => b.block_id));
    rc = await j1(SI, 'Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata,
      state: { values: { date: { date_pick: { selected_date: '2026-11-12' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 7') },
        det_project: { det_project_in: { value: 'KUBA' } }, det_client: { det_client_in: { value: 'Jem Lim' } }, det_engineer: { det_engineer_pick: tv('U1') }, det_more_eng: { more_eng_c_pick: ms(['U7']) } } } } } } }], 'Read Cache 10': cacheRow });
    ok(rc.newTitle === 'KUBA / Jem Lim / HL DR' && rc.newDetails && rc.newDetails.Engineer === 'Howard Luistro, Daryl Reyes' && rc.newDetails.team.split(' ').sort().join() === 'U1,U7',
      'v71: Elijah swapped for Daryl under More engineers -> "KUBA / Jem Lim / HL DR", Engineer: Howard Luistro, Daryl Reyes', { t: rc.newTitle, nd: rc.newDetails, e: rc.answer && rc.answer.errors });
    ok(rc.oldTeam.sort().join() === 'U1,U5', 'who was on it before: Howard, Elijah', rc.oldTeam);
  }
  const cn = (await run(SI, 'Change Notices', [{ json: {} }], { 'Read Change': [{ json: rc }], 'After Move': [{ json: { ok: true, card: '✅ *Changed.*\n\n*KUBA*', nb: null } }], 'Read Cache 7': cacheRow }).catch(e => [{ json: { err: String(e) } }])) || [];
  ok(JSON.stringify(cn).indexOf('U7') !== -1 || JSON.stringify(cn).indexOf('U08V3CKDGJF') !== -1, 'Change Notices: Daryl (added) is told', JSON.stringify(cn).slice(0, 300));

  console.log('My bookings: "You’re engineering" for the second engineer');
  const W = { user: 'U5', start: '2026-11-12', end: '2026-11-19', channel: 'D5', ts: '' };
  const items = [{ id: 'e1', summary: 'KUBA / Jem Lim / HL AEG x MV', start: { dateTime: '2026-11-12T13:00:00+08:00' }, end: { dateTime: '2026-11-12T16:00:00+08:00' },
    description: 'Engineer: Howard Luistro, Elijah Gan | Arranger: Mike Villegas | Booked by: Howard Luistro | ref: U1 | team: U1 U5 U6', location: 'Studio 7' }];
  const rmb = await j1(SI, 'Render My Bookings', [{ json: { items } }], { 'My Window': [{ json: W }], 'Read Cache 5': cacheRow, 'Read Cache': cacheRow, 'Read Cache 4': cacheRow, 'Read Cache 6': cacheRow });
  ok(/You’re engineering/.test(JSON.stringify(rmb.blocks)), 'Elijah (the second engineer) sees "You’re engineering"', JSON.stringify(rmb.blocks).slice(0, 400));

  console.log('Reminders v10 / Request Messages v7: the Engineer line as a list');
  const brJs = RM.nodes.find(n => n.name === 'Build Reminders').parameters.jsCode;
  ok(/\]\.flatMap\(x => String\(x \|\| ''\)\.split\(\/\\s\*,\\s\*\/\)\)\.map\(byName\)/.test(brJs), 'Reminders: every name on the Engineer / Arranger line looked up');
  const rqJs = RQ.nodes.find(n => n.name === 'Render').parameters.jsCode;
  ok(/const _named = \[\]\.concat\(_engL\.map/.test(rqJs) && /name: _nameAt\[i\], as: _named\[i\]/.test(rqJs), 'Request Messages: one role and name per person, in team: order');
  // v72 (Howard, 6 Nov): "Multiple engineers"; "+ Multiple studios" behind a "Multiple studios" tick
  if (/v72 \(Howard, 6 Nov\)/.test(JSON.stringify(SI.nodes))) {
    console.log('v72: the Multiple studios tick');
    const FREE = ['Studio 7', 'Studio 8', 'Studio 1', 'Studio 2', 'Studio F'];
    let w = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio 8'], free_rooms: FREE });
    const t = blk(w, 'more_rooms_toggle'), o = t && t.elements[0].options[0];
    ok(t && o.text.text === 'Multiple studios' && /^mr:/.test(o.value) && o.value.length <= 150 && !t.elements[0].initial_options && !blk(w, 'more_rooms'), 'step 2: "Multiple studios" unticked, no list', w.blocks.map(b => b.block_id));
    ok(blk(w, 'more_eng_toggle').elements[0].options[0].text.text === 'Multiple engineers', 'the engineers tick reads "Multiple engineers"');
    w = await step2(S('VO Recording', 'studio', { pre: { r: 'Studio 7', mr: 'Studio 8' } }), { free_priority: ['Studio 7', 'Studio 8'], free_rooms: FREE });
    ok((blk(w, 'more_rooms_toggle').elements[0].initial_options || []).length === 1 && (blk(w, 'more_rooms').element.initial_options || []).map(x => x.value).join() === 'Studio 8', 'a saved / typed second studio -> ticked, Studio 8 picked');
    const tog = async (blocks, sel) => (await run(SI, 'Note Toggle', [], { 'Read Request': [{ json: { payload: { actions: [{ action_id: 'more_rooms_toggle', type: 'checkboxes', selected_options: sel }],
      view: { id: 'V1', hash: 'h', callback_id: 'book_step2', title: { type: 'plain_text', text: 'Book a room' }, blocks, state: { values: {} } } } } }] }))[0].json;
    const w0 = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio 8'], free_rooms: FREE });
    let nt = await tog(w0.blocks, [blk(w0, 'more_rooms_toggle').elements[0].options[0]]);
    const ml = blk(nt.view, 'more_rooms');
    ok(nt.ok && ml && ml.label.text === 'More studios' && ml.element.action_id === 'more_rooms_pick' && ml.element.options.map(x => x.value).indexOf('Studio 8') !== -1
       && nt.view.blocks.indexOf(ml) === nt.view.blocks.findIndex(b => b.block_id === 'more_rooms_toggle') + 1, 'ticked -> "More studios" opens under it (the studios free then)', ml && ml.element.options.map(x => x.value));
    nt = await tog(nt.view.blocks, []);
    ok(!blk(nt.view, 'more_rooms'), 'unticked -> the list goes');
    const wm = await step2(S('Meeting', 'meeting'), { free_rooms: ['Likha', 'Katha', 'Salin', 'Studio 7'], free_priority: ['Likha', 'Katha'] });
    const tm = blk(wm, 'more_rooms_toggle');
    ok(tm && tm.elements[0].options[0].text.text === 'Multiple rooms' && /^mm:/.test(tm.elements[0].options[0].value), 'a meeting: "Multiple rooms"', wm.blocks.map(b => b.block_id));
    const chk2 = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
    const bk2 = { id: 'e2', d: '2026-11-12', s: '13:00', e: '16:00', r: 'Studio 7, Studio 8', t: 'KUBA / HL', st: 'VO Recording' };
    const cv2 = (await j1(SI, 'Build Change', [], { 'Check Signature': [chk2], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(bk2) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
    ok((blk(cv2, 'more_rooms_c_toggle').elements[0].initial_options || []).length === 1 && (blk(cv2, 'studios_c').element.initial_options || []).map(x => x.value).join() === 'Studio 8', 'Change on Studio 7 + 8: ticked, Studio 8 picked', cv2.blocks.map(b => b.block_id));
    const rc2 = await j1(SI, 'Read Change', [], { 'Check Signature': [chk2], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv2.private_metadata,
      state: { values: { date: { date_pick: { selected_date: '2026-11-12' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 7') },
        more_rooms_c_toggle: { more_rooms_c_toggle: { selected_options: [] } } } } } } } }], 'Read Cache 10': cacheRow });
    ok(rc2.newRooms === 'Studio 7' && rc2.roomChanged, 'Change: unticked -> Studio 8 taken off (the booking is Studio 7 only)', { r: rc2.newRooms, c: rc2.roomChanged, e: rc2.answer && rc2.answer.errors });
  }
  // main v291 (Howard's Slack test, 6 Nov 4:12 PM): several engineers typed fill the form
  const MAINF = process.argv[6] || (fs.existsSync('workflows/project-jessie-v291.json') ? 'workflows/project-jessie-v291.json' : '');
  const MAIN = MAINF ? JSON.parse(fs.readFileSync(MAINF, 'utf8')) : null;
  if (MAIN && /v291 \(Howard, 6 Nov/.test(JSON.stringify(MAIN.nodes))) {
    console.log('main v291: several engineers typed');
    const jsOf = n => MAIN.nodes.find(x => x.name === n).parameters.jsCode;
    const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
    const STF = bookers.map(b => b.fields);
    const offer = async text => {
      const O = { 'Slack Trigger': [{ json: { text, user: 'U1', ts: '100.1', channel: 'D1' } }], 'Get Recent Messages': [{ json: { ts: '100.1', text, user: 'U1' } }], 'Gate Context': [{ json: { epoch: '', gate: {} } }],
        'Get Booker': [{ json: { fields: STF[0] } }], 'All Bookers': STF.map(f => ({ json: { fields: f } })), 'All Rooms': FX.rooms.map(r => ({ json: r })), 'All Session Types': sessionTypes.map(t => ({ json: t })) };
      const bf = new Function('$', '$input', jsOf('Booked For'))($f(O), { first: () => ({ json: {} }) })[0].json;
      Object.assign(O, { 'Booked For': [{ json: bf }], 'Gate Context': [{ json: { datesInMessage: '2026-11-07', confirmed: false, gate: {}, todayIso: '2026-11-06' } }], 'Get Recent Messages': [] });
      const r = await new Function('$', '$input', 'return (async function(){' + jsOf('Form Offer') + '\n})();')($f(O), { first: () => ({ json: {} }), all: () => [{ json: {} }] });
      return { bf, F: r[0].json.formOffer }; };
    let o = await offer('book a vo recording tomorrow 2-4pm for studio 7, engineers howard and eli. project two-eng test');
    ok(o.F.prefill.en === 'U1,U5' && /Engineer: Howard Luistro, Elijah Gan/.test(o.F.text), '"engineers howard and eli" -> both pre-filled, "Engineer: Howard Luistro, Elijah Gan"', { en: o.F.prefill.en, t: o.F.text, bf: o.bf.engineers });
    o = await offer('book studio 7 tomorrow 2-4pm vo recording, engineer: Howard, Drey');
    ok(o.F.prefill.en === 'U1,U7', '"engineer: Howard, Drey" -> Howard + Daryl', o.F.prefill.en);
    o = await offer('book studio f tomorrow 2-4pm music recording, engineers ana and eli, arrangers mike');
    ok(o.F.prefill.en === 'U8,U5' && o.F.prefill.ar === 'U6', '"engineers ana and eli, arrangers mike" -> two engineers, one arranger', { F: o.F, bf: [o.bf.engineers, o.bf.engineer, o.bf.arranger] });
    o = await offer('book studio 7 tomorrow 2-4pm vo recording, engineer eli');
    ok(o.F.prefill.en === 'U5', '"engineer eli" -> Elijah only, as before', o.F.prefill.en);
    o = await offer('book studio 7 tomorrow 2-4pm vo recording, engineers howard and somebody new');
    ok(o.F.prefill.en !== 'U1,U5' && !/,/.test(String(o.F.prefill.en || '')), 'a name nobody on staff has in the list -> not a list (as before)', o.F.prefill.en);
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('  FAIL  crashed: ' + (e && e.stack || e)); process.exit(1); });
