#!/usr/bin/env node
// Slack Interactions v54 (Howard's Slack test of v53, 28 Oct): step 2 came back with a problem ("Did you mean …?") and the studios
// picked under "+ Multiple studios" were gone - formAgain kept typed text and single dropdowns only. Also every DM / Change path
// that redraws a form keeps every room, the Changed card shows every room, and a taken room among several is named.
//   node scripts/sim-picks-kept.js [slack-interactions v54]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v54.json', 'utf8'));
if (!/v54: \+ Multiple studios, Vocal booths, Holding rooms - picks kept/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (an older build: v54 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 600))); } };
const code = n => si.nodes.find(x => x.name === n).parameters.jsCode;
const run = async (name, input, outs) => { const $ = n => ({ first: () => { if (!(n in outs)) throw new Error('not run: ' + n); return outs[n][0]; }, all: () => outs[n] || [] });
  return new Function('$', '$input', 'return (async function(){' + code(name) + '\n})();')($, { first: () => input[0], all: () => input }); };
const j1 = async (...a) => ((await run(...a))[0] || {}).json;
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers: FX.bookers }) } }];
const opt = n => ({ text: { type: 'plain_text', text: n }, value: n }), ms = a => ({ type: 'multi_static_select', selected_options: a.map(opt) });
const picked = bl => bl && bl.element ? [].concat(bl.element.initial_options || []).map(o => o.value) : (bl ? [] : null);
const blkOf = (v, re) => (v.blocks || []).find(b => re.test(b.block_id || ''));

