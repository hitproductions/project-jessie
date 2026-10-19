#!/usr/bin/env node
// sim-round-8-book (Book Session v112 + Log Booking v1, round 8, 19 Oct): the faster booking run and the single-room types.
//   node scripts/sim-round-8-book.js [workflows/book-session-vN.json] [workflows/log-booking-vN.json]
const fs = require('fs'), path = require('path');
const W = p => JSON.parse(fs.readFileSync(p));
const B = W(process.argv[2] || path.join(__dirname, '..', 'workflows', 'book-session-v112.json'));
const L = W(process.argv[3] || path.join(__dirname, '..', 'workflows', 'log-booking-v1.json'));
const node = (wf, n) => wf.nodes.find(x => x.name === n);
const code = (wf, n) => node(wf, n).parameters.jsCode;
let pass = 0, fail = 0;
const ok = (c, msg, d) => { if (c) { pass++; console.log('  ok    ' + msg); } else { fail++; console.log('  FAIL  ' + msg + (d === undefined ? '' : '  :: ' + JSON.stringify(d).slice(0, 500))); } };
const wrap = it => ({ first: () => it[0], all: () => it, isExecuted: true });
const to = (wf, n, i = 0) => (((wf.connections[n] || {}).main || [])[i] || []).map(c => c.node);

// ── 3. Client Cache ──────────────────────────────────────────────────────────────────────────────────────────────────────
console.log('Client Cache - the prepare run\'s lookups reused by the booking run');
const cache = (REQ) => new Function('$', code(B, 'Client Cache'))(n => wrap([{ json: REQ }]))[0].json;
const now = new Date().toISOString(), old = new Date(Date.now() - 10 * 60 * 1000).toISOString();
const gc = [{ id: 'rec1', fields: { Name: 'Jem Lim' } }];
const cc = (o) => JSON.stringify(Object.assign({ v: 1, at: now, client: 'Jem Lim', gc, al: [], an: null }, o));
ok(cache({ client: 'Jem Lim', client_cache: cc() }).use === true, 'same client, fresh -> use');
ok(cache({ client: 'Jem Lim', client_cache: cc() }).gc[0].id === 'rec1', '... with the rows');
ok(cache({ client: 'Jem Lim', mode: 'prepare', client_cache: cc() }).use === false, 'the prepare run itself never uses a cache');
ok(cache({ client: 'Jem Lim', client_cache: cc({ at: old }) }).use === false, 'older than 3 minutes -> the lookups run');
ok(cache({ client: 'Pael', client_cache: cc() }).use === false, 'a different client -> the lookups run');
ok(cache({ client: '', client_cache: cc({ client: 'None' }) }).use === true, 'no client on both ("None" on the card) -> use');
ok(cache({ client: 'Jem Lim' }).use === false, 'no cache (chat, Book Series, consent) -> the lookups run');
ok(cache({ client: 'Jem Lim', client_cache: '{bad' }).use === false, 'an unreadable cache -> the lookups run');
ok(to(B, 'All Bookers')[0] === 'Client Cache' && to(B, 'Client Cache')[0] === 'Cached?' && to(B, 'Cached?', 0)[0] === 'Get Events In Window'
   && to(B, 'Cached?', 1)[0] === 'Get Client', 'All Bookers -> Client Cache -> Cached? -> (cached) Get Events In Window / Get Client');
ok(node(B, 'When Executed by Another Workflow').parameters.workflowInputs.values.some(v => v.name === 'client_cache'), 'client_cache is a Book Session input');
const CCjs = code(B, 'Check Conflicts');
ok(!/\$\('Get Client'\)\.(all|first)\(\)(?![^(]*\}\)\(\)\))/.test(CCjs.replace(/return \$\('Get Client'\)\.(all|first)\(\); \}\)\(\)\)/g, '')),
   'Check Conflicts reads Get Client only through the cache switch');
// Check Conflicts' reads with the cache on: the cached rows, without Get Client having run
{
  const getRows = new Function('$', "return " + CCjs.match(/\(\(\(\) => \{ try \{ const c = \$\('Client Cache'\)\.first\(\)\.json; if \(c && c\.use && Array\.isArray\(c\.gc\)\) return c\.gc\.map\(j => \(\{ json: j \}\)\); \} catch \(e\) \{\} return \$\('Get Client'\)\.all\(\); \}\)\(\)\)/)[0]);
  const rows = getRows(n => n === 'Client Cache' ? wrap([{ json: { use: true, gc } }]) : { all: () => { throw new Error('not executed'); } });
  ok(rows.length === 1 && rows[0].json.id === 'rec1', 'cache on: Check Conflicts gets the cached client rows, Get Client never asked');
  const live = getRows(n => n === 'Client Cache' ? wrap([{ json: { use: false } }]) : wrap([{ json: { id: 'recLIVE' } }]));
  ok(live[0].json.id === 'recLIVE', 'cache off: Get Client\'s own rows');
}
// Prepared Out hands the lookups back
{
  const PO = code(B, 'Prepared Out');
  const out = new Function('$', PO)(n => n === 'Render Summary' ? wrap([{ json: { status: 'PREPARED', prep_payload: JSON.stringify({ F: { Client: 'Jem Lim' } }) } }])
    : n === 'Get Client' ? wrap([{ json: gc[0] }]) : n === 'Client Aliases' ? wrap([]) : n === 'Store Prepared' ? wrap([{ json: {} }])
    : { all: () => { throw new Error('not executed'); }, first: () => { throw new Error('not executed'); } })[0].json;
  let c = {}; try { c = JSON.parse(out.client_cache); } catch (e) {}
  ok(c.v === 1 && c.client === 'Jem Lim' && c.gc[0].id === 'rec1' && c.an === null && out.prep_stored === true, 'Prepared Out: client_cache with the prepare run\'s rows', c);
}

