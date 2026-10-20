#!/usr/bin/env node
// Slack Interactions v34 (20 Oct): "Studio E isn't a room for Music Presentation. These are free:" shows when step 2 opens, and is not
// repeated when the form comes back after a problem (formAgain in After Prepare / After Book / After Prepare Series).
// Usage: node scripts/sim-v34-note.js [slack-interactions v34]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v34.json', 'utf8'));
if (!/block_id: 'pre_note'/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (v34 on; this build is older)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 300))); } };
const run = async (name, input, outs) => { const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }); const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + si.nodes.find(x => x.name === name).parameters.jsCode + '\n})();')($, $input); };
const ST = (t, roles, pri) => ({ id: 'st-' + t, fields: { Type: t, Priority: pri, 'Last Resort': [], 'Engineer Role Required': roles, 'Room Requirements': '' } });
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms,
  sessionTypes: [ST('Music Presentation', ['Music Arranger', 'Music Engineer'], ['rf', 'r7']), ST('Post Processing', ['Multimedia Specialist'], ['re'])],
  bookers: [{ id: 'b1', fields: { Name: 'Howard Luistro', Initials: 'HL', 'Slack User ID': 'U1', Info: 'Post Engineer', Department: ['Audio Post'] } }] }) } }];
(async () => {
  const s = { date: '2027-10-21', t0: '12:00', t1: '14:00', purpose: 'Music Presentation', kind: 'studio', requester: 'U1', channel: 'D1', ext: 'x', pre: { r: 'Studio E', p: 'Post Processing', fn: 'Dilan' } };
  const v = (await run('Build Step 2', [{ json: { status: 'OK', busy: [], free_priority: ['Studio F', 'Studio 7'] } }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] }))[0].json.view;
  const note = v.blocks.find(b => b.block_id === 'pre_note');
  ok(note && /Studio E isn’t a room for Music Presentation\. These are free:/.test(note.text.text), 'step 2 opens: "Studio E isn\'t a room for Music Presentation. These are free:" (tagged pre_note)');
  const payload = { view: Object.assign({}, v, { id: 'V1', private_metadata: JSON.stringify(s), state: { values: {} } }) };
  for (const n of ['After Prepare', 'After Book']) {
    const outs = { 'Read Request': [{ json: { payload } }], 'Read Step 2': [{ json: { viewId: 'V1', channel: 'D1', s, prep: {}, again: {} } }], 'To Prepare': [{ json: {} }], 'Read Cache 3': cache,
      'After Prepare': [{ json: { book: {} } }], 'To Book': [{ json: {} }] };
    let out; try { out = (await run(n, [{ json: { status: 'REJECTED', reason: 'SOMETHING_ELSE', human: 'x' } }], outs))[0].json; } catch (e) { out = { err: e.message }; }
    const vb = (out.view || {}).blocks || [];
    ok(vb.length && !vb.some(b => b.block_id === 'pre_note') && vb.some(b => b.block_id === 'problem'), n + ': the form after a problem - the problem on top, the room note gone', out.err || vb.map(b => b.block_id));
  }
  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
