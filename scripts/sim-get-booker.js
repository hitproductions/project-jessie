#!/usr/bin/env node
// Offline checks for main v175 (Get Booker served from the reference cache), on real executions.
//
//   node scripts/sim-get-booker.js <v175.json> <v174.json> <main-execution.json>...
//
// For each execution: builds the cache snapshot from its own Airtable reads, runs the Get Booker adapter for its
// sender, and requires the same records the live Airtable search returned. Then every node that reads
// $('Get Booker') - Gate Context, Booked For, Room Table and every expression in the tool nodes - is evaluated twice,
// once on the recorded Get Booker and once on the adapter, and must give identical results.
const fs = require('fs');
const [candF, baseF, ...execFs] = process.argv.slice(2);
const M = JSON.parse(fs.readFileSync(candF)), B = JSON.parse(fs.readFileSync(baseF));
const node = (w, n) => w.nodes.find(x => x.name === n);
let pass = 0, fail = 0;
const ok = (c, msg) => { if (c) pass++; else { fail++; console.log('  FAIL ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const AsyncFn = Object.getPrototypeOf(async function () {}).constructor;
const wrap = it => ({ first: () => it[0], last: () => it[it.length - 1], all: () => it, item: it[0] });
// $getWorkflowStaticData: Gate Context keeps state there; each run gets its own empty store so runs are comparable.
const exec = (src, $, input = [{ json: {} }]) => { const sd = {}; return new AsyncFn('$input', '$', '$getWorkflowStaticData', src)(wrap(input), $, () => sd); };

(async () => {
  for (const f of execFs) {
    const run = JSON.parse(fs.readFileSync(f)).data.resultData.runData;
    const rec = n => run[n] ? (((run[n][0].data || {}).main || [[]])[0] || []) : null;
    const mk$ = (over = {}) => n => { const it = over[n] || rec(n); if (!it) throw new Error('unexecuted: ' + n); return wrap(it); };
    console.log(f.split('/').pop());
    const snap = { ok: true, bookers: rec('All Bookers').map(i => ({ id: i.json.id, fields: i.json.fields })) };
    const gbSrc = node(M, 'Get Booker').parameters.jsCode;
    const got = await exec(gbSrc, mk$({ 'Reference Snapshot': [{ json: snap }] }));
    const want = rec('Get Booker');
    ok(eq(got.map(i => i.json), want.map(i => ({ id: i.json.id, fields: i.json.fields }))), 'adapter returns the record the Airtable search returned (' + (want[0].json.fields || {}).Name + ')');
    for (const [label, user] of [['unknown sender', 'U00NOBODY'], ['empty sender', '']]) {
      const r = await exec(gbSrc, mk$({ 'Reference Snapshot': [{ json: snap }], 'Slack Trigger': [{ json: { user } }] }));
      ok(eq(r.map(i => i.json), [{}]), label + ' -> one empty item, like alwaysOutputData');
    }
    const A = mk$(), Bw = mk$({ 'Get Booker': got });
    for (const n of ['Gate Context', 'Booked For', 'Room Table']) {
      const src = node(M, n).parameters.jsCode; const inp = rec(n === 'Gate Context' ? 'Get Recent Messages' : (n === 'Booked For' ? 'All Bookers' : 'Prepared Booking'));
      let a, b; try { a = (await exec(src, A, inp)).map(i => i.json); } catch (e) { a = 'ERR ' + e.message; }
      try { b = (await exec(src, Bw, inp)).map(i => i.json); } catch (e) { b = 'ERR ' + e.message; }
      if (n === 'Gate Context') { const strip = x => JSON.parse(JSON.stringify(x, (k, v) => /time|now|epoch/i.test(k) && typeof v !== 'object' ? undefined : v)); a = strip(a); b = strip(b); }
      ok(eq(a, b) && typeof a !== 'string', n + ' identical on cached Get Booker');
    }
    let exprs = 0, same = 0;
    const $fromAI = () => '';
    const tmpl = ($, s) => s.slice(1).replace(/\{\{([\s\S]*?)\}\}/g, (m, e) => { try { return String(new Function('$', '$fromAI', '$json', 'return (' + e + ');')($, $fromAI, {})); } catch (x) { return 'ERR'; } });
    const walk = (o, cb) => { if (typeof o === 'string') cb(o); else if (o && typeof o === 'object') Object.values(o).forEach(v => walk(v, cb)); };
    for (const n of M.nodes) walk(n.parameters, s => {
      if (typeof s !== 'string' || !s.startsWith('=') || !s.includes("'Get Booker'") || n.type.endsWith('.code')) return;
      exprs++; if (tmpl(A, s) === tmpl(Bw, s)) same++; else console.log('    differs in ' + n.name);
    });
    ok(exprs > 5 && same === exprs, `every expression reading Get Booker gives the same value (${same}/${exprs})`);
  }
  console.log('wiring');
  const to = (w, n, b = 0) => (((w.connections[n] || {}).main || [])[b] || []).map(t => t.node);
  ok(eq(to(M, 'Consent Reject?', 1), ['Read Reference Cache']), 'Consent Reject? (not a consent reply) -> Read Reference Cache');
  ok(eq(to(M, 'Reference OK?', 0), ['Get Booker']) && eq(to(M, 'Reference OK?', 1), ['Reference Lookup Failed']), 'Reference OK? -> Get Booker | failure reply');
  ok(eq(to(M, 'Get Booker'), ['Get Recent Messages']) && eq(to(M, 'Get Recent Messages'), ['Gate Context']) && eq(to(M, 'Gate Context'), ['All Rooms']), 'Get Booker -> Get Recent Messages -> Gate Context -> All Rooms');
  ok(!M.nodes.some(n => n.type === 'n8n-nodes-base.airtable'), 'no Airtable read left in the main chain (tools only)');
  const diff = B.nodes.filter(n => { const m = node(M, n.name); return !m || JSON.stringify(m.parameters) !== JSON.stringify(n.parameters) || m.type !== n.type; }).map(n => n.name);
  ok(eq(diff, ['Get Booker']) && M.nodes.length === B.nodes.length, 'only Get Booker changed from v174 (' + diff + ')');
  const strip = c => { const x = JSON.parse(JSON.stringify(c)); delete x['Consent Reject?']; delete x['Reference OK?']; delete x['Gate Context']; return x; };
  ok(eq(strip(M.connections), strip(B.connections)), 'every other connection unchanged');
  console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('CRASH', e.stack); process.exit(2); });
