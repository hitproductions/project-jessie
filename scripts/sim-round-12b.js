#!/usr/bin/env node
// Round 12b offline (20 Oct): Slack Interactions v31 (wait estimates on the loading views, learned in Jessie Timings; Localization
// Projects at step 2 only for a filled-in code), Book Session v115 (the project code to Log Booking) and Log Booking v2 (a code
// not in Localization Projects -> the New Projects tab, after the reply).
// Usage: node scripts/sim-round-12b.js [slack-interactions v31] [book-session v115] [log-booking v2]
const fs = require('fs');
const si = JSON.parse(fs.readFileSync(process.argv[2] || 'workflows/slack-interactions-v31.json', 'utf8'));
const bs = JSON.parse(fs.readFileSync(process.argv[3] || 'workflows/book-session-v115.json', 'utf8'));
const lb = JSON.parse(fs.readFileSync(process.argv[4] || 'workflows/log-booking-v2.json', 'utf8'));
if (!/v31: the estimate/.test(JSON.stringify(si.nodes))) { console.log('0 ok, 0 failed (round 12b is v31 on; this build is older)'); process.exit(0); }
const FX = require('./sim-fixture-rooms.js');
let pass = 0, fail = 0;
const ok = (c, m, d) => { if (c) { pass++; console.log('  ok    ' + m); } else { fail++; console.log('FAIL ' + m + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 400))); } };
async function runIn(wf, name, input, outs) {
  const js = wf.nodes.find(x => x.name === name).parameters.jsCode;
  const $ = n => { if (outs[n] === undefined) { const e = () => { throw new Error('Node \'' + n + '\' hasn\'t been executed'); }; return { first: e, all: e }; }
    return { first: () => (outs[n] || [])[0], all: () => outs[n] || [] }; };
  const $input = { first: () => input[0], all: () => input };
  return new Function('$', '$input', 'return (async function(){' + js + '\n}).call(this);').call({ helpers: {} }, $, $input);
}
const j1 = async (...a) => (await runIn(si, ...a))[0].json;
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const expr = (e, outs) => { const body = String(e).replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
  const $ = n => ({ first: () => (outs[n] || [])[0], all: () => outs[n] || [] }); return new Function('$', 'return (' + body + ');')($); };
const B = (id, name, ini, slack, info) => ({ id, fields: { Name: name, Initials: ini, 'Slack User ID': slack, Info: info, Department: ['Audio Post'] } });
const bookers = [B('b1', 'Howard Luistro', 'HL', 'U1', 'Post Engineer'), B('b2', 'Jetrho Ty', 'JT', 'U3', 'Loc Engineer')];
const cacheRow = [{ json: { cache_key: 'jessie-reference', refreshed_at: new Date().toISOString(), payload: JSON.stringify({ rooms: FX.rooms, sessionTypes: FX.sessionTypes, bookers }) } }];
const chk = { json: { user: 'U1', triggerId: 'T1', channel: 'D1' } };
const tv = v => ({ selected_option: { value: v } });
const T = (scenario, seconds, dates) => ({ json: { id: 1, scenario, seconds, dates } });
const ctx = v => (v.blocks.find(b => b.type === 'context') || { elements: [{}] }).elements[0].text || '';