// ── 1. the room's answer ─────────────────────────────────────────────────────────────────────────────────────────────────
console.log('Room Answered? - on as soon as every room has answered');
const ansExpr = node(B, 'Room Answered?').parameters.conditions.conditions[0].leftValue.replace(/^=\{\{\s*/, '').replace(/\s*\}\}$/, '');
const answered = ev => new Function('$json', 'return ' + ansExpr)(ev);
const S7 = { email: 's7@resource.calendar.google.com', resource: true };
ok(answered({ id: 'e', attendees: [{ ...S7, responseStatus: 'needsAction' }] }) === false, 'room still needsAction -> wait and read again');
ok(answered({ id: 'e', attendees: [{ ...S7, responseStatus: 'accepted' }] }) === true, 'accepted -> on');
ok(answered({ id: 'e', attendees: [{ ...S7, responseStatus: 'declined' }] }) === true, 'declined -> on (Verify deletes it)');
ok(answered({ id: 'e', attendees: [{ ...S7, responseStatus: 'accepted' }, { email: 'm4@r', resource: true, responseStatus: 'needsAction' }] }) === false, 'one room of two still to answer -> wait');
ok(answered({ id: 'e', attendees: [{ email: 'p@hitproductions.net', responseStatus: 'needsAction' }] }) === true, 'only people on it (no room) -> on');
ok(answered({ error: { message: 'boom' } }) === true, 'the read failed -> on (Verify keeps the create response)');
ok(node(B, 'Room Answered 2?').parameters.conditions.conditions[0].leftValue === node(B, 'Room Answered?').parameters.conditions.conditions[0].leftValue, 'the second check is the same test');

// ── 4. single-room booking types ─────────────────────────────────────────────────────────────────────────────────────────
console.log('Check Conflicts - single-room booking types');
{
  const i = CCjs.indexOf('// v112 (round 8): single-room'), j = CCjs.indexOf('const keys = Object.keys(ROOMS);', i);
  const rule = new Function('REQ', 'wantedNames', CCjs.slice(i, j) + '\nreturn null;');
  const r = (st, rooms) => { const x = rule({ session_type: st }, rooms); return x ? x[0].json : null; };
  let x = r('Atmos Mixing', ['Studio 6']);
  ok(x && x.reason === 'ROOM_UNSUITABLE' && x.human === 'Atmos Mixing can only be booked in Studio C. Nothing was booked.', 'Atmos Mixing in Studio 6 -> refused', x);
  ok(r('Localization Atmos Mixing', ['Studio 6']) !== null, 'the old name (Localization Atmos Mixing) too');
  ok(r('Atmos Mixing', ['Studio C']) === null, 'Atmos Mixing in Studio C -> on');
  x = r('Van Recording', ['Studio 7']);
  ok(x && x.human === 'Van Recording can only be booked in Studio M. Nothing was booked.', 'Van Recording in Studio 7 -> refused', x);
  ok(r('Van Recording', ['Studio M']) === null, 'Van Recording in Studio M -> on');
  x = r('VO Recording', ['Studio M']);
  ok(x && x.human === 'Studio M is only for Van Recording. Nothing was booked.', 'VO Recording in Studio M -> refused (Studio M is only for Van Recording)', x);
  ok(r('Meeting', ['Studio M']) !== null, 'a meeting in Studio M -> refused');
  ok(r('VO Recording', ['Studio 6', 'Studio A']) === null, 'anything else -> untouched');
}

