#!/usr/bin/env node
// Round 11 offline (Slack Interactions v29, 20 Oct): faster redraws + clean-up. The Localization Projects table read only when it is
// used (Loc Needed? / Code Typed?), a room tick with nothing to redraw answers nothing, the department from the people picked (no
// Department field - Howard, 19 Oct), the unused project-code search gone, an unsigned probe refused quietly.
// Usage: node scripts/sim-round-11.js [slack-interactions v29]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v29.json', 'utf8'));
const FX = require('./sim-fixture-rooms.js');
if (!/v29: no Department field/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (round 11 is v29 on; this build is older)'); process.exit(0); }
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const node = n => si.nodes.find(x => x.name === n);
const NOTRUN = '__not_run__';
async function run(name, input, outs) {
  const js = node(name).parameters.jsCode;
  // a node that did not run this time throws when read, as n8n does
  const $ = n => { if (outs[n] === NOTRUN) { const e = () => { throw new Error('Node \'' + n + '\' hasn\'t been executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await run(...a))[0].json;
const ifExpr = (name, outs) => { const e = node(name).parameters.conditions.conditions[0].leftValue.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
  const $ = n => ({ first: () => (outs[n] || [])[0] }); return new Function('$', 'return (' + e + ');')($); };

const ST = (t, pri, roles) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': '' } });
const sessionTypes = [ST('Celebrity Recording', ['rf', 'rc'], ['Music Engineer', 'Post Engineer', 'Music Arranger']), ST('Van Recording', ['sm'], ['Post Engineer', 'Music Arranger']),
  ST('VO Recording', ['r7'], ['Post Engineer']), ST('Localization Dubbing', ['r1', 'r2'], ['Loc Engineer']), ST('Meeting', ['lk', 'sa', 'ka'], ['None'])];
const rooms = FX.rooms.concat([{ id: 'sm', fields: { 'Room Name': 'Studio M', 'Room Type': ['Van'] } }]);
const B = (id, name, ini, slack, info, dept) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: dept } });
const bookers = [B('b1', 'Tara Lim', 'TL', 'U026N6E1R', 'Post Engineer, Goes by Tara.', ['Audio Post']), B('b2', 'Joaquin Santos', 'JS', 'U9', 'Music Arranger', ['Music']),
  B('b3', 'Camy Caridad', 'CC', 'U5', 'Coordinator', ['Marketing']), B('b4', 'Daryl Reyes', 'DR', 'U2', 'Music Engineer, Post Engineer. Goes by Daryl, Drey.', ['Music']),
  B('b5', 'Jetrho Ty', 'JT', 'U3', 'Loc Engineer', ['Localization'])];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes, bookers }) } }];
const LOC = [{ json: { id: 'p1', 'Project Code': 'NET-MALAS', 'Project Title': 'BAD DAY', 'Client Name': 'NETFLIX', Recordist: ['Jetrho'], Mixer: ['Via'] } }];
const tv = v => ({ selected_option: { value: v } });
const S = (purpose, kind, req) => ({ date: '2027-10-19', t0: '11:30', t1: '12:30', purpose, kind, requester: req || 'U026N6E1R', channel: 'D1', ext: 'x', msg: { ch: 'D1', ts: '1.1' } });
const M = (purpose, kind, req) => Object.assign(S(purpose, kind, req), { label: purpose, when: 'Tuesday, Oct 19 · 11:30 AM–12:30 PM' });
const blk = (v, id) => v.blocks.find(b => b.block_id === id);

