#!/usr/bin/env node
// Slack Interactions v39 (22 Oct, QA on mobile): every dropdown that can be "none" is required with "No booth / engineer / arranger"
// picked by default - a phone has no "Clear selection", and desktop no longer shows it either. Book and Change; Repeats' "Use the end date".
// Usage: node scripts/sim-v39-dropdowns.js [slack-interactions]
const path = require('path'); const P = path.join(__dirname, '..') + '/';
const si = require(P + (process.argv[2] || 'workflows/slack-interactions-v39.json'));
// v53 (28 Oct): the Vocal booth(s) is a multi-select - no "No booth" item; the picked booths read the same on either shape
const V53 = JSON.stringify(si.nodes).indexOf("label: pt('Vocal booths')") !== -1;
const bPick = bl => (bl && bl.element ? [].concat(bl.element.initial_options || (bl.element.initial_option ? [bl.element.initial_option] : [])) : []).map(o => o.value).filter(x => x !== 'none');
const FX = require(P + 'scripts/sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
const run = (name, input, outs) => new Function('$', '$input', 'return (async function(){' + si.nodes.find(x => x.name === name).parameters.jsCode + '\n})();')(
  n => { if (outs[n] === undefined) { const e = () => { throw new Error(n + ' not executed'); }; return { first: e, all: e }; } return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; },
  { first: () => input[0], all: () => input });
const ST = (t, roles, pri, req) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': req || '' } });
const types = [ST('VO Recording', ['Post Engineer'], ['r7']), ST('Music Mixing', ['Music Engineer', 'Music Arranger'], ['rf']), ST('Music Arranging', ['Music Arranger'], ['rf']),
  ST('Celebrity Recording', ['Music Engineer', 'Post Engineer', 'Music Arranger'], ['rf'], 'Large'), ST('Localization Dubbing', ['Loc Engineer'], ['r1'], 'Separate vocal booth')];
const B = (id, name, slack, info) => ({ id, fields: { Name: name, Initials: name.split(' ').map(x => x[0]).join(''), 'Slack User ID': slack, Info: info, Department: ['Music'] } });
const bookers = [B('b1', 'Howard Luistro', 'U1', 'Post Engineer'), B('b2', 'Rico Gonzales', 'U2', 'Music Engineer'), B('b3', 'Joaquin Santos', 'U3', 'Music Arranger'), B('b4', 'Lea Lim', 'U4', 'Loc Engineer')];
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: types, bookers }) } }];
const kind = t => /^Localization/.test(t) ? 'loc' : 'studio';
const step2 = async (t, me, free) => (await run('Build Step 2', [{ json: { status: 'OK', free_priority: free, free_last_resort: [], busy: [] } }],
  { 'Read Step 1': [{ json: { s: { date: '2027-10-25', t0: '10:00', t1: '12:00', purpose: t, kind: kind(t), requester: me, channel: 'D1', ext: 'x' } } }], 'Read Cache 2': cache, 'Loc Projects 2': [] }))[0].json.view;