// ── 2. the log sheets after the reply ────────────────────────────────────────────────────────────────────────────────────
console.log('Build Log Row -> Log Booking (no wait) -> Return Booked');
{
  const REQ = { summary: 'ATLAS / Acme Records / TL', client: 'Acme Records', rooms: 'Studio 6', start_iso: '2027-10-20T13:00:00+08:00', end_iso: '2027-10-20T15:00:00+08:00',
    description: 'Engineer: Tara Lim | Booked by: Howard Luistro | ref: U1', department: 'Audio Post', bookingType: 'Advertising', session_type: 'VO Recording' };
  const run = (gcRows, cacheOn) => new Function('$', code(B, 'Build Log Row'))(n => n === 'Verify' ? wrap([{ json: { status: 'CREATED', event_id: 'ev1', title: REQ.summary } }])
    : n === 'When Executed by Another Workflow' ? wrap([{ json: REQ }]) : n === 'Check Conflicts' ? wrap([{ json: { final_client: 'Acme Records', final_summary: REQ.summary, final_start: REQ.start_iso } }])
    : n === 'Client Cache' ? wrap([{ json: cacheOn ? { use: true, gc: gcRows } : { use: false } }])
    : n === 'Get Client' ? (cacheOn ? { all: () => { throw new Error('not executed'); } } : wrap(gcRows.map(j => ({ json: j })))) : wrap([]))[0].json;
  let o = run([{}], false), lg = JSON.parse(o.log), cl = o.client ? JSON.parse(o.client) : null;
  ok(lg.Action === 'BOOKED' && lg['Event ID'] === 'ev1' && lg.Title === REQ.summary && lg['Room(s)'] === 'Studio 6' && lg.Booker === 'Howard Luistro' && lg.Date === '2027-10-20'
     && lg.Department === 'Audio Post' && lg.Note === 'Advertising', 'the Log row as before', lg);
  ok(cl && cl.Client === 'Acme Records' && cl.Status === 'For Review' && cl['Event ID'] === 'ev1' && cl.Project === 'ATLAS' && cl['Booking Date'] === '2027-10-20', 'an unknown client -> the New Clients row', cl);
  o = run([{ id: 'rec9', fields: { Name: 'Acme Records' } }], false);
  ok(o.client === '', 'a client in Airtable -> no New Clients row');
  o = run([{ id: 'rec9', fields: { Name: 'Acme Records' } }], true);
  ok(o.client === '', 'the same with the cached lookups (Get Client never ran)');
  o = run([{}], true);
  ok(o.client !== '', 'an unknown client with the cached lookups -> the row');
  o = run([{ error: 'timeout' }], false);
  ok(o.client === '', 'a lookup that errored is not evidence -> no row');
  const lb = node(B, 'Log Booking');
  ok(lb.type === 'n8n-nodes-base.executeWorkflow' && lb.parameters.options.waitForSubWorkflow === false && lb.onError === 'continueRegularOutput',
     'Log Booking: Execute Workflow, not waited for, never fails the booking');
  ok(lb.parameters.workflowInputs.value.log === '={{ $json.log }}' && lb.parameters.workflowInputs.value.client === '={{ $json.client }}', 'Log Booking gets the two rows');
  ok(to(B, 'Logged?', 0)[0] === 'Build Log Row' && to(B, 'Build Log Row')[0] === 'Log Booking' && to(B, 'Log Booking')[0] === 'Return Booked', 'Logged? -> Build Log Row -> Log Booking -> Return Booked');
  ok(['Log to Sheet', 'New Client?', 'New Client Row', 'Log New Client'].every(n => !node(B, n)), 'the sheet nodes are gone from Book Session');
  ok(lb.parameters.workflowId.value !== '' , 'Log Booking id set: ' + lb.parameters.workflowId.value);
}

// ── Log Booking v1 ───────────────────────────────────────────────────────────────────────────────────────────────────────
console.log('Jessie — Log Booking');
{
  const trig = n => (inp) => n === 'When Executed by Another Workflow' ? wrap([{ json: inp }]) : wrap([]);
  const row = (n, inp) => new Function('$', code(L, n))(m => trig(m)(inp));
  ok(row('Log Row', { log: JSON.stringify({ Action: 'BOOKED' }) })[0].json.Action === 'BOOKED', 'Log Row: the row');
  ok(row('Log Row', { log: '' }).length === 0, 'no row -> nothing written');
  ok(row('Client Row', { client: JSON.stringify({ Client: 'Acme Records' }) })[0].json.Client === 'Acme Records', 'Client Row: the new client');
  ok(row('Client Row', { client: '' }).length === 0, 'a known client -> nothing written');
  ok(to(L, 'When Executed by Another Workflow')[0] === 'Log Row' && to(L, 'Log Row')[0] === 'Log to Sheet' && to(L, 'Log to Sheet')[0] === 'Client Row'
     && to(L, 'Client Row')[0] === 'Log New Client', 'trigger -> Log Row -> Log to Sheet -> Client Row -> Log New Client');
  const s = node(L, 'Log to Sheet'), c = node(L, 'Log New Client');
  ok(s.parameters.operation === 'append' && s.parameters.documentId.value === '1vIQ_cf2jJJ_WKpwFfnZQjQeKg2cxQz4tXGS6RZTEMwo' && s.onError === 'continueRegularOutput'
     && c.parameters.operation === 'appendOrUpdate' && c.parameters.columns.matchingColumns[0] === 'Client', 'the same two sheet writes as Book Session v111');
  ok(node(L, 'When Executed by Another Workflow').parameters.workflowInputs.values.map(v => v.name).join() === 'log,client', 'inputs: log, client');
}

console.log(`\n${pass} passed, ${fail} failed`); process.exit(fail ? 1 : 0);