(async () => {
  console.log('1: the loading views say how long it usually takes');
  const M = (extra) => Object.assign({ date: '2027-10-21', t0: '13:00', t1: '15:00', purpose: 'VO Recording', kind: 'studio', requester: 'U1', channel: 'D1', ext: 'x', label: 'VO Recording', when: 'x' }, extra || {});
  const read2 = async (tim, meta) => j1('Read Step 2', [], { 'Check Signature': [chk], 'Timings 2': tim, 'Read Cache 3': cacheRow,
    'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V1', private_metadata: JSON.stringify(meta || M()), blocks: [], state: { values: { room: { room_radio: tv('Studio 7') }, project: { project_in: { value: 'x' } }, engineer: { engineer_pick: tv('U1') } } } } } } }] });
  const cases = [
    [[], 'Usually under 30 seconds.', 'book, nothing learned yet -> the fallback, 30 s'],
    [[{ json: {} }], 'Usually under 30 seconds.', 'book, an empty table (alwaysOutputData) -> 30 s'],
    [[T('book', 21.7, 9)], 'Usually under 30 seconds.', 'book 21.7 s over 9 runs -> under 30 seconds (rounded up)'],
    [[T('book', 31, 9)], 'Usually under 40 seconds.', 'book 31 s -> under 40 seconds'],
    [[T('book', 12, 3)], 'Usually under 30 seconds.', 'book 12 s but only 3 runs -> still the 30 s fallback'],
    [[T('book', 45, 3)], 'Usually under 50 seconds.', 'book 45 s after 3 runs -> under 50 seconds (slower than the fallback)'],
    [[T('book', 64, 20)], 'Usually under 2 minutes.', 'book 64 s -> under 2 minutes'],
    [[T('change', 5, 20)], 'Usually under 30 seconds.', 'another scenario\'s row is ignored'],
    [[{ json: { error: 'table not found' } }], 'Usually under 30 seconds.', 'the table could not be read -> the fallback'],
  ];
  for (const [rows, want, label] of cases) { const r = await read2(rows); ok(ctx(r.answer.view).indexOf(want + ' You can close this window') === 0, label, ctx(r.answer.view)); }
  let r = await read2([T('check', 4, 8)], M({ series: { freq: 'weekly', days: ['TH'], dates: ['2027-10-21', '2027-10-28', '2027-11-04'] } }));
  ok(/^Checking availability for each date\. Usually under 20 seconds\. You can close/.test(ctx(r.answer.view)), 'checking 3 dates at 4 s each -> under 20 seconds', ctx(r.answer.view));
  const rsc = async (tim, n) => j1('Read Series Confirm', [], { 'Check Signature': [chk], 'Timings 13': tim, 'Read Request': [{ json: { payload: { type: 'view_submission', view: { id: 'V3', private_metadata: JSON.stringify({ key: 'k', n, title: 'X' }) } } } }] });
  for (const [tim, n, want] of [[[], 4, 'Usually under 2 minutes.'], [[T('series', 25, 6)], 4, 'Usually under 2 minutes.'], [[T('series', 25, 6)], 16, 'Usually under 7 minutes.'], [[T('series', 8, 6)], 3, 'Usually under 30 seconds.']]) {
    const x = await rsc(tim, n); ok(ctx(x.answer.view).indexOf(want + ' You can close this window') === 0, 'booking ' + n + ' dates' + (tim.length ? ' at ' + tim[0].json.seconds + ' s each' : ', nothing learned (30 s a date)') + ' -> ' + want, ctx(x.answer.view));
  }
  ok(!/Multiple bookings may take longer/.test(JSON.stringify((await rsc([], 2)).answer.view)), 'the estimate replaces "Multiple bookings may take longer to process."');
  const read1 = async (tim, extra) => j1('Read Step 1', [], { 'Check Signature': [chk], 'Timings 1': tim, 'Read Request': [{ json: { payload: { type: 'view_submission', view: { private_metadata: JSON.stringify({ requester: 'U1', channel: 'D1' }),
    state: { values: Object.assign({ date: { date_pick: { selected_date: '2027-10-21' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('15:00') }, purpose: { purpose_pick: tv('VO Recording') } }, extra || {}) } } } } }] });
  let r1 = await read1([]);
  ok(r1.valid && ctx(r1.answer.view) === 'Usually under 10 seconds.' && /Finding free rooms/.test(JSON.stringify(r1.answer.view)), 'Finding free rooms… - "Usually under 10 seconds."', r1.answer && r1.answer.view);
  r1 = await read1([T('rooms', 3.2, 12)]);
  ok(ctx(r1.answer.view) === 'Usually under 10 seconds.', 'rooms 3.2 s -> under 10 seconds (never less than 10)');
  const rch = await j1('Read Change', [], { 'Check Signature': [chk], 'Timings 10': [T('change', 14, 7)], 'Read Cache 10': cacheRow,
    'Read Request': [{ json: { payload: { view: { id: 'V1', private_metadata: JSON.stringify({ b: { id: 'e1', d: '2027-10-21', s: '13:00', e: '15:00', r: 'Studio 7', t: 'VO / HL', st: 'VO Recording' } }),
      state: { values: { date: { date_pick: { selected_date: '2027-10-22' } }, start: { start_pick: tv('13:00') }, end: { end_pick: tv('15:00') }, room: { room_pick: tv('Studio 7') } } } } } } }] });
  ok(rch.valid && ctx(rch.answer.view).indexOf('Usually under 20 seconds. You can close this window') === 0 && /Changing…/.test(JSON.stringify(rch.answer.view)), 'Changing… - change 14 s -> "Usually under 20 seconds."', rch.answer);

  console.log('which row each loading view reads');
  const RQ = p => ({ 'Read Request': [{ json: { payload: p } }] });
  ok(expr(node(si, 'Timings 1').parameters.filters.conditions[0].keyValue, RQ({ view: { state: { values: { date: {} } } } })) === 'rooms', 'step 1, no Repeats -> rooms');
  ok(expr(node(si, 'Timings 1').parameters.filters.conditions[0].keyValue, RQ({ view: { state: { values: { rep_freq: {} } } } })) === 'rooms-series', 'step 1 with Repeats -> rooms-series');
  ok(expr(node(si, 'Timings 2').parameters.filters.conditions[0].keyValue, RQ({ view: { private_metadata: JSON.stringify({ series: { dates: ['a', 'b'] } }) } })) === 'check', 'step 2 of a series -> check');
  ok(expr(node(si, 'Timings 2').parameters.filters.conditions[0].keyValue, RQ({ view: { private_metadata: '{bad' } })) === 'book', 'step 2, unreadable metadata -> book (no crash)');
  ok(node(si, 'Timings 13').parameters.filters.conditions[0].keyValue === 'series' && node(si, 'Timings 10').parameters.filters.conditions[0].keyValue === 'change', 'series confirm -> series; change -> change');
  for (const n of ['Timings 1', 'Timings 2', 'Timings 13', 'Timings 10', 'Read Timing', 'Save Timing']) {
    const x = node(si, n);
    ok(x.type === 'n8n-nodes-base.dataTable' && x.typeVersion === 1 && x.parameters.dataTableId.value === 'xZAKroMpWBdt0lib' && x.onError === 'continueRegularOutput' && !x.disabled
       && (n === 'Save Timing' ? x.parameters.operation === 'upsert' : x.parameters.operation === 'get' && x.alwaysOutputData && x.parameters.returnAll), n + ': Jessie Timings, the shape Read Cache / Store Prepared use, never stops the run');
  }
  const sv = node(si, 'Save Timing').parameters.columns;
  ok(sv.schema.map(c => c.id + ':' + c.type).join() === 'scenario:string,seconds:number,dates:number' && Object.keys(sv.value).join() === 'scenario,seconds,dates', 'Save Timing writes scenario, seconds, dates (not "at" - updatedAt has it)');

  console.log('learning: the sample and the next estimate');
  const now = Date.now();
  const samp = async (route, extra, ago) => runIn(si, 'Timing Sample', [], Object.assign({ 'Check Signature': [{ json: { route } }], 'Read Request': [{ json: { receivedAt: now - (ago || 21000) } }] }, extra));
  let s = await samp(6, { 'Read Step 2': [{ json: { s: { kind: 'studio' } } }] });
  ok(s.length === 1 && s[0].json.scenario === 'book' && Math.abs(s[0].json.per - 21) < 1, 'route 6, one date -> book, ~21 s', s[0] && s[0].json);
  s = await samp(6, { 'Read Step 2': [{ json: { s: { series: { dates: ['a', 'b', 'c'] } } } }] }, 30000);
  ok(s[0].json.scenario === 'check' && Math.abs(s[0].json.per - 10) < 1 && s[0].json.n === 3, 'route 6, 3 dates in 30 s -> check, 10 s a date');
  s = await samp(13, { 'Read Series Confirm': [{ json: { meta: { n: 4 } } }] }, 100000);
  ok(s[0].json.scenario === 'series' && Math.abs(s[0].json.per - 25) < 1, 'route 13, 4 dates in 100 s -> series, 25 s a date');
  s = await samp(5, { 'Read Step 1': [{ json: { s: { kind: 'studio' } } }] }, 4000);
  ok(s[0].json.scenario === 'rooms', 'route 5 -> rooms');
  s = await samp(11, {}, 9000);
  ok(s[0].json.scenario === 'change', 'route 11 -> change');
  ok((await samp(8, {})).length === 0 && (await samp(6, {}, 4000000)).length === 0, 'a redraw (route 8) or a run over 30 minutes -> no sample');
  ok((await runIn(si, 'Timing Sample', [], { 'Check Signature': [{ json: { route: 6 } }], 'Read Request': [{ json: {} }] })).length === 0, 'no receivedAt -> no sample');
  const nextE = async (per, rows) => runIn(si, 'Next Estimate', [], { 'Timing Sample': [{ json: { scenario: 'book', per } }], 'Read Timing': rows });
  let n = await nextE(21, [{ json: {} }]);
  ok(n[0].json.seconds === 21 && n[0].json.dates === 1, 'the first run -> 21 s, 1 run');
  n = await nextE(18, [T('book', 21, 3)]);
  ok(n[0].json.seconds === 21 && n[0].json.dates === 4, 'runs 2-5 keep the slowest (21 s)');
  n = await nextE(18, [T('book', 21, 9)]);
  ok(n[0].json.seconds === 20.4 && n[0].json.dates === 10, 'after 5 runs a faster run nudges it down a little (21 -> 20.4)');
  n = await nextE(30, [T('book', 21, 9)]);
  ok(n[0].json.seconds === 26.7, 'a slower run moves it up more (21 -> 26.7)');
  let q = 20; for (let i = 0; i < 400; i++) { const x = 15 + 10 * ((i * 7919) % 100) / 100; const o = await nextE(x, [T('book', q, 9)]); q = o[0].json.seconds; }
  ok(q > 22.5 && q < 25.5, 'runs spread evenly over 15-25 s -> it settles near the 90th percentile (~24 s): ' + q);
  ok((await nextE(20, [{ json: { error: 'x' } }])).length === 0, 'the table could not be read -> nothing written');

  console.log('wiring');
  const C = si.connections, nx = k => ((C[k] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
  ok(C.Route.main[5][0].node === 'Timings 1' && nx('Timings 1') === 'Read Step 1' && nx('Read Cache 3') === 'Timings 2' && nx('Timings 2') === 'Read Step 2'
     && C.Route.main[13][0].node === 'Timings 13' && nx('Timings 13') === 'Read Series Confirm' && nx('Read Cache 10') === 'Timings 10' && nx('Timings 10') === 'Read Change', 'a read right before each loading view');
  ok(['Show Step 2', 'Show Result', 'Show Series Step', 'Show Series Result', 'Show Change Result'].every(k => nx(k).split(/[+|]/).map(x => x.trim()).indexOf('Timing Sample') !== -1)
     && nx('Timing Sample') === 'Read Timing' && nx('Read Timing') === 'Next Estimate' && nx('Next Estimate') === 'Save Timing', 'learning after every answer on screen');
  const lnc = node(si, 'Loc Needed?').parameters.conditions.conditions[0].leftValue;
  ok(expr(lnc, { 'Read Step 1': [{ json: { s: { kind: 'loc' } } }] }) === false && expr(lnc, { 'Read Step 1': [{ json: { s: { kind: 'loc', pre: { cd: ' ' } } } }] }) === false
     && expr(lnc, { 'Read Step 1': [{ json: { s: { kind: 'loc', pre: { cd: 'NET-MALAS' } } } }] }) === true, 'Localization Projects at step 2 only for a code already filled in');

  console.log('Book Session v115 -> Log Booking v2: new project codes');
  const blr = async (st, title) => (await runIn(bs, 'Build Log Row', [], { 'Verify': [{ json: { title, event_id: 'ev1' } }],
    'When Executed by Another Workflow': [{ json: { session_type: st, summary: title, start_iso: '2027-10-21T13:00:00+08:00', end_iso: '2027-10-21T15:00:00+08:00', rooms: 'Studio 1', department: 'Localization', description: 'Booked by: Howard Luistro | ref: U1' } }],
    'Check Conflicts': [{ json: { final_summary: title, final_start: '2027-10-21T13:00:00+08:00' } }], 'Client Cache': [], 'Get Client': [] }))[0].json;
  let L = await blr('Localization Dubbing', 'net-malas / JT');
  let P = JSON.parse(L.project || 'null');
  ok(P && P.Code === 'NET-MALAS' && P.Status === 'For Review' && P['Booked by'] === 'Howard Luistro' && P['Session Type'] === 'Localization Dubbing' && P['Booking Date'] === '2027-10-21', 'a Localization booking -> its code (the title\'s first part, in capitals)', P);
  L = await blr('QC', 'ABC-01 / JT');
  ok(JSON.parse(L.project).Code === 'ABC-01', 'QC -> its code too');
  L = await blr('VO Recording', 'SONG / Jem Lim / HL');
  ok(L.project === '' && L.log, 'any other booking -> no project row (nothing looked up)');
  ok(node(bs, 'Log Booking').parameters.workflowInputs.value.project === '={{ $json.project }}' && node(bs, 'Log Booking').parameters.options.waitForSubWorkflow === false, 'Book Session passes it on, still without waiting');
  ok(node(lb, 'When Executed by Another Workflow').parameters.workflowInputs.values.map(v => v.name).join() === 'log,client,project', 'Log Booking takes log, client, project');
  const pr = async (p) => runIn(lb, 'Project Row', [], { 'When Executed by Another Workflow': [{ json: { project: p } }] });
  ok((await pr('')).length === 0 && (await pr('{"Code":"  "}')).length === 0 && (await pr('nonsense')).length === 0, 'no code -> nothing looked up (an empty value would match every row - gotcha 7)');
  const prow = (await pr(JSON.stringify({ Code: 'net-malas', Status: 'For Review' })))[0].json;
  ok(prow.Code === 'NET-MALAS', 'the code in capitals');
  const fp = node(lb, 'Find Project');
  const f = expr(fp.parameters.filterByFormula, { 'Project Row': [{ json: prow }] });
  ok(f === "UPPER(TRIM({Project Code})) = 'NET-MALAS'" && expr(fp.parameters.filterByFormula, { 'Project Row': [{ json: { Code: "O'BRIEN" } }] }) === "UPPER(TRIM({Project Code})) = 'O\\'BRIEN'"
     && expr(fp.parameters.filterByFormula, { 'Project Row': [{ json: {} }] }) === 'FALSE()', 'Find Project: one exact code (quotes escaped), never an empty search', f);
  ok(fp.parameters.table.value === 'tbljkG6z7odPUtTIf' && fp.parameters.base.value === 'app8GQxEInqJi1NRP' && fp.alwaysOutputData && fp.onError === 'continueRegularOutput' && fp.credentials.airtableTokenApi, 'Localization Projects, the Airtable credential Book Session uses, never stops the run');
  const np = async (rows) => runIn(lb, 'New Project?', [], { 'Find Project': rows, 'Project Row': [{ json: prow }] });
  ok((await np([{ json: {} }])).length === 1, 'not in the table (an empty answer) -> a New Projects row');
  ok((await np([{ json: { id: 'rec1', 'Project Code': 'NET-MALAS' } }])).length === 0, 'in the table -> nothing written');
  ok((await np([{ json: { error: 'timeout' } }])).length === 0, 'the lookup errored -> nothing written (not evidence)');
  const lnp = node(lb, 'Log New Project'), lncl = node(lb, 'Log New Client');
  ok(lnp.parameters.sheetName.value === 'New Projects' && lnp.parameters.columns.matchingColumns.join() === 'Code' && lnp.parameters.operation === 'appendOrUpdate'
     && lnp.parameters.documentId.value === lncl.parameters.documentId.value && JSON.stringify(lnp.credentials) === JSON.stringify(lncl.credentials) && lnp.onError === 'continueRegularOutput',
     'Log New Project: the New Projects tab of the Jessie Log sheet, one row per code, like New Clients');
  const LC = lb.connections, lx = k => ((LC[k] || {}).main || []).map(o => (o || []).map(c => c.node).join('+')).join(' | ');
  ok(lx('When Executed by Another Workflow') === 'Log Row+Project Row' && lx('Log Row') === 'Log to Sheet' && lx('Client Row') === 'Log New Client' && lx('Project Row') === 'Find Project'
     && lx('Find Project') === 'New Project?' && lx('New Project?') === 'Log New Project', 'Log Booking wiring: the log branch as before, the project branch beside it');

  console.log('\n' + pass + ' ok, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})().catch(e => { console.error(e); process.exit(2); });