const blk = (v, re) => v.blocks.find(b => re.test(b.block_id || ''));
const last = b => b.element.options[b.element.options.length - 1].value;
(async () => {
  if (JSON.stringify(si.nodes).indexOf('required (no Slack') === -1) { console.log('0 ok, 0 failed (an older build: v39 not in it)'); process.exit(0); }
  console.log('Book');
  let v = await step2('Music Mixing', 'U3', ['Studio F']);
  let e = blk(v, /^engineer$/), a = blk(v, /^arranger$/);
  ok(!e.optional && last(e) === 'none' && e.element.initial_option.value === 'none', 'Music Mixing by an arranger: Engineer required, "No engineer" picked (last choice)', e);
  ok(!a.optional && last(a) === 'none' && a.element.initial_option.value === 'U3', 'Arranger required, set to them, "No arranger" there to pick');
  v = await step2('Music Mixing', 'U1', ['Studio F']);
  ok(blk(v, /^arranger$/).element.initial_option.value === 'none' && blk(v, /^engineer$/).element.initial_option.value === 'U1', 'by an engineer: Engineer them, Arranger "No arranger"');
  v = await step2('Music Arranging', 'U1', ['Studio F']);
  a = blk(v, /^arranger$/);
  ok(!a.optional && !a.element.options.some(o => o.value === 'none') && !a.element.initial_option && !blk(v, /^engineer$/), 'an arranger-only type: Arranger required, no "No arranger", nothing picked');
  v = await step2('VO Recording', 'U1', ['Studio 7']);
  e = blk(v, /^engineer$/);
  ok(!e.optional && !e.element.options.some(o => o.value === 'none') && e.element.initial_option.value === 'U1', 'VO Recording: Engineer required, no "No engineer" (as before)');
  let bt = blk(v, /^booth~/);
  ok(bt && (V53 ? bt.optional && bt.element.type === 'multi_static_select' && !bPick(bt).length && !bt.element.options.some(o => o.value === 'none') : !bt.optional && last(bt) === 'none' && bt.element.initial_option.value === 'none'),
     V53 ? 'VO Recording: Vocal booths optional, nothing picked, no "No booth" item (v53)' : 'VO Recording: Vocal booth required, "No booth" picked', bt && bt.element);
  v = await step2('Localization Dubbing', 'U4', ['Studio 1']);
  bt = blk(v, /^booth~/);
  ok(bt && !bt.optional && !bt.element.options.some(o => o.value === 'none') && bPick(bt).length === 1, 'Localization Dubbing (a booth is needed): the usual booth, no "No booth"');
  ok(!v.blocks.some(b => b.type === 'input' && b.optional && b.element && b.element.type === 'static_select' && b.block_id !== 'room_other'), 'no optional single dropdown left in step 2 (but Choose a different room)');
  console.log('Read Step 2: "none" is empty');
  v = await step2('Music Mixing', 'U3', ['Studio F']);
  const vals = { room: { room_radio: { selected_option: { value: 'Studio F' } } }, engineer: { engineer_pick: { selected_option: { value: 'none' } } }, arranger: { arranger_pick: { selected_option: { value: 'U3' } } },
    project: { project_in: { value: 'song' } } };
  const r2 = (await run('Read Step 2', [], { 'Check Signature': [{ json: { user: 'U3' } }], 'Read Cache 3': cache, 'Timings 2': [],
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', blocks: v.blocks, private_metadata: v.private_metadata, state: { values: vals } } } } }] }))[0].json;
  ok(r2.valid && r2.engineerId === '' && r2.arrangerId === 'U3' && /no engineer/.test(r2.prep.requester_text), '"No engineer" + an arranger -> booked with the arranger only');
  console.log('Change');
  const bc = async bk => (await run('Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify(bk) }], container: { channel_id: 'D1', message_ts: '1' } } } }] }))[0].json.view;
  let cv = await bc({ id: 'e1', d: '2027-10-25', s: '10:00', e: '12:00', r: 'Studio F, Studio A', t: 'SONG / RG', st: 'Music Mixing' });
  const bcB = blk(cv, /^booth_c$/), de = blk(cv, /^det_engineer$/), da = blk(cv, /^det_arranger$/);
  ok(bcB && bPick(bcB).join() === 'Studio A' && (V53 ? bcB.optional && !bcB.element.options.some(o => o.value === 'none') : !bcB.optional && last(bcB) === 'none'),
     V53 ? 'Change: Vocal booths, the booking\'s picked, can be emptied (v53)' : 'Change: Vocal booth required, set to the booking\'s, "No booth" there', bcB && bcB.element);
  ok(de && !de.optional && de.element.initial_option && last(de) === 'none', 'Change: Engineer (either) required, "No engineer" there', de && de.element.initial_option);
  ok(da && !da.optional && da.element.initial_option.value === 'none', 'Change: Arranger required, "No arranger" when there is none');
  cv = await bc({ id: 'e2', d: '2027-10-25', s: '10:00', e: '12:00', r: 'Studio 7', t: 'SPOT / HL', st: 'VO Recording' });
  ok(blk(cv, /^booth_c$/) && (V53 ? !bPick(blk(cv, /^booth_c$/)).length : blk(cv, /^booth_c$/).element.initial_option.value === 'none'), 'Change: a VO Recording with no booth -> Vocal booth offered, "No booth" picked');
  console.log('Repeats');
  const b1 = si.nodes.find(n => n.name === 'Build Step 1').parameters.jsCode;
  ok(/counts\.push\(\{ text: pt\('Use the end date'\), value: '0' \}\)/.test(b1), 'How many times: "Use the end date" (a phone cannot clear a number)');
  const rs1 = si.nodes.find(n => n.name === 'Read Step 1').parameters.jsCode;
  ok(/const count = Number\(/.test(rs1) && /const until = count \? '' :/.test(rs1), 'Read Step 1: "0" is no number -> Or until is used (as before)');
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
