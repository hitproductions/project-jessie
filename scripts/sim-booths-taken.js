#!/usr/bin/env node
// Slack Interactions v79 (Howard, 9 Nov): "Not free then:" under Vocal booths too - the field's hint names the vocal booths taken then
// (on a series, on any of the dates); none when every booth is free; the same in Build Step 1, Build Step 2 and Note Toggle (the
// redraw when the studio changes reads the form's bx, which now carries nf).
//   node scripts/sim-booths-taken.js [slack-interactions v79]
const fs = require('fs');
const W = f => JSON.parse(fs.readFileSync(f, 'utf8'));
const SI = W(process.argv[2] || 'workflows/slack-interactions-v79.json');
if (JSON.stringify(SI.nodes).indexOf('v79 (Howard): the taken booths named') === -1) { console.log('0 ok, 0 failed (older build: SI v79 not in it)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('  FAIL  ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 700))); } };
const jsOf = (wf, n) => wf.nodes.find(x => x.name === n).parameters.jsCode;
const $f = O => n => ({ first: () => { if (!(n in O)) throw new Error('not run: ' + n); return O[n][0]; }, all: () => O[n] || [] });
const run = async (wf, name, input, O) => new Function('$', '$input', 'return (async function(){' + jsOf(wf, name) + '\n})();')($f(O), { first: () => input[0], all: () => input });
const j1 = async (...a) => ((await run(...a))[0] || {}).json;
const rooms = JSON.parse(JSON.stringify(FX.rooms));
rooms.find(r => r.fields['Room Name'] === 'Studio E').fields['Vocal Booth'] = true;   // as in Airtable since 3 Nov
const cache = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms, sessionTypes: FX.sessionTypes, bookers: FX.bookers }) } }];
const step2 = async (s, ra) => j1(SI, 'Build Step 2', [{ json: Object.assign({ status: 'OK', busy: [] }, ra) }], { 'Read Step 1': [{ json: { s } }], 'Read Cache 2': cache, 'Loc Projects 2': [] });
const FREE = ['Studio 1', 'Studio 2', 'Studio 3', 'Studio 5', 'Studio 6', 'Studio 7', 'Studio 8', 'Studio F', 'Studio C', 'Studio A', 'Studio B', 'Studio D', 'Studio E', 'Likha', 'Katha', 'Salin'];
const S = { date: '2026-11-10', t0: '10:00', t1: '15:00', kind: 'loc', purpose: 'Localization Dubbing', requester: 'U1', when: 'x' };
const booth = v => v.blocks.find(b => /^booth/.test(b.block_id || '') && b.type === 'input');
const meta = r => { try { return JSON.parse(r.view.private_metadata || r.private_metadata || '{}'); } catch (e) { return {}; } };

(async () => {
  console.log('Build Step 2: the Vocal booths hint');
  let r = await step2(S, { free_priority: ['Studio 2'], free_rooms: FREE.filter(n => ['Studio 1', 'Studio 6', 'Studio A', 'Studio D'].indexOf(n) === -1),
    busy: ['Studio 1 (X)', 'Studio 6 (Y)', 'Studio A (Z)', 'Studio D (W)'] });
  let b = booth(r.view);
  ok(b && b.hint && b.hint.type === 'plain_text' && b.hint.text === 'Not free then: Studio A, Studio D', 'Studio A and D taken -> "Not free then: Studio A, Studio D" under Vocal booths', b && b.hint);
  ok(b && b.element.options.map(o => o.value).join() === 'Studio B,Studio E', 'the list still holds only the free booths', b && b.element.options.map(o => o.value));
  ok(JSON.stringify(r.view.blocks).indexOf('Not free then: Studio 1, Studio 6') !== -1, 'the studios line is unchanged ("Not free then: Studio 1, Studio 6")');
  const m = meta(r);
  ok(m.bx && [].concat(m.bx.nf).join() === 'Studio A,Studio D', 'the form keeps nf (not free) in its bx (for the redraw)', m.bx);
  ok(String(r.view.private_metadata || '').length < 3000, 'private_metadata under 3,000 characters', String(r.view.private_metadata || '').length);

  r = await step2(S, { free_priority: ['Studio 2'], free_rooms: FREE });
  b = booth(r.view);
  ok(b && !('hint' in b), 'every booth free -> no line', b && b.hint);

  r = await step2(S, { free_priority: ['Studio 2'], free_rooms: FREE.filter(n => !/^Studio [ABDE]$/.test(n)), busy: ['Studio A (1)', 'Studio B (2)', 'Studio D (3)', 'Studio E (4)'] });
  const ctx = r.view.blocks.find(x => /^booth/.test(x.block_id || ''));
  ok(ctx && ctx.type === 'context' && /No vocal booth is free then/.test(ctx.elements[0].text) && !ctx.hint, 'no booth free -> the "No vocal booth is free then" line, as before', ctx);

  r = await step2(Object.assign({}, S, { kind: 'studio', purpose: 'VO Recording' }), { free_priority: ['Studio 2'], free_rooms: FREE.filter(n => n !== 'Studio B'), busy: ['Studio B (X)'] });
  b = booth(r.view);
  ok(b && b.optional === true && b.hint && b.hint.text === 'Not free then: Studio B', 'VO Recording (booth optional) -> "Not free then: Studio B"', b);

  console.log('the same boothBlocks in Build Step 1, Build Step 2 and Note Toggle');
  const fnOf = n => { const c = jsOf(SI, n), i = c.indexOf('function boothBlocks'), e = c.indexOf('\n}\n', i); return c.slice(i, e + 2); };
  const f1 = fnOf('Build Step 1'), f2 = fnOf('Build Step 2'), f3 = fnOf('Note Toggle');
  ok(f1 === f2 && f2 === f3, 'identical in the three nodes');
  const bb = new Function(f3 + '\nreturn boothBlocks;')();
  const BX = { need: true, list: ['Studio B', 'Studio E'], pair: { 'Studio 6': ['Studio D', 'Studio B'] }, nf: ['Studio A', 'Studio D'] };
  const out = bb('Studio 6', BX)[0];
  ok(out.hint && out.hint.text === 'Not free then: Studio A, Studio D' && out.element.initial_options[0].value === 'Studio B', 'Note Toggle redraw for another studio keeps the line', out);
  const old = bb('Studio 6', { need: true, list: ['Studio B'], pair: {} })[0];
  ok(!('hint' in old), 'a form opened before v79 (no nf in bx) -> no line, no error', old);

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