(async () => {
  console.log('1: the Localization Projects table only when it is used');
  const C = si.connections;
  const nx = n => ((C[n] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
  ok(nx('Read Cache 2') === 'Loc Needed?' && nx('Loc Needed?') === 'Loc Projects 2 | To Room Availability' && nx('Loc Projects 2') === 'To Room Availability', 'Find rooms: Read Cache 2 -> Loc Needed? -> Loc Projects 2 (yes) or To Room Availability (no)', [nx('Read Cache 2'), nx('Loc Needed?')]);
  ok(nx('Read Cache 9') === 'Code Typed?' && nx('Code Typed?') === 'Loc Projects 9 | Note Toggle' && nx('Loc Projects 9') === 'Note Toggle', 'a redraw: Read Cache 9 -> Code Typed? -> Loc Projects 9 (yes) or Note Toggle (no)');
  for (const k of ['loc', 'studio', 'meeting', 'booth', 'atmos', 'post']) ok(ifExpr('Loc Needed?', { 'Read Step 1': [{ json: { s: { kind: k } } }] }) === (k === 'loc'), 'Loc Needed? for ' + k + ': ' + (k === 'loc'));
  for (const a of ['code_in', 'det_code_in', 'code_pick', 'room_radio', 'room_other_pick', 'repeat_toggle', 'purpose_pick', 'note_toggle'])
    ok(ifExpr('Code Typed?', { 'Read Request': [{ json: { payload: { actions: [{ action_id: a }] } } }] }) === /code/.test(a), 'Code Typed? for ' + a + ': ' + /code/.test(a));
  ok(ifExpr('Code Typed?', { 'Read Request': [{ json: { payload: {} } }] }) === false, 'Code Typed? with no action: false (no crash)');
  for (const n of ['Loc Needed?', 'Code Typed?']) ok(node(n).type === 'n8n-nodes-base.if' && !node(n).disabled, n + ' is an IF node, not deactivated');

  // Build Step 2 for a studio booking without the Loc Projects read (it did not run)
  const step2 = async (s, ra, loc) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cacheRow, 'Loc Projects 2': loc })).view;
  let v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7'] }, NOTRUN);
  ok(v && v.blocks.some(b => /^room/.test(b.block_id || '')) && blk(v, 'project'), 'VO Recording, Loc Projects 2 not run -> step 2 as before (room list, project)');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2'] }, LOC);
  ok(v && blk(v, 'code'), 'Localization Dubbing, Loc Projects 2 ran -> the project code box');
  v = await step2(S('Localization Dubbing', 'loc'), { free_priority: ['Studio 1', 'Studio 2'] }, NOTRUN);
  ok(v && blk(v, 'code'), 'Localization Dubbing, the read failed -> still drawn (the code is checked again on Enter)');

  console.log('2: a room tick with nothing to redraw');
  const toggle = async (view, action, extra, state, loc) => run('Note Toggle', [], { 'Read Request': [{ json: { payload: { view: Object.assign({ id: 'V1', hash: 'h' }, view, { state: { values: state || {} } }),
    actions: [Object.assign({ action_id: action }, extra || {})] } } }], 'Read Cache 9': cacheRow, 'Loc Projects 9': loc === undefined ? NOTRUN : loc });
  const vm = await step2(S('Meeting', 'meeting'), { free_priority: ['Likha', 'Salin', 'Katha'], free_other: ['Studio 5'] }, NOTRUN);
  ok(!vm.blocks.some(b => /^booth/.test(b.block_id || '')), 'a meeting has no booth on the form');
  let t = await toggle(vm, 'room_radio', { selected_option: { value: 'Salin' } }, { room: { room_radio: tv('Salin') } });
  ok(Array.isArray(t) && t.length === 0, 'a meeting: Salin ticked, nothing else picked -> no redraw (nothing sent to Slack)', t);
  t = await toggle(vm, 'room_radio', { selected_option: { value: 'Salin' } }, { room: { room_radio: tv('Salin') }, room_other: { room_other_pick: tv('Studio 5') } });
  ok(t.length === 1 && t[0].json.view.blocks.some(b => /^room_other~\d+$/.test(b.block_id || '')), 'a meeting: Salin ticked while Another room had Studio 5 -> redrawn, Another room cleared');
  v = await step2(S('VO Recording', 'studio'), { free_priority: ['Studio 7', 'Studio 8'], free_other: ['Studio 5'] }, NOTRUN);
  const md = v.private_metadata;
  ok(v.blocks.some(b => /^booth/.test(b.block_id || '')), 'VO Recording has a booth on the form');
  t = await toggle(v, 'room_radio', { selected_option: { value: 'Studio 8' } }, { room: { room_radio: tv('Studio 8') } });
  ok(t.length === 1 && t[0].json.view.blocks.some(b => /^booth~\d+$/.test(b.block_id || '')), 'VO Recording: Studio 8 ticked -> redrawn (the booth follows the room), as before');
  t = await toggle(Object.assign({}, v, { private_metadata: md }), 'room_radio', { selected_option: { value: 'Studio 8' } }, { room: { room_radio: tv('Studio 8') }, room_other: { room_other_pick: tv('Studio 5') } });
  ok(t.length === 1 && t[0].json.view.blocks.some(b => /^room_other~\d+$/.test(b.block_id || '')), 'Studio 8 ticked while Another room had Studio 5 -> redrawn, Another room cleared');
  t = await toggle(Object.assign({}, v, { private_metadata: md }), 'room_other_pick', { selected_option: { value: 'Studio 5' } }, { room: { room_radio: tv('Studio 8') }, room_other: { room_other_pick: tv('Studio 5') } });
  ok(t.length === 1 && t[0].json.view.blocks.some(b => /^room~\d+$/.test(b.block_id || '')), 'a room from Another room -> redrawn, the ticked one cleared (unchanged)');
  const vb = { blocks: v.blocks.concat([{ type: 'input', block_id: 'booth~1', optional: true, label: { type: 'plain_text', text: 'Booth' }, element: { type: 'static_select', action_id: 'booth_pick', options: [] } }]), private_metadata: md };
  t = await toggle(vb, 'room_radio', { selected_option: { value: 'Studio 8' } }, { room: { room_radio: tv('Studio 8') } });
  ok(t.length === 1, 'a booth on the form -> redrawn (the booth follows the room)');
  t = await toggle(Object.assign({}, v, { private_metadata: md }), 'room_radio', { selected_option: { value: '__other' } }, { room: { room_radio: tv('__other') } });
  ok(t.length === 1, 'an old form\'s "Another room…" option -> redrawn as before');
  t = await toggle(Object.assign({}, v, { private_metadata: md }), 'repeat_toggle', { selected_options: [{ value: 'on' }] }, {});
  ok(t.length === 1, 'Repeats ticked -> redrawn, without the Loc Projects read');
  const vc = { blocks: [{ type: 'input', block_id: 'code', dispatch_action: true, label: { type: 'plain_text', text: 'Project code' }, element: { type: 'plain_text_input', action_id: 'code_in' } }], private_metadata: '{}' };
  t = await toggle(vc, 'code_in', { value: 'net-malas' }, { code: { code_in: { value: 'net-malas' } } }, LOC);
  ok(t.length === 1 && /BAD DAY/.test(JSON.stringify(t[0].json.view.blocks)), 'a project code typed -> the project found (Loc Projects 9 read)', t[0] && t[0].json.view.blocks);

  console.log('3: the department from the people picked');
  ok(!blk(await step2(S('Celebrity Recording', 'studio'), { free_priority: ['Studio F'] }, NOTRUN), 'department'), 'Celebrity Recording - no Department field');
  ok(!blk(await step2(S('Van Recording', 'studio'), { free_priority: ['Studio M'] }, NOTRUN), 'department'), 'Van Recording - no Department field');
  const read2 = async (vv, meta) => j1('Read Step 2', [], { 'Check Signature': [{ json: { user: meta.requester } }], 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta), blocks: [], state: { values: vv } } } } }], 'Read Cache 3': cacheRow });
  const F = (eng, arr, extra) => Object.assign({ room: { room_radio: tv('Studio F') }, project: { project_in: { value: 'qatest' } } }, eng ? { engineer: { engineer_pick: tv(eng) } } : {}, arr ? { arranger: { arranger_pick: tv(arr) } } : {}, extra || {});
  const cases = [
    ['Celebrity, engineer Tara (Post Engineer)', F('U026N6E1R'), 'U026N6E1R', 'Audio Post'],
    ['Celebrity, booked by Camy (Marketing), engineer Tara', F('U026N6E1R'), 'U5', 'Audio Post'],
    ['Celebrity, arranger Joaquin', F('', 'U9'), 'U026N6E1R', 'Music'],
    ['Celebrity, arranger Joaquin + engineer Tara', F('U026N6E1R', 'U9'), 'U026N6E1R', 'Music'],
    ['Celebrity, engineer Daryl (Music and Post Engineer), booked by Tara (Audio Post)', F('U2'), 'U026N6E1R', 'Audio Post'],
    ['Celebrity, engineer Daryl, booked by Camy (Marketing) -> the type\'s first', F('U2'), 'U5', 'Music'],
    ['Celebrity, engineer Jetrho (Loc Engineer - not one of the type\'s)', F('U3'), 'U026N6E1R', 'Audio Post'],
    ['an old form (v28) still open: Department Music picked, engineer Tara', F('U026N6E1R', '', { department: { department_pick: tv('Music') } }), 'U026N6E1R', 'Music'],
  ];
  for (const [label, vals, req, want] of cases) {
    const r = await read2(vals, M('Celebrity Recording', 'studio', req));
    ok(r.valid && r.prep && r.prep.department === want, label + ' -> ' + want, { valid: r.valid, dept: r.prep && r.prep.department });
  }
  let r = await read2(Object.assign(F('U026N6E1R'), { room: { room_radio: tv('Studio M') } }), M('Van Recording', 'studio'));
  ok(r.valid && r.prep.department === 'Audio Post', 'Van Recording, engineer Tara -> Audio Post', r.prep && r.prep.department);
  r = await read2(Object.assign(F('', 'U9'), { room: { room_radio: tv('Studio M') } }), M('Van Recording', 'studio'));
  ok(r.valid && r.prep.department === 'Music', 'Van Recording, arranger Joaquin -> Music', r.prep && r.prep.department);
  const vo = await read2(Object.assign(F('U026N6E1R'), { room: { room_radio: tv('Studio 7') } }), M('VO Recording', 'studio'));
  ok(vo.valid && !vo.prep.department, 'VO Recording (one department) -> left to Book Session, as before', vo.prep && vo.prep.department);

  console.log('4: the unused project-code search');
  for (const n of ['Loc Projects S', 'Suggest Codes', 'Answer Suggest']) ok(!node(n), n + ' removed');
  const dangling = []; for (const [src, o] of Object.entries(C)) { if (!node(src)) dangling.push('from ' + src); for (const outs of (o.main || [])) for (const c of (outs || [])) if (!node(c.node)) dangling.push(src + ' -> ' + c.node); }
  ok(dangling.length === 0, 'no connection to or from a node that is gone', dangling);
  ok(!si.nodes.some(n => /\$\('(Loc Projects S|Suggest Codes|Answer Suggest)'\)/.test(JSON.stringify(n.parameters))), 'no node reads them');
  const route = async (payload) => (await j1('Check Signature', [{ json: { computed: 'abc' } }], { 'Read Request': [{ json: { sig: 'v0=abc', ts: String(Math.floor(Date.now() / 1000)), payload } }] })).route;
  ok(await route({ type: 'block_suggestion', action_id: 'code_pick' }) === 3, 'a block_suggestion (an old form) -> "other" (answered, nothing done)');
  const sw = node('Check Signature').parameters.jsCode.match(/const ROUTES = \{([^}]*)\}/)[1];
  const outs = (C['Route'] || C['Route Request'] || Object.values(C).find(o => (o.main || []).length > 10) || { main: [] }).main;
  ok(outs.length >= Math.max(...sw.match(/\d+/g).map(Number)) + 1, 'the router still has an output for every route');

  console.log('5: refusals');
  let x = await run('Report Refused', [], { 'Check Signature': [{ json: { sigOk: false, fresh: false, ageSec: null, rawSource: 'none', rawLength: 0 } }] });
  ok(Array.isArray(x) && x.length === 0, 'no Slack timestamp (curl, a link preview) -> refused quietly, no DM');
  x = await run('Report Refused', [], { 'Check Signature': [{ json: { sigOk: false, fresh: true, ageSec: 2, rawSource: 'rawBody', rawLength: 900, type: 'block_actions' } }] });
  ok(x.length === 1 && /did not match/.test(x[0].json.text), 'Slack-shaped but the signature did not match -> the tester is DM\'d, as before');
  x = await run('Report Refused', [], { 'Check Signature': [{ json: { sigOk: true, fresh: false, ageSec: 900, rawSource: 'rawBody', rawLength: 900 } }] });
  ok(x.length === 1 && /900 s/.test(x[0].json.text), 'a stale Slack timestamp -> DM\'d, as before');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
