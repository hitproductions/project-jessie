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
  let v = await step2(S('VO Recording', 'studio'));
  let e = blk(v, 'engineer');
  ok(e && e.element.type === 'multi_static_select' && e.dispatch_action === true && (e.element.initial_options || []).map(o => o.value).join() === 'U1' && !e.element.options.some(o => o.value === 'none'),
    'VO Recording: Engineer is a multi-select, you picked (as before), no "No engineer" option (a phone can clear it)', e && e.element);
  v = await step2(S('VO Recording', 'studio', { pre: { en: 'U1,U5' } }));
  ok((blk(v, 'engineer').element.initial_options || []).map(o => o.value).sort().join() === 'U1,U5' && /Picked: Elijah Gan, Howard Luistro/.test(JSON.stringify(v.blocks)), 'saved answers "U1,U5" -> both picked, "Picked: Elijah Gan, Howard Luistro"');
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
  const bk = { id: 'e1', d: '2026-11-12', s: '13:00', e: '16:00', r: 'Studio 7', t: 'KUBA / Jem Lim / HL AEG x MV', st: 'Music Recording' };
  const cv = (await j1(SI, 'Build Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { actions: [{ value: JSON.stringify(bk) }], container: { channel_id: 'D1', message_ts: '1' } } } }], 'Read Cache 6': cacheRow })).view;
  const de = blk(cv, 'det_engineer'), da = blk(cv, 'det_arranger');
  ok(de && de.element.type === 'multi_static_select' && (de.element.initial_options || []).map(o => o.value).sort().join() === 'U1,U5' && da && (da.element.initial_options || []).map(o => o.value).join() === 'U6',
    'Change opens with Howard + Elijah as engineers, Mike as arranger (from "HL AEG x MV")', { de: de && de.element, da: da && da.element.initial_options });
  const rc = await j1(SI, 'Read Change', [], { 'Check Signature': [chk], 'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: cv.private_metadata,
    state: { values: { date: { date_pick: { selected_date: '2026-11-12' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('16:00') }, room: { room_pick: tv('Studio 7') },
      det_project: { det_project_in: { value: 'KUBA' } }, det_client: { det_client_in: { value: 'Jem Lim' } }, det_engineer: { det_engineer_pick: ms(['U1', 'U7']) }, det_arranger: { det_arranger_pick: ms(['U6']) } } } } } } }], 'Read Cache 10': cacheRow });
  ok(rc.newTitle === 'KUBA / Jem Lim / HL DR x MV' && rc.newDetails && rc.newDetails.Engineer === 'Howard Luistro, Daryl Reyes' && rc.newDetails.team.split(' ').sort().join() === 'U1,U6,U7',
    'Elijah swapped for Daryl -> "KUBA / Jem Lim / HL DR x MV", Engineer: Howard Luistro, Daryl Reyes, team: all three', { t: rc.newTitle, nd: rc.newDetails, e: rc.answer && rc.answer.errors });
  ok(rc.oldTeam.sort().join() === 'U1,U5,U6', 'who was on it before: Howard, Elijah, Mike (each one id)', rc.oldTeam);
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
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('  FAIL  crashed: ' + (e && e.stack || e)); process.exit(1); });
