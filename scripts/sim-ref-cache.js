#!/usr/bin/env node
// Offline checks for the reference cache (refresh v2 + main v173), on real data from a main execution.
//
//   node scripts/sim-ref-cache.js <refresh.json> <main-candidate.json> <main-live.json> <main-execution.json>
//
// Runs the new Code nodes with an emulated $ / $input, and runs main's unchanged Booked For, Room Table and the
// staff_data tool expressions twice - once on the Airtable items the execution really had, once on the adapter
// output built from the same records through Build Cache -> cache row -> Reference Snapshot - and requires both
// runs to produce identical results.
const fs = require('fs');
const [refreshF, mainF, liveF, execF] = process.argv.slice(2);
const R = JSON.parse(fs.readFileSync(refreshF)), M = JSON.parse(fs.readFileSync(mainF)), L = JSON.parse(fs.readFileSync(liveF));
const run = JSON.parse(fs.readFileSync(execF)).data.resultData.runData;
const node = (w, n) => w.nodes.find(x => x.name === n);
const code = (w, n) => node(w, n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg) => { if (c) pass++; else { fail++; console.log('  FAIL ' + msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const AsyncFn = Object.getPrototypeOf(async function () {}).constructor;
const wrap = it => ({ first: () => it[0], last: () => it[it.length - 1], all: () => it, item: it[0] });
const recorded = n => { const r = run[n]; return r ? (((r[0].data || {}).main || [[]])[0] || []) : null; };
const mk$ = (over = {}) => n => { const it = over[n] || recorded(n); if (!it) throw new Error('Referenced node is unexecuted: ' + n); return wrap(it); };
const exec = (src, $, input = [{ json: {} }]) => new AsyncFn('$input', '$', src)(wrap(input), $);
const throws = async (f) => { try { await f(); return false; } catch (e) { return e.message; } };

(async () => {
  const air = { 'All Rooms': recorded('All Rooms'), 'All Session Types': recorded('All Session Types'), 'All Bookers': recorded('All Bookers') };
  const flat = Object.fromEntries(Object.entries(air).map(([k, v]) =>
    [k, v.map(i => ({ json: { id: i.json.id, createdTime: i.json.createdTime, ...i.json.fields } }))]));

  console.log('1. Build Cache');
  const bc = code(R, 'Build Cache');
  const out = await exec(bc, mk$(air));
  ok(out.length === 1, 'emits exactly one item (got ' + out.length + ')');
  const row = out[0].json;
  ok(row.cache_key === 'jessie-reference', 'cache_key');
  ok(!isNaN(Date.parse(row.refreshed_at)) && /Z$/.test(row.refreshed_at), 'refreshed_at is an ISO string');
  ok(typeof row.payload === 'string', 'payload is a string');
  const P = JSON.parse(row.payload);
  ok(P.rooms.length === air['All Rooms'].length && P.sessionTypes.length === air['All Session Types'].length && P.bookers.length === air['All Bookers'].length,
     `counts ${P.rooms.length}/${P.sessionTypes.length}/${P.bookers.length}`);
  ok(P.rooms.every(r => Object.keys(r).join() === 'id,fields'), 'records normalised to {id, fields}');
  const outFlat = await exec(bc, mk$(flat));
  ok(outFlat[0].json.payload === row.payload, 'flattened Airtable records give the identical payload');
  for (const [label, over] of [
    ['empty read (alwaysOutputData {})', { 'All Bookers': [{ json: {} }] }],
    ['error item', { 'All Rooms': [{ json: { error: 'Airtable 503' } }] }],
    ['record missing its name', { 'All Session Types': [{ json: { id: 'recX', fields: { Type: '' } } }] }],
    ['duplicate record', { 'All Bookers': [air['All Bookers'][0], air['All Bookers'][0]] }],
    ['no items at all', { 'All Rooms': [] }]]) {
    const m = await throws(() => exec(bc, mk$({ ...air, ...over })));
    ok(m && /cache not changed/.test(m), 'refuses ' + label + ' (throws, so Save never runs)');
  }

  console.log('2. Check Reference Cache');
  const ck = code(M, 'Check Reference Cache');
  const at = ms => new Date(Date.now() - ms).toISOString();
  const good = { id: 175, cache_key: 'jessie-reference', payload: row.payload, refreshed_at: at(60e3) };
  const nul = { id: 1, cache_key: null, payload: null, refreshed_at: null };
  const check = async rows => (await exec(ck, mk$(), rows.map(j => ({ json: j }))))[0].json;
  let c = await check([nul, nul, good]);
  ok(c.cacheFresh === true && c.cacheState === 'fresh', 'fresh row among null rows -> hit');
  c = await check([{ ...good, refreshed_at: at(16 * 60e3) }]);
  ok(c.cacheFresh === false && c.cacheState === 'stale', 'older than 15 min -> stale');
  c = await check([{}]);
  ok(c.cacheFresh === false && c.cacheState === 'no cache row', 'no row (alwaysOutputData {}) -> missing');
  c = await check([{ error: 'data table unreachable' }]);
  ok(c.cacheFresh === false, 'read error -> miss');
  c = await check([{ ...good, payload: '{"rooms":' }]);
  ok(c.cacheFresh === false && /JSON/.test(c.cacheState), 'truncated payload -> malformed');
  c = await check([{ ...good, payload: JSON.stringify({ ...P, bookers: [] }) }]);
  ok(c.cacheFresh === false && /bookers/.test(c.cacheState), 'empty bookers -> malformed');
  c = await check([{ ...good, refreshed_at: 'yesterday' }]);
  ok(c.cacheFresh === false, 'bad refreshed_at -> malformed');
  c = await check([{ ...good, refreshed_at: at(20 * 60e3) }, { ...good, id: 176, refreshed_at: at(30e3) }]);
  ok(c.cacheFresh === true, 'duplicate keyed rows -> newest valid one is used');
  ok(!('payload' in c), 'check item does not copy the payload');

  console.log('3. Reference Snapshot');
  const sn = code(M, 'Reference Snapshot');
  const hit = async rows => (await exec(sn, mk$({ 'Read Reference Cache': rows.map(j => ({ json: j })) }),
    [{ json: { cacheFresh: true } }]))[0].json;
  let s = await hit([nul, good]);
  ok(s.ok && s.source === 'cache' && s.rooms.length === P.rooms.length, 'cache hit -> snapshot from the cached row');
  const saved = { ...good, id: 175, refreshed_at: new Date().toISOString(), createdAt: 'x', updatedAt: 'y' };
  s = (await exec(sn, mk$(), [{ json: saved }]))[0].json;
  ok(s.ok && s.source === 'refresh', 'miss -> snapshot from the row Refresh Cache Now returned');
  s = (await exec(sn, mk$(), [{ json: { error: { message: 'Build Cache: All Rooms: invalid or failed Airtable read' } } }]))[0].json;
  ok(s.ok === false && /refresh failed/.test(s.reason), 'refresh failure -> ok:false (lookup-failure reply)');
  s = (await exec(sn, mk$(), [{ json: { ...saved, payload: 'null' } }]))[0].json;
  ok(s.ok === false, 'refresh returning a malformed row -> ok:false');
  const fr = (await exec(code(M, 'Reference Lookup Failed'), mk$(), [{ json: { ok: false, reason: 'x' } }]))[0].json;
  ok(typeof fr.output === 'string' && fr.output.length > 20, 'failure path produces a Send Reply output');

  console.log('4. Adapters and downstream equivalence (' + execF.split('/').pop() + ')');
  const snap = await hit([good]);
  const $snap = mk$({ 'Reference Snapshot': [{ json: snap }] });
  const adapted = {};
  for (const n of ['All Rooms', 'All Session Types', 'All Bookers']) {
    adapted[n] = await exec(code(M, n), $snap, [{ json: snap }]);
    ok(eq(adapted[n].map(i => i.json), air[n].map(i => ({ id: i.json.id, fields: i.json.fields }))),
       n + ': same records, same order, same {id, fields}');
    ok(adapted[n].every(i => eq(i.pairedItem, { item: 0 })), n + ': items paired to the input item');
  }
  const bfSrc = code(L, 'Booked For'), rtSrc = code(L, 'Room Table');
  ok(bfSrc === code(M, 'Booked For') && rtSrc === code(M, 'Room Table'), 'Booked For / Room Table unchanged in v173');
  const world = async src => {
    const bf = await exec(bfSrc, mk$(src), src['All Bookers']);
    const $w = mk$({ ...src, 'Booked For': bf });
    const rt = await exec(rtSrc, $w, recorded('Prepared Booking'));
    const exprs = {};
    for (const t of ['Book Session', 'Prepare Booking', 'Book Direct']) {
      const n = node(M, t); const v = JSON.stringify(n.parameters);
      const m = /"staff_data":"=\{\{(.*?)\}\}"/.exec(v);
      if (m) exprs[t] = new Function('$', 'return (' + JSON.parse('"' + m[1] + '"') + ');')($w);
    }
    return { bf: bf.map(i => i.json), rt: rt.map(i => i.json), exprs };
  };
  const A = await world(air), B = await world(adapted);
  ok(eq(A.bf, B.bf), 'Booked For output identical');
  ok(eq(A.rt, B.rt), 'Room Table output identical (' + JSON.stringify(A.rt).length + ' chars)');
  ok(Object.keys(A.exprs).length === 3 && eq(A.exprs, B.exprs), 'staff_data expressions in Book Session / Prepare Booking / Book Direct identical');

  console.log('5. Wiring');
  const to = (w, n, b = 0) => (((w.connections[n] || {}).main || [])[b] || []).map(t => t.node);
  ok(eq(to(M, 'Gate Context'), ['Read Reference Cache']), 'Gate Context -> Read Reference Cache');
  ok(eq(to(M, 'Cache Fresh?', 0), ['Reference Snapshot']) && eq(to(M, 'Cache Fresh?', 1), ['Refresh Cache Now']), 'hit skips the refresh; miss refreshes');
  ok(eq(to(M, 'Reference OK?', 0), ['All Rooms']) && eq(to(M, 'Reference OK?', 1), ['Reference Lookup Failed']) && eq(to(M, 'Reference Lookup Failed'), ['Send Reply']), 'ok -> adapters; failure -> reply');
  for (const [a, b] of [['All Rooms', 'All Session Types'], ['All Session Types', 'All Bookers'], ['All Bookers', 'Booked For'], ['Booked For', 'Prepared Booking'], ['Prepared Booking', 'Room Table'], ['Room Table', 'Book Direct?']])
    ok(eq(to(M, a), [b]), a + ' -> ' + b + ' preserved');
  ok(['All Rooms', 'All Session Types', 'All Bookers'].every(n => node(M, n).type === 'n8n-nodes-base.code'), 'no Airtable read on the three names in main');
  ok(node(M, 'Get Booker').type === 'n8n-nodes-base.airtable', 'Get Booker still live');
  ok(node(M, 'Refresh Cache Now').parameters.workflowId.value === 'DxByjma1WLGMLR0L', 'Refresh Cache Now calls the refresh workflow');
  const changed = L.nodes.filter(n => { const m = node(M, n.name); return !m || JSON.stringify(m.parameters) !== JSON.stringify(n.parameters) || m.type !== n.type; }).map(n => n.name).sort();
  ok(eq(changed, ['All Bookers', 'All Rooms', 'All Session Types']), 'only the three reads changed in main (' + changed + ')');
  ok(M.nodes.length === L.nodes.length + 7, 'seven nodes added');
  const liveConn = JSON.parse(JSON.stringify(L.connections)); delete liveConn['Gate Context'];
  const candConn = JSON.parse(JSON.stringify(M.connections));
  for (const k of ['Gate Context', 'Read Reference Cache', 'Check Reference Cache', 'Cache Fresh?', 'Refresh Cache Now', 'Reference Snapshot', 'Reference OK?', 'Reference Lookup Failed']) delete candConn[k];
  ok(eq(Object.keys(liveConn).sort(), Object.keys(candConn).sort()) && Object.keys(liveConn).every(k => eq(liveConn[k], candConn[k])), 'every other connection unchanged');
  const rt = n => to(R, n);
  ok(['Run Manually', 'Every 5 Minutes', 'When Executed by Another Workflow'].every(t => eq(rt(t), ['All Rooms'])), 'refresh: all three triggers -> All Rooms');
  ok(eq(rt('All Rooms'), ['All Session Types']) && eq(rt('All Session Types'), ['All Bookers']) && eq(rt('All Bookers'), ['Build Cache']) && eq(rt('Build Cache'), ['Save Reference Cache']), 'refresh: read chain -> Build Cache -> Save');
  ok(Object.values(R.connections).flatMap(v => v.main.flat()).filter(t => t.node === 'Save Reference Cache').length === 1, 'refresh: Save is reachable only from Build Cache');
  for (const n of ['All Rooms', 'All Session Types', 'All Bookers']) {
    const x = node(R, n);
    // n8n drops settings equal to their default when it saves: returnAll defaults to true (Airtable v2 search) and
    // onError to stopping the workflow, so a missing value is the default, not a missing setting.
    ok(x.executeOnce === true && x.parameters.returnAll !== false && (x.onError === undefined || x.onError === 'stopWorkflow') && x.credentials && x.credentials.airtableTokenApi, 'refresh ' + n + ': once, all pages, stop on error, credential kept');
  }
  ok(node(R, 'All Rooms').parameters.filterByFormula === "={{ '{Active / Bookable}' }}", 'refresh: Active / Bookable filter kept');
  const sv = node(R, 'Save Reference Cache').parameters;
  ok(sv.operation === 'upsert' && sv.dataTableId.value === 'CsdJhgDxCsqq9K9j' && eq(Object.keys(sv.columns.value), ['cache_key', 'payload', 'refreshed_at']) && sv.columns.schema.every(c => c.type === 'string'), 'refresh: upsert writes all three String columns');
  ok([5, undefined].includes(node(R, 'Every 5 Minutes').parameters.rule.interval[0].minutesInterval), 'refresh: every 5 minutes (5 is the default n8n drops on save)');

  console.log(`\n${fail ? 'FAIL' : 'OK'} - ${pass} passed, ${fail} failed`);
  process.exit(fail ? 1 : 0);
})().catch(e => { console.log('CRASH', e.stack); process.exit(2); });