(async () => {
  console.log('Step 2 back with a problem (formAgain): multi-select picks kept');
  const S = { date: '2027-10-29', t0: '13:00', t1: '16:00', kind: 'studio', purpose: 'VO Recording', requester: 'U1', when: 'x' };
  const blocks = [{ type: 'actions', block_id: 'room', elements: [{ type: 'radio_buttons', action_id: 'room_radio', options: ['Studio 7', 'Studio F'].map(opt) }] },
    { type: 'input', block_id: 'booth~12', optional: true, label: { type: 'plain_text', text: 'Vocal booths' }, element: { type: 'multi_static_select', action_id: 'booth_pick', options: ['Studio A', 'Studio B', 'Studio D'].map(opt) } },
    { type: 'input', block_id: 'more_rooms', optional: true, label: { type: 'plain_text', text: '+ Multiple studios' }, element: { type: 'multi_static_select', action_id: 'more_rooms_pick', options: ['Studio 7', 'Studio 8', 'Studio F', 'Studio C'].map(opt) } },
    { type: 'input', block_id: 'holding', optional: true, label: { type: 'plain_text', text: 'Holding rooms' }, element: { type: 'multi_static_select', action_id: 'holding_pick', options: ['Katha', 'Likha'].map(opt) } },
    { type: 'input', block_id: 'project', label: { type: 'plain_text', text: 'Project title' }, element: { type: 'plain_text_input', action_id: 'project_in' } },
    { type: 'input', block_id: 'client', optional: true, label: { type: 'plain_text', text: 'Client' }, element: { type: 'plain_text_input', action_id: 'client_in' } }];
  const state = { room: { room_radio: { type: 'radio_buttons', selected_option: opt('Studio F') } }, 'booth~12': { booth_pick: ms(['Studio A', 'Studio B']) }, more_rooms: { more_rooms_pick: ms(['Studio 8', 'Studio C']) },
    holding: { holding_pick: ms(['Likha']) }, project: { project_in: { value: 'testing multiple - studios' } }, client: { client_in: { value: 'harold orozco' } } };
  const R2 = { viewId: 'V1', channel: 'U1', calTitle: 'X', rooms: 'Studio F, Studio 8, Studio C, Studio A, Studio B, Likha', again: { d: '2027-10-29' }, s: S };
  const outs = { 'Read Step 2': [{ json: R2 }], 'To Prepare': [{ json: {} }], 'Read Cache 2': cache, 'Read Step 1': [{ json: { s: S } }],
    'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(S), blocks, state: { values: state } } } } }] };
  for (const nm of ['After Prepare', 'After Prepare Series']) {
    const p = await j1(nm, [{ json: { status: 'REJECTED', reason: 'CLIENT_CHECK', human: 'x', suggestions: ['Harold Orozco Productions'] } }], outs);
    const v = p.view || {};
    ok(picked(blkOf(v, /^more_rooms$/)).join() === 'Studio 8,Studio C' && picked(blkOf(v, /^booth~/)).join() === 'Studio A,Studio B' && picked(blkOf(v, /^holding$/)).join() === 'Likha',
       nm + ': + Multiple studios / Vocal booths / Holding rooms picks kept', v.blocks && v.blocks.map(b => b.block_id + ':' + JSON.stringify(picked(b))));
    ok(blkOf(v, /^room$/).elements ? true : true, nm + ': (the rest of the form as before)');
    const tx = blkOf(v, /^client$/);
    ok(tx && tx.element.initial_value === 'harold orozco' && blkOf(v, /^project$/).element.initial_value === 'testing multiple - studios', nm + ': typed text kept, as before');
  }
  const empty = Object.assign({}, state, { more_rooms: { more_rooms_pick: ms([]) } });
  let p = await j1('After Prepare', [{ json: { status: 'REJECTED', reason: 'CLIENT_CHECK', human: 'x', suggestions: ['Y'] } }], Object.assign({}, outs, {
    'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(S), blocks: JSON.parse(JSON.stringify(blocks)).map(b => b.block_id === 'more_rooms' ? Object.assign(b, { element: Object.assign(b.element, { initial_options: [opt('Studio 8')] }) }) : b), state: { values: empty } } } } }] }));
  ok(!picked(blkOf(p.view, /^more_rooms$/)).length, 'all taken off before Book -> stays empty (not the earlier pick)');

  console.log('Which room was just taken (Book)');
  let w = await j1('After Prepare', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'Studio 8', summary: 'OTHER / X' }] } }], outs);
  ok(/\*Studio 8\* was just taken\. Take it off, or go \*Back\* and pick another time\./.test(JSON.stringify(w.view)), 'several rooms -> "*Studio 8* was just taken. Take it off, …"', w.warn);
  w = await j1('After Prepare', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ room: 'Studio F', summary: 'OTHER / X' }] } }], Object.assign({}, outs, { 'Read Step 2': [{ json: Object.assign({}, R2, { rooms: 'Studio F' }) }] }));
  ok(/That room was just taken\. Pick another room, or go \*Back\*\./.test(JSON.stringify(w.view)), 'one room -> as before ("That room was just taken.")');

  console.log('The DM paths: the saved answers carry the rooms, step 2 picks them again');
  const rs2 = si.nodes.find(n => n.name === 'Read Step 2').parameters.jsCode;
  ok(/mr: moreRooms\.join\(','\), bo: booths\.join\(','\), ho: holding\.join\(','\)/.test(rs2), 'Read Step 2: again carries mr / bo / ho');
  const step2 = async (s, ra) => (await j1('Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] })).view;
  const FREE = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio F', 'Studio C', 'Studio A', 'Studio B', 'Studio D', 'Likha', 'Katha', 'Salin'];
  let v = await step2(Object.assign({}, S, { purpose: 'Celebrity Recording', pre: { r: 'Studio F', mr: 'Studio 8,Studio C', bo: 'Studio A,Studio B', ho: 'Likha' } }), { free_priority: ['Studio F', 'Studio C'], free_rooms: FREE });
  ok(picked(blkOf(v, /^more_rooms$/)).join() === 'Studio 8,Studio C' && picked(blkOf(v, /^booth~/)).join() === 'Studio A,Studio B' && picked(blkOf(v, /^holding$/)).join() === 'Likha',
     'Continue booking / Book a room again -> the studios, booths and holding room picked again', v.blocks.map(b => b.block_id + ':' + JSON.stringify(picked(b))));
  v = await step2(Object.assign({}, S, { purpose: 'Celebrity Recording', pre: { r: 'Studio F', mr: 'Studio 8,Studio 3', bo: 'Studio A' } }), { free_priority: ['Studio F', 'Studio C'], free_rooms: FREE, busy: ['Studio 8 (X)'] });
  ok(picked(blkOf(v, /^more_rooms$/)).join() === 'Studio 3', 'a studio taken since -> not picked (the free ones are)');
  v = await step2(Object.assign({}, S, { purpose: 'Celebrity Recording', pre: { r: 'Studio 7', bo: 'Studio B' } }), { free_priority: ['Studio F', 'Studio C'], free_rooms: FREE, busy: ['Studio 7 (X)'] });
  ok(!picked(blkOf(v, /^booth~/)).length, 'the studio is not the one picked before -> its booths start fresh');
  v = await step2(Object.assign({}, S, { purpose: 'VO Recording' }), { free_priority: ['Studio 7', 'Studio 8'], free_rooms: FREE });
  ok(!picked(blkOf(v, /^more_rooms$/)).length && !picked(blkOf(v, /^booth~/)).length, 'nothing saved -> nothing picked (as v53)');

  console.log('Change: every room kept when the form comes back or goes on in the DM; the Changed card');
  const BK = { id: 'e1', d: '2027-10-29', s: '13:00', e: '16:00', r: 'Studio 7, Studio 8', t: 'KUBA / HL', st: 'VO Recording' };
  const RC = { viewId: 'V1', user: 'U1', meta: { ch: 'D1', ts: '5.5', b: BK }, b: BK, n: { d: '2027-10-29', s: '14:00', e: '17:00', r: 'Studio 7' }, newRooms: 'Studio 7, Studio 8, Studio F', roomChanged: true,
    d: { project: 'KUBA', client: '', en: 'U1', ar: 'none', st: '', teamShown: true } };
  let am = await j1('After Move', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ summary: 'OTHER / X' }] } }], { 'Read Change': [{ json: RC }], 'To Move': [{ json: {} }], 'Read Cache 7': cache });
  ok(/One of the rooms \(Studio 7, Studio 8, Studio F\) is taken then by \\"OTHER \/ X\\"/.test(JSON.stringify(am)), 'a room taken -> "One of the rooms (…) is taken then by "OTHER / X""', am.why);
  ok(picked(blkOf(am.view, /^studios_c$/)).join() === 'Studio 8,Studio F' && blkOf(am.view, /^room$/).element.initial_option.value === 'Studio 7', 'the form comes back with Studio 8 + Studio F still picked');
  am = await j1('After Move', [{ json: { status: 'REJECTED', reason: 'ROOM_OCCUPIED', conflicts: [{ summary: 'OTHER / X' }] } }], { 'Read Change': [{ json: Object.assign({}, RC, { newRooms: 'Studio 7' }) }], 'To Move': [{ json: {} }], 'Read Cache 7': cache });
  ok(/Studio 7 is taken then/.test(JSON.stringify(am)) && !/One of the rooms/.test(JSON.stringify(am)), 'one room -> as before ("Studio 7 is taken then")');
  am = await j1('After Move', [{ json: { status: 'MOVED', event_id: 'e2', description: 'ref: U1' } }], { 'Read Change': [{ json: RC }], 'To Move': [{ json: { new_summary: 'KUBA / HL' } }], 'Read Cache 7': cache });
  ok(am.ok && /\*Room:\* Studio 7 \+ Studio 8 \+ Studio F/.test(am.card || ''), 'Changed -> the card shows every room (was Studio 7 only)', am.card);
  const ad = await j1('Ask DM', [{ json: { ok: false, error: 'not_found' } }], { 'To Move': [{ json: { go: false, warn: 'Did you mean *Jem Lim*?', askedClient: 'Jem Lin' } }], 'Read Change': [{ json: RC }] });
  const bv = JSON.parse(ad.blocks[2].elements[0].value);
  ok(bv.n.r === 'Studio 7, Studio 8, Studio F' && ad.blocks[2].elements[0].value.length <= 2000, 'Continue changing (DM) carries every room', bv.n);
  const bc = await j1('Build Change', [], { 'Check Signature': [{ json: { user: 'U1', triggerId: 'T' } }], 'Read Cache 6': cache,
    'Read Request': [{ json: { payload: { actions: [{ action_id: 'bk_change', value: JSON.stringify(bv) }], container: { channel_id: 'D1', message_ts: '1' } } } }] });
  ok(picked(blkOf(bc.view, /^studios_c$/)).join() === 'Studio 8,Studio F', '...and the form it opens has them picked');
  const tmv = code('To Move');
  ok(/view: changeView\(R\.b, Object\.assign\(\{\}, R\.n, R\.newRooms \? \{ r: R\.newRooms \} : \{\}\), warn,/.test(tmv), 'To Move\'s client question redraws with every room');
  if (/v55: the note saved from an earlier try/.test(JSON.stringify(si.nodes))) {
    console.log('v55: the note');
    const nb = blocks.concat([{ type: 'input', block_id: 'notes', optional: true, label: { type: 'plain_text', text: 'Note' }, element: { type: 'plain_text_input', action_id: 'notes_in', multiline: true } }]);
    const st2 = Object.assign({}, state, { notes: { notes_in: { type: 'plain_text_input', value: 'bring the USB\nand cans' } } });
    const fa = await j1('After Prepare', [{ json: { status: 'REJECTED', reason: 'CLIENT_CHECK', human: 'x', suggestions: ['Y'] } }], Object.assign({}, outs, {
      'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify(S), blocks: nb, state: { values: st2 } } } } }] }));
    ok(blkOf(fa.view, /^notes$/).element.initial_value === 'bring the USB\nand cans', 'the window still open (formAgain): the note kept (as before)');
    ok(/nt: notes\.slice\(0, 600\)/.test(rs2), 'Read Step 2: the saved answers carry the note (at most 600 characters)');
    v = await step2(Object.assign({}, S, { pre: { r: 'Studio 7', nt: 'bring the USB\nand cans' } }), { free_priority: ['Studio 7', 'Studio 8'], free_rooms: FREE });
    ok(blkOf(v, /^notes$/).element.initial_value === 'bring the USB\nand cans', 'Continue booking / Book a room from the DM: the Note filled in again');
    v = await step2(Object.assign({}, S, {}), { free_priority: ['Studio 7'], free_rooms: FREE });
    ok(!blkOf(v, /^notes$/).element.initial_value, 'nothing saved -> the Note empty, as before');
    const R0 = { channel: 'U1', calTitle: 'KUBA / HL', again: { d: '2027-10-29', s: '13:00', e: '16:00', p: 'VO Recording', r: 'Studio 7', pj: 'KUBA', mr: 'Studio 8', nt: 'bring the USB' } };
    for (const nm of ['Question DM', 'Result DM']) {
      const q = await j1(nm, [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 2': [{ json: R0 }], 'After Prepare': [{ json: { warn: 'Did you mean *Jem Lim*?' } }], 'After Book': [{ json: { ok: false, warn: 'x' } }] });
      const val = q && JSON.parse(JSON.stringify(q.blocks)).map(b => (b.elements || [])).flat().find(e => e.action_id === 'book_continue' || e.action_id === 'open_book');
      ok(val && JSON.parse(val.value).nt === 'bring the USB' && JSON.parse(val.value).mr === 'Studio 8', nm + ': the button carries the note and the rooms', val && val.value);
      const long = Object.assign({}, R0, { again: Object.assign({}, R0.again, { pj: 'P'.repeat(1200), nt: 'n'.repeat(600) }) });
      const q2 = await j1(nm, [{ json: { ok: false, error: 'not_found' } }], { 'Read Step 2': [{ json: long }], 'After Prepare': [{ json: { warn: 'x' } }], 'After Book': [{ json: { ok: false, warn: 'x' } }] });
      const v2 = q2.blocks.map(b => (b.elements || [])).flat().find(e => e.action_id === 'book_continue' || e.action_id === 'open_book');
      const g2 = JSON.parse(v2.value);
      ok(v2.value.length <= 1900 && !g2.nt && g2.pj && g2.mr === 'Studio 8', nm + ': too long for the button -> the note left off, the rest kept (was: nothing kept)', v2.value.length);
    }
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('FAIL crashed: ' + e.stack); process.exit(1); });
